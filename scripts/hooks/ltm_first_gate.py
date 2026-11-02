#!/usr/bin/env python3
"""LTM-first gate (ledger claim-gate-recall-before-block:develop, owner 2026-10-26: "ask LTM first overcomes most problems").

CLAUDE.md rule 1 says: call memory_recall and kb_recall before acting. As advice it loses as a session grows (context rot), so this
PreToolUse hook enforces it. In a turn started by the person, the first tool that is not itself a recall (or a loader such as
ToolSearch) is refused until a recall tool has been called in the same turn; the refusal names the tools to call. The agent then
recalls, and the same tool is allowed on its retry, so a violation costs one short retry, not a wasted turn of work.

Deliberate safeguards, so the gate cannot lock a session:
  * turns started by the system (a notification, a scheduled message) are not gated;
  * after MAX_IGNORED refused attempts in the same turn the gate stands aside (the Agent MCP may be disconnected), and says so;
  * the read-only loaders and the ask/task bookkeeping tools are exempt.
It never edits a call and never blocks a turn that has already recalled.
"""
import json
import re
import sys

RECALL = re.compile(r"(memory_recall|kb_recall|code_recall|training_recall|pd_find|pd_search|library_search)$")
EXEMPT = re.compile(
    r"(memory_recall|kb_recall|code_recall|training_recall|pd_find|pd_search|library_search|rules_load|register_session|"
    r"message_inbox|tasks_decisions_pending|ToolSearch|ReadNotifications|Skill|AskUserQuestion|TaskCreate|TaskUpdate|TaskList|TaskGet)$"
)
AUTOMATED = re.compile(r"^\s*<system-reminder>|\[SYSTEM NOTIFICATION", re.I)
MAX_IGNORED = 3

NEXT = ("LTM first (CLAUDE.md rule 1, owner 2026-10-26): before acting on this request, call memory_recall and kb_recall "
        "(and code_recall before exploring the repo) on its subject through the Claudia Control Plane MCP; load them with ToolSearch "
        "if they are deferred. Apply what they return, then retry this tool. If the MCP is not connected, say so in your reply "
        "(this gate stands aside after {n} attempts).")


def _content(entry):
    msg = entry.get("message") or {}
    c = msg.get("content")
    if isinstance(c, str):
        return [{"type": "text", "text": c}]
    return c if isinstance(c, list) else []


def current_turn(lines):
    """(first user text of the turn, entries after it). The turn starts at the last user entry that is not only tool results."""
    start, text = 0, ""
    for i, e in enumerate(lines):
        if e.get("type") != "user":
            continue
        blocks = _content(e)
        if blocks and all(isinstance(b, dict) and b.get("type") == "tool_result" for b in blocks):
            continue
        start = i + 1
        text = " ".join(b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text")
    return text, lines[start:]


def decide(event, lines):
    name = str(event.get("tool_name", ""))
    if EXEMPT.search(name):
        return None
    text, turn = current_turn(lines)
    if AUTOMATED.search(text or ""):
        return None
    ignored = 0
    for e in turn:
        if e.get("type") != "assistant":
            continue
        for b in _content(e):
            if isinstance(b, dict) and b.get("type") == "tool_use":
                n = str(b.get("name", ""))
                if RECALL.search(n):
                    return None
                if not EXEMPT.search(n):
                    ignored += 1
    if ignored >= MAX_IGNORED:
        return None
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": NEXT.format(n=MAX_IGNORED)}}


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
    out = decide(event, load(event.get("transcript_path") or ""))
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
