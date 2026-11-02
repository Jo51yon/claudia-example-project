#!/usr/bin/env python3
"""Brief-chat gate (ledger brief-chat-core-rule:develop, owner 2026-10-26).

Rules core A8 and the task-manager skill (section "Brief chat") already say chat carries only outcomes, decisions needed and
exceptions, with the detail on the ledger. A rule written as advice loses as a session grows (context rot), so this Stop hook
makes it mechanical, in the same way as ask_gate.py:
  * the turn's final text is over the word or line budget -> pushed back: roll the detail into the ledger and memory, and
    reply with Decided / Need from you / Exceptions only;
  * the turn did real work (several tool calls) but wrote nothing to the ledger or memory -> pushed back: the detail is the
    audit trail the owner wants ingested and distilled, so record it first (tasks_heartbeat, tasks_record_decision,
    memory_write, kb_author), then give the short reply.
  * Claudia heartbeat cadence (claudia-session-hooks-parity:develop, owner 2026-11-02): while the session holds a claimed
    ledger task (tasks_claim with no later tasks_transition to done or tasks_release), a turn of real work must write a
    tasks_heartbeat, and no more than HEARTBEAT_MINUTES may pass between heartbeats. The progress events are what the
    distiller turns into memory, and a claim with no heartbeat is reclaimed (claudia_reclaim_stale_claims).
A push-back never changes the reply and never blocks the work; stop_hook_active is honoured, so a second stop in the same
turn always goes through (no loop).
"""
import json
import re
import sys
from datetime import datetime

MAX_WORDS = 170          # outside code fences
MAX_LINES = 16           # non-empty lines outside code fences
WORK_TOOL_CALLS = 6      # a turn with at least this many tool calls must have written its detail down
LEDGER_WRITE = re.compile(r"(tasks_heartbeat|tasks_record_decision|tasks_upsert|tasks_transition|tasks_block|memory_write|kb_author)$")
FENCE = re.compile(r"```.*?```", re.S)
HEARTBEAT_MINUTES = 15
CLAIM = re.compile(r"tasks_claim$")
RELEASE = re.compile(r"(tasks_release|tasks_transition)$")
HEARTBEAT = re.compile(r"tasks_heartbeat$")

NEXT = ("Roll the detail up: write it (what was done, evidence, decisions, reasoning) to the ledger task with tasks_heartbeat "
        "or tasks_record_decision and to memory with memory_write or kb_author, then reply in at most ~{w} words and ~{l} lines "
        "as: Decided / Need from you / Exceptions. Say nothing for steps that are routine or unchanged (CI waiting, tool "
        "output, narration). Questions for the owner stay, with their context and options (at most 5).")


def body_stats(text: str):
    body = FENCE.sub("", text or "")
    lines = [l for l in body.splitlines() if l.strip()]
    words = len(body.split())
    return words, len(lines)


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
    tool_calls, wrote, last_text = 0, False, ""
    for e in turn:
        if e.get("type") != "assistant":
            continue
        for b in _content(e):
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                tool_calls += 1
                if LEDGER_WRITE.search(str(b.get("name", ""))):
                    wrote = True
            if b.get("type") == "text" and b.get("text", "").strip():
                last_text = b["text"]
    return tool_calls, wrote, last_text


def _ts(entry):
    try:
        return datetime.fromisoformat(str(entry.get("timestamp", "")).replace("Z", "+00:00"))
    except ValueError:
        return None


def claim_state(lines):
    """(open claimed task ids, time of the last claim or heartbeat on them, time of the last entry)."""
    open_ids, last_beat, last_seen = set(), None, None
    for e in lines:
        t = _ts(e)
        if t:
            last_seen = t
        if e.get("type") != "assistant":
            continue
        for b in _content(e):
            if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                continue
            name, inp = str(b.get("name", "")), b.get("input") or {}
            tid = str(inp.get("task_id", ""))
            if CLAIM.search(name) and tid:
                open_ids.add(tid)
                last_beat = t or last_beat
            elif HEARTBEAT.search(name):
                last_beat = t or last_beat
            elif RELEASE.search(name) and tid and (name.endswith("tasks_release") or inp.get("status") == "done"):
                open_ids.discard(tid)
    return open_ids, last_beat, last_seen


def turn_heartbeat(turn):
    for e in turn:
        if e.get("type") != "assistant":
            continue
        for b in _content(e):
            if isinstance(b, dict) and b.get("type") == "tool_use" and HEARTBEAT.search(str(b.get("name", ""))):
                return True
    return False


def heartbeat_problem(lines, turn, tool_calls):
    open_ids, last_beat, last_seen = claim_state(lines)
    if not open_ids:
        return None
    ids = ", ".join(sorted(i[:8] for i in open_ids))
    if tool_calls >= WORK_TOOL_CALLS and not turn_heartbeat(turn):
        return (f"you hold claimed task(s) {ids} and this turn did real work ({tool_calls} tool calls) with no tasks_heartbeat; "
                "write what landed and its evidence with tasks_heartbeat (pass actor)")
    if last_beat and last_seen and (last_seen - last_beat).total_seconds() > HEARTBEAT_MINUTES * 60:
        mins = int((last_seen - last_beat).total_seconds() // 60)
        return (f"claimed task(s) {ids} last had a heartbeat {mins} minutes ago (rule: at least every {HEARTBEAT_MINUTES}); "
                "call tasks_heartbeat with what landed")
    return None


def decide_stop(event, lines):
    if event.get("stop_hook_active"):
        return None
    turn = current_turn(lines)
    tool_calls, wrote, text = turn_facts(turn)
    if not text.strip():
        return None
    words, nlines = body_stats(text)
    problems = []
    if words > MAX_WORDS or nlines > MAX_LINES:
        problems.append(f"your reply is {words} words and {nlines} lines (budget {MAX_WORDS} words, {MAX_LINES} lines)")
    if tool_calls >= WORK_TOOL_CALLS and not wrote:
        problems.append(f"this turn made {tool_calls} tool calls but wrote nothing to the ledger or memory, so the detail is not on the audit trail")
    beat = heartbeat_problem(lines, turn, tool_calls)
    if beat:
        problems.append(beat)
    if not problems:
        return None
    return {"decision": "block",
            "reason": "Pushed back (brief-gate): " + "; ".join(problems) + ". " + NEXT.format(w=MAX_WORDS, l=MAX_LINES)}


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
    out = decide_stop(event, load(event.get("transcript_path") or ""))
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
