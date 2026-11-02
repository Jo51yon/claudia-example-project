import io
import json
import unittest
from unittest import mock

import egress_signpost as hook


def run(payload):
    out = io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(json.dumps(payload))), mock.patch("sys.stdout", out):
        hook.main()
    return out.getvalue()


class EgressSignpost(unittest.TestCase):
    def test_proxy_403_adds_signpost(self):
        got = run({"tool_name": "Bash", "hook_event_name": "PostToolUse",
                   "tool_response": {"stdout": "", "stderr": "curl: (56) CONNECT tunnel failed, response 403"}})
        self.assertIn("mm_95365c5b8a72", json.loads(got)["hookSpecificOutput"]["additionalContext"])

    def test_host_not_allowed_on_failure_event(self):
        got = run({"tool_name": "Bash", "hook_event_name": "PostToolUseFailure", "error": "host_not_allowed"})
        self.assertEqual(json.loads(got)["hookSpecificOutput"]["hookEventName"], "PostToolUseFailure")

    def test_webfetch_enotfound(self):
        self.assertTrue(run({"tool_name": "WebFetch", "tool_response": "ENOTFOUND example.org"}))

    def test_ordinary_output_is_silent(self):
        self.assertEqual(run({"tool_name": "Bash", "tool_response": {"stdout": "ok"}}), "")

    def test_other_tools_are_ignored(self):
        self.assertEqual(run({"tool_name": "Read", "tool_response": "CONNECT tunnel failed"}), "")

    def test_bad_stdin_is_silent(self):
        with mock.patch("sys.stdin", io.StringIO("not json")):
            self.assertEqual(hook.main(), 0)


if __name__ == "__main__":
    unittest.main()
