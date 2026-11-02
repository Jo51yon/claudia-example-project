import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(__file__))
import ask_gate as g

def a_text(t): return {"type": "assistant", "message": {"content": [{"type": "text", "text": t}]}}
def a_tool(n): return {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": n, "input": {}}]}}
def u(t): return {"type": "user", "message": {"content": t}}
def res(): return {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}
Q = "Shall I raise the Gemini cap?"

class AskGate(unittest.TestCase):
    def test_question_detection(self):
        self.assertTrue(g.asks_question("Done.\n\n" + Q))
        self.assertFalse(g.asks_question("Done. Merged #12."))
        self.assertFalse(g.asks_question("```\nwhy?\n```\n> was it?\nAll merged."))

    def test_no_recall_no_receipt_pushed_back(self):
        out = g.decide_stop({}, [u("go"), a_text(Q)])
        self.assertEqual(out["decision"], "block")
        self.assertIn("recall and receipt", out["reason"])

    def test_recall_in_an_earlier_turn_does_not_count(self):
        out = g.decide_stop({}, [u("a"), a_tool("mcp__Claudia_Control_Plane__kb_recall"), res(), u("b"), a_text("Searched: x -> y. " + Q)])
        self.assertIn("recall", out["reason"])

    def test_recall_and_receipt_pass(self):
        lines = [u("go"), a_tool("mcp__Claudia_Control_Plane__kb_recall"), res(), a_text("Searched: kb_recall(\"gemini cap\") -> mm_1. Not found, so asking: " + Q)]
        self.assertIsNone(g.decide_stop({}, lines))

    def test_no_question_passes_and_stop_hook_active_never_loops(self):
        self.assertIsNone(g.decide_stop({}, [u("go"), a_text("All merged.")]))
        self.assertIsNone(g.decide_stop({"stop_hook_active": True}, [u("go"), a_text(Q)]))

    def test_ask_user_question_tool(self):
        ev = {"hook_event_name": "PreToolUse", "tool_input": {"questions": [{"question": Q}]}}
        self.assertEqual(g.decide_ask_tool(ev, [u("go")])["hookSpecificOutput"]["permissionDecision"], "deny")
        ok = {"hook_event_name": "PreToolUse", "tool_input": {"questions": [{"question": "Searched: kb_recall -> none. " + Q}]}}
        self.assertIsNone(g.decide_ask_tool(ok, [u("go"), a_tool("mcp__x__memory_recall"), res()]))

    def test_main_end_to_end(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            for e in [u("go"), a_text(Q)]: f.write(json.dumps(e) + "\n")
        import io, contextlib
        sys.stdin = io.StringIO(json.dumps({"hook_event_name": "Stop", "transcript_path": f.name}))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf): g.main()
        self.assertEqual(json.loads(buf.getvalue())["decision"], "block")
        os.unlink(f.name)

if __name__ == "__main__":
    unittest.main()
