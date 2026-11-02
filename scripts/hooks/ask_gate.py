#!/usr/bin/env python3
"""Ask-gate for chat questions (ledger ask-gate-control-plane-enforcement:develop, owner 2026-10-22).

The Agent MCP pushes back a tasks_block question that has no recall or receipt (askgate.ts). This hook does the same
for questions asked in chat:
  * Stop: the turn's final text asks the owner a question -> it must carry a "Searched: ..." receipt and the turn must
    have called a recall tool (memory_recall, kb_recall, ...). If not, the stop is pushed back ("decision": "block"),
    so the agent runs recall and answers from it, or re-asks with the receipt.
  * PreToolUse on AskUserQuestion: the same check, before the question is shown.
A push-back is never a block on the work: it sends the agent back to meet the rule. stop_hook_active is honoured, so a
second stop in the same turn always goes through (no loop).
"""
import json
import re
import sys

RECALL = re.compile(r"(memory_recall|kb_recall|code_recall|training_recall|pd_find|pd_search|library_search)$")
RECEIPT = re.compile(r"\bsearched\s*:\s*\S", re.I)
FENCE = re.compile(r"```.*?```", re.S)

NEXT = ("Run memory_recall and kb_recall (Claudia Control Plane MCP) on the question's subject. If the results answer it, "
        "apply the answer and do not ask. If a hit says something is blocked or impossible, check whether that has "
        "since been fixed before relying on it. Only if the question still stands, open it with the receipt: "
        "'Searched: kb_recall(\"...\") -> <ids>; memory_recall(\"...\") -> <ids>. Not found, so asking: <one question>.'")


def asks_question(text: str) -> bool:
    """True when the text puts a question to the reader: a sentence ending in '?' outside code and quotes."""
    body = FENCE.sub("", text or "")
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith(">") or line.startswith("|"):
            continue
        if re.search(r"\?\s*\**\s*$", line):
            return True
    return False


def _content(entry):
    msg = entry.get("message") or {}
    c = msg.get("content")
    if isinstance(c, str):
        return [{"type": "text", "text": c}]
    return c if isinstance(c, list) else []


def current_turn(lines):
    """The entries after the last message the person typed (a user entry that is not only tool results)."""
    start = 0
    for i, e in enumerate(lines):
        if e.get("type") != "user":
            continue
        blocks = _content(e)
        if blocks and all(isinstance(b, dict) and b.get("type") == "tool_result" for b in blocks):
            continue
        start = i + 1
    return lines[start:]


def turn_facts(turn):
    recalled, last_text = False, ""
    for e in turn:
        if e.get("type") != "assistant":
            continue
        for b in _content(e):
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use" and RECALL.search(str(b.get("name", ""))):
                recalled = True
            if b.get("type") == "text" and b.get("text", "").strip():
                last_text = b["text"]
    return recalled, last_text


def missing_for(text: str, recalled: bool):
    missing = []
    if not recalled:
        missing.append("recall")
    if not RECEIPT.search(text or ""):
        missing.append("receipt")
    return missing


def decide_stop(event, lines):
    if event.get("stop_hook_active"):
        return None
    recalled, text = turn_facts(current_turn(lines))
    if not asks_question(text):
        return None
    missing = missing_for(text, recalled)
    if not missing:
        return None
    return {"decision": "block",
            "reason": f"Pushed back (ask-gate): your reply asks the owner a question without {' and '.join(missing)}. {NEXT}"}


def decide_ask_tool(event, lines):
    qs = (event.get("tool_input") or {}).get("questions") or []
    text = " ".join(str(q.get("question", "")) for q in qs if isinstance(q, dict))
    recalled, last_text = turn_facts(current_turn(lines))
    missing = missing_for(text + " " + last_text, recalled)
    if not missing:
        return None
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
            "permissionDecisionReason": f"Pushed back (ask-gate): this question is missing {' and '.join(missing)}. {NEXT}"}}


def load(path):
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    except OSError:
        pass
    return out


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    lines = load(event.get("transcript_path") or "")
    if event.get("hook_event_name") == "PreToolUse":
        out = decide_ask_tool(event, lines)
    else:
        out = decide_stop(event, lines)
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
