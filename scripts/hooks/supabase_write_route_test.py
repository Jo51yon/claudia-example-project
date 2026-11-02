import io
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(__file__))
import supabase_write_route as hook  # noqa: E402

CLAUDIA = "ujjisckqspndzyasptni"
SAFESPACES = "yksfygrpcljqvdbbkuyg"


def run(tool, query=None, project=SAFESPACES):
    tool_input = {"query": query} if query else {"name": "x"}
    tool_input["project_id"] = project
    payload = {"tool_name": tool, "hook_event_name": "PreToolUse", "tool_input": tool_input}
    out = io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(json.dumps(payload))), mock.patch("sys.stdout", out):
        hook.main()
    return out.getvalue()


def reason(got):
    d = json.loads(got)["hookSpecificOutput"]
    return d["permissionDecision"], d["permissionDecisionReason"]


class SupabaseWriteRoute(unittest.TestCase):
    def test_apply_migration_on_safespaces_names_the_runner(self):
        decision, why = reason(run("mcp__Supabase__apply_migration"))
        self.assertEqual(decision, "deny")
        self.assertIn("run-live-sql", why)

    def test_apply_migration_on_claudia_names_ci(self):
        decision, why = reason(run("mcp__Supabase__apply_migration", project=CLAUDIA))
        self.assertEqual(decision, "deny")
        self.assertIn("migration-dry-run.yml", why)
        self.assertIn("apply-migrations.yml", why)
        self.assertNotIn("run-live-sql", why)

    def test_write_sql_is_denied_on_both(self):
        for project in (CLAUDIA, SAFESPACES):
            for q in ["update claudia_tasks set status='todo' where id='x'", "do $s$ begin perform 1; end $s$",
                      "create or replace function f() returns int as $$ select 1 $$ language sql",
                      "insert into t(a) values (1)", "select cron.schedule('j','* * * * *','select 1')"]:
                self.assertEqual(reason(run("mcp__Supabase__execute_sql", q, project))[0], "deny", (project, q))

    def test_reads_pass(self):
        for q in ["select status, updated_at from claudia_tasks where title ilike '%update the docs%'",
                  "select * from claudia_tasks for update skip locked",
                  "-- drop table x\nselect 1",
                  "with d as (select 1) select * from d",
                  "select extensions.http_get('https://example.com')"]:
            self.assertEqual(run("mcp__Supabase__execute_sql", q, CLAUDIA), "", q)

    def test_other_tools_pass(self):
        self.assertEqual(run("Bash", "drop table x"), "")


if __name__ == "__main__":
    unittest.main()
