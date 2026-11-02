import os, sys, unittest
sys.path.insert(0, os.path.dirname(__file__))
import ltm_first_gate as g

def a_tool(n): return {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": n, "input": {}}]}}
def a_text(t): return {"type": "assistant", "message": {"content": [{"type": "text", "text": t}]}}
def u(t): return {"type": "user", "message": {"content": t}}
def res(): return {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}
RECALL = "mcp__Claudia_Control_Plane__kb_recall"


class LtmFirst(unittest.TestCase):
    def test_first_work_tool_without_recall_is_refused(self):
        out = g.decide({"tool_name": "Bash"}, [u("read the CV")])
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("memory_recall", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_recall_tools_and_loaders_are_exempt(self):
        for t in (RECALL, "mcp__Claudia_Control_Plane__memory_recall", "ToolSearch", "ReadNotifications", "Skill"):
            self.assertIsNone(g.decide({"tool_name": t}, [u("go")]), t)

    def test_after_a_recall_in_the_turn_work_is_allowed(self):
        self.assertIsNone(g.decide({"tool_name": "Bash"}, [u("go"), a_tool(RECALL), res()]))

    def test_a_recall_in_an_earlier_turn_does_not_count(self):
        out = g.decide({"tool_name": "Edit"}, [u("a"), a_tool(RECALL), res(), u("b")])
        self.assertIsNotNone(out)

    def test_system_started_turns_are_not_gated(self):
        self.assertIsNone(g.decide({"tool_name": "Bash"}, [u("<system-reminder>\n[SYSTEM NOTIFICATION - NOT USER INPUT] ...")]))

    def test_gate_stands_aside_after_repeated_refusals(self):
        lines = [u("go")]
        for _ in range(g.MAX_IGNORED):
            lines += [a_tool("Bash"), res()]
        self.assertIsNone(g.decide({"tool_name": "Bash"}, lines))

    def test_exempt_calls_do_not_count_as_ignored(self):
        lines = [u("go")]
        for _ in range(g.MAX_IGNORED + 2):
            lines += [a_tool("ToolSearch"), res()]
        self.assertIsNotNone(g.decide({"tool_name": "Bash"}, lines))


if __name__ == "__main__":
    unittest.main()
