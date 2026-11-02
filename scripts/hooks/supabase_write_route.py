#!/usr/bin/env python3
"""Supabase write route for Claudia sessions (ported from oursafe-space scripts/hooks/supabase_write_route.py,
claudia-session-hooks-parity:develop, owner 2026-11-02).

PreToolUse on the Supabase connector's apply_migration and execute_sql. A WRITE through the connector raises a
confirmation that never reaches the owner: it times out and the agent reports "approve it" as a false human block
(SafeSpaces, 2026-10-24 and 2026-10-26). So the hook refuses a connector write before it is sent and names the
sanctioned route for the database it targets:
  * Claudia's control plane (project ujjisckqspndzyasptni): migrations go through CI only. Commit the migration (with a
    self-test under testing/sql/) on a branch, open a PR into preview: migration-dry-run.yml runs it against live in a
    rolled-back transaction, and apply-migrations.yml applies it once merged. Ledger and memory writes go through the
    Claudia Control Plane MCP, never by SQL (rules core A10).
  * SafeSpaces (project yksfygrpcljqvdbbkuyg) and any other project: the audited run-live-sql runner in the
    oursafe-space repo (agent-adhoc-playwright.yml with needs_service_role=true, kb tip mm_c617322279ac).
Read-only SELECTs through the connector are fine, including SELECTs that only call extensions.http.
"""
import json
import re
import sys

TOOL = re.compile(r"^mcp__.*supabase.*__(apply_migration|execute_sql)$", re.I)
WRITE = re.compile(
    r"\b(insert\s+into|update\s+\w|delete\s+from|merge\s+into|alter\s+|create\s+|drop\s+|truncate\b|grant\s+|revoke\s+|"
    r"comment\s+on|do\s+\$|call\s+\w|vacuum\b|refresh\s+materialized|cron\.schedule|cron\.unschedule|set_config\s*\()",
    re.I,
)
CLAUDIA_REF = "ujjisckqspndzyasptni"

CLAUDIA_ROUTE = (
    "SUPABASE WRITE ROUTE (Claudia control plane): do not write through the Supabase connector. Its confirmation never "
    "reaches the owner, so the call times out and becomes a false human block. Claudia migrations go through CI only: "
    "commit supabase/migrations/<timestamp>_<name>.sql with a self-test under testing/sql/<feature>/, open a PR into "
    "preview (migration-dry-run.yml runs it on live and rolls it back), and apply-migrations.yml applies it once merged. "
    "Ledger and memory writes go through the Claudia Control Plane MCP (tasks_*, memory_write), never by SQL. "
    "Read-only SELECTs through the connector are fine."
)
OTHER_ROUTE = (
    "SUPABASE WRITE ROUTE: do not write through the Supabase connector. Its confirmation never reaches the owner, so the "
    "call times out and becomes a false human block. For SafeSpaces (and any non-Claudia project) use the audited "
    "run-live-sql route in the oursafe-space repo, which needs no approval: commit the migration and an apply script "
    "under testing/rig/adhoc/, then dispatch .github/workflows/agent-adhoc-playwright.yml with script_path=<that script> "
    "and needs_service_role=true, and read RESULT: from the run log (kb tip mm_c617322279ac). Read-only SELECTs through "
    "the connector are fine."
)


def is_write(tool: str, args: dict) -> bool:
    if tool.endswith("apply_migration"):
        return True
    q = str(args.get("query") or "")
    q = re.sub(r"--[^\n]*", " ", q)                    # line comments
    q = re.sub(r"'(?:[^']|'')*'", "''", q)             # string literals
    q = re.sub(r"\bfor\s+(no\s+key\s+)?update\b", " ", q, flags=re.I)   # a locking read is still a read
    return bool(WRITE.search(q))


def route_for(args: dict) -> str:
    return CLAUDIA_ROUTE if str(args.get("project_id") or "") == CLAUDIA_REF else OTHER_ROUTE


def decide(payload: dict):
    tool = str(payload.get("tool_name") or "")
    args = payload.get("tool_input") or {}
    if not TOOL.match(tool) or not is_write(tool, args):
        return None
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": route_for(args)}}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    out = decide(payload)
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
