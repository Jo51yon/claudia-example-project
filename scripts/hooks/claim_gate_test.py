import os, sys, unittest
sys.path.insert(0, os.path.dirname(__file__))
import claim_gate as g

def a_text(t): return {"type": "assistant", "message": {"content": [{"type": "text", "text": t}]}}
def a_recall(q): return {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "mcp__Claudia_Control_Plane__kb_recall", "input": {"query": q}}]}}
def u(t): return {"type": "user", "message": {"content": t}}
def res(): return {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}


class ClaimGate(unittest.TestCase):
    def test_absence_claim_without_recall_is_pushed_back(self):
        out = g.decide_stop({}, [u("go"), a_text("Nothing extracts PDF text, so I logged a task.")])
        self.assertEqual(out["decision"], "block")
        self.assertIn("claim-gate", out["reason"])

    def test_limits_wording_is_caught(self):
        self.assertIsNotNone(g.decide_stop({}, [u("go"), a_text("These are limits on what I can do from this session.")]))

    def test_recall_on_the_subject_supports_the_claim(self):
        lines = [u("go"), a_recall("extract text from PDF"), res(), a_text("Nothing extracts PDF text on the runner.")]
        self.assertIsNone(g.decide_stop({}, lines))

    def test_recall_on_another_subject_does_not(self):
        lines = [u("go"), a_recall("LinkedIn headline wording"), res(), a_text("Nothing extracts PDF text on the runner.")]
        self.assertIsNotNone(g.decide_stop({}, lines))

    def test_receipt_supports_the_claim(self):
        text = "Searched: kb_recall(\"pdf\") -> mm_1. The deck is not available on Wasabi."
        self.assertIsNone(g.decide_stop({}, [u("go"), a_text(text)]))

    def test_plain_reply_and_quoted_lines_pass(self):
        self.assertIsNone(g.decide_stop({}, [u("go"), a_text("Merged #8819.\n> I cannot see it\n| not available |\n```\nno way\n```")]))

    def test_recall_in_an_earlier_turn_does_not_count(self):
        lines = [u("a"), a_recall("extract text from PDF"), res(), u("b"), a_text("Nothing extracts PDF text.")]
        self.assertIsNotNone(g.decide_stop({}, lines))

    def test_stop_hook_active_never_loops(self):
        self.assertIsNone(g.decide_stop({"stop_hook_active": True}, [u("go"), a_text("I cannot do that.")]))


if __name__ == "__main__":
    unittest.main()
