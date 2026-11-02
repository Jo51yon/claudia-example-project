import os, sys, unittest
sys.path.insert(0, os.path.dirname(__file__))
import brief_gate as g

def a_text(t): return {"type": "assistant", "message": {"content": [{"type": "text", "text": t}]}}
def a_tool(n): return {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": n, "input": {}}]}}
def u(t): return {"type": "user", "message": {"content": t}}
def res(): return {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}

SHORT = "Decided: arc approved.\nNeed from you: Oracle listing.\nExceptions: none."
LONG = " ".join(["word"] * (g.MAX_WORDS + 20))


class BriefGate(unittest.TestCase):
    def work(self, n, name="Bash"):
        out = [u("go")]
        for _ in range(n):
            out += [a_tool(name), res()]
        return out

    def test_short_reply_passes(self):
        self.assertIsNone(g.decide_stop({}, [u("go"), a_text(SHORT)]))

    def test_long_reply_is_pushed_back_with_the_numbers(self):
        out = g.decide_stop({}, [u("go"), a_text(LONG)])
        self.assertEqual(out["decision"], "block")
        self.assertIn("words", out["reason"])
        self.assertIn("ledger task", out["reason"])

    def test_many_lines_is_pushed_back(self):
        out = g.decide_stop({}, [u("go"), a_text("\n".join(["- item"] * (g.MAX_LINES + 3)))])
        self.assertEqual(out["decision"], "block")

    def test_code_fences_do_not_count(self):
        text = SHORT + "\n```\n" + LONG + "\n```"
        self.assertIsNone(g.decide_stop({}, [u("go"), a_text(text)]))

    def test_work_without_a_ledger_write_is_pushed_back(self):
        out = g.decide_stop({}, self.work(g.WORK_TOOL_CALLS) + [a_text(SHORT)])
        self.assertIn("audit trail", out["reason"])

    def test_work_with_a_ledger_write_passes(self):
        lines = self.work(g.WORK_TOOL_CALLS - 1) + [a_tool("mcp__Claudia_Control_Plane__tasks_heartbeat"), res(), a_text(SHORT)]
        self.assertIsNone(g.decide_stop({}, lines))

    def test_little_work_needs_no_write(self):
        self.assertIsNone(g.decide_stop({}, self.work(2) + [a_text(SHORT)]))

    def test_a_write_in_an_earlier_turn_does_not_count(self):
        lines = [u("a"), a_tool("mcp__Claudia_Control_Plane__memory_write"), res()] + self.work(g.WORK_TOOL_CALLS) + [a_text(SHORT)]
        out = g.decide_stop({}, lines)
        self.assertIsNotNone(out)

    def test_stop_hook_active_never_loops(self):
        self.assertIsNone(g.decide_stop({"stop_hook_active": True}, [u("go"), a_text(LONG)]))

    def test_empty_final_text_passes(self):
        self.assertIsNone(g.decide_stop({}, self.work(g.WORK_TOOL_CALLS)))


def at(entry, ts):
    entry = dict(entry)
    entry["timestamp"] = ts
    return entry


def a_call(n, **inp):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": n, "input": inp}]}}


CLAIM = "mcp__Claudia_Control_Plane__tasks_claim"
BEAT = "mcp__Claudia_Control_Plane__tasks_heartbeat"
TID = "e304d058-be6a-4517-b358-026063b9e9dd"


class HeartbeatCadence(unittest.TestCase):
    def claimed(self, t0="2026-11-02T12:00:00Z"):
        return [u("start"), at(a_call(CLAIM, task_id=TID), t0), res()]

    def test_work_on_a_claimed_task_without_heartbeat_is_pushed_back(self):
        lines = self.claimed() + [u("go")]
        for i in range(g.WORK_TOOL_CALLS):
            lines += [at(a_tool("Bash"), f"2026-11-02T12:0{i}:30Z"), res()]
        lines += [a_call("mcp__Claudia_Control_Plane__memory_write"), res(), a_text(SHORT)]
        out = g.decide_stop({}, lines)
        self.assertIsNotNone(out)
        self.assertIn("no tasks_heartbeat", out["reason"])
        self.assertIn(TID[:8], out["reason"])

    def test_work_with_a_heartbeat_in_the_turn_passes(self):
        lines = self.claimed() + [u("go")]
        for i in range(g.WORK_TOOL_CALLS):
            lines += [at(a_tool("Bash"), f"2026-11-02T12:0{i}:30Z"), res()]
        lines += [at(a_call(BEAT, task_id=TID), "2026-11-02T12:09:00Z"), res(), a_text(SHORT)]
        self.assertIsNone(g.decide_stop({}, lines))

    def test_more_than_fifteen_minutes_since_the_last_heartbeat_is_pushed_back(self):
        lines = self.claimed() + [u("status?"), at(a_text(SHORT), "2026-11-02T12:40:00Z")]
        out = g.decide_stop({}, lines)
        self.assertIsNotNone(out)
        self.assertIn("40 minutes ago", out["reason"])

    def test_a_task_closed_or_released_is_no_longer_held(self):
        for close in (a_call("mcp__Claudia_Control_Plane__tasks_transition", task_id=TID, status="done"),
                      a_call("mcp__Claudia_Control_Plane__tasks_release", task_id=TID)):
            lines = self.claimed() + [close, res(), u("status?"), at(a_text(SHORT), "2026-11-02T13:40:00Z")]
            self.assertIsNone(g.decide_stop({}, lines))

    def test_no_claim_means_no_cadence_check(self):
        self.assertIsNone(g.decide_stop({}, [u("go"), at(a_text(SHORT), "2026-11-02T13:40:00Z")]))


if __name__ == "__main__":
    unittest.main()
