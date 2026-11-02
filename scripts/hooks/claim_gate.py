#!/usr/bin/env python3
"""Claim gate (ledger claim-gate-recall-before-block:develop, owner 2026-10-26).

ask_gate.py only catches replies that ask a question. The failures the owner kept hitting were statements: "nothing extracts PDF
text", "limits on what I can do", "the sandbox blocks X", "v5a is not available". A sentence that claims something is missing,
impossible or blocked must rest on a recall about that subject. This Stop hook pushes back a final reply that makes such a claim
unless, in the same turn, (a) a recall tool was called with a query that shares a significant word with the claim sentence, or
(b) the reply carries a "Searched: ..." receipt. A push-back never rewrites the reply; stop_hook_active is honoured, so a second
stop in the same turn always goes through.
"""
import json
import re
import sys

RECALL = re.compile(r"(memory_recall|kb_recall|code_recall|training_recall|pd_find|pd_search|library_search)$")
RECEIPT = re.compile(r"\bsearched\s*:\s*\S", re.I)
FENCE = re.compile(r"```.*?```", re.S)
CLAIM = re.compile(
    r"\bI (?:cannot|can't|can not|am unable to|was unable to|could not|couldn't)\b"
    r"|\b(?:there is no|there's no|no) (?:way|route|tool|means|connector|option)\b"
    r"|\b(?:nothing|no tool|no code) (?:extracts?|reads?|does|exists?|can|handles?)\b"
    r"|\b(?:does not|doesn't|do not|don't) exist\b"
    r"|\bnot (?:available|possible|supported)\b"
    r"|\b(?:sandbox|session|proxy) (?:blocks?|refuses?|denies)\b"
    r"|\blimits? on what I can\b",
    re.I,
)
STOP = {"there", "their", "which", "these", "those", "would", "could", "should", "about", "other", "being", "where", "while",
        "cannot", "nothing", "exist", "exists", "available", "possible", "supported", "route", "means", "option"}

NEXT = ("Pushed back (claim-gate): your reply says something is missing, impossible or blocked ({claims}) without a recall on that "
        "subject. Call memory_recall and kb_recall (and look in the repo) about it first. If they show a route or an existing "
        "answer, use it and drop the claim. Only if the claim still stands, keep it with the receipt: 'Searched: kb_recall(\"...\") "
        "-> <ids>; memory_recall(\"...\") -> <ids>. Not found, so: <the claim, the workaround, how it is prevented again>'.")


def _content(entry):
    msg = entry.get("message") or {}
    c = msg.get("content")
    if isinstance(c, str):
        return [{"type": "text", "text": c}]
    return c if isinstance(c, list) else []


def current_turn(lines):
    start = 0
    for i, e in enumerate(lines):
        if e.get("type") != "user":
            continue
        blocks = _content(e)
        if blocks and all(isinstance(b, dict) and b.get("type") == "tool_result" for b in blocks):
            continue
        start = i + 1
    return lines[start:]


def words(s: str):
    """Significant words, reduced to their first five letters so 'extracts' matches 'extract'."""
    return {w[:5] for w in re.findall(r"[a-z0-9]{5,}", (s or "").lower()) if w not in STOP}


def turn_facts(turn):
    queries, last_text = [], ""
    for e in turn:
        if e.get("type") != "assistant":
            continue
        for b in _content(e):
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use" and RECALL.search(str(b.get("name", ""))):
                queries.append(json.dumps(b.get("input", {}), default=str))
            if b.get("type") == "text" and b.get("text", "").strip():
                last_text = b["text"]
    return queries, last_text


def claim_sentences(text: str):
    body = FENCE.sub("", text or "")
    out = []
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith(">") or s.startswith("|"):
            continue
        for sent in re.split(r"(?<=[.!;:])\s+", s):
            m = CLAIM.search(sent)
            if m:
                out.append((m.group(0), sent))
    return out


def decide_stop(event, lines):
    if event.get("stop_hook_active"):
        return None
    queries, text = turn_facts(current_turn(lines))
    claims = claim_sentences(text)
    if not claims or RECEIPT.search(text):
        return None
    qwords = set()
    for q in queries:
        qwords |= words(q)
    unsupported = [c for c, sent in claims if not (words(sent) & qwords)]
    if not unsupported:
        return None
    return {"decision": "block", "reason": NEXT.format(claims="; ".join(sorted(set(u.lower() for u in unsupported))[:3]))}


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
