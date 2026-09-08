#!/usr/bin/env python3
"""Offline regression checks for the Issue #38 loopback visual verifier."""

import contextlib
import json
import threading
import unittest
import urllib.error
import urllib.request
from unittest import mock

import gateway_policy_poc as proof
import gateway_visual_demo as visual


class GatewayVisualDemoTest(unittest.TestCase):
    def start_server(self, controller):
        server = visual.create_server(port=0, controller=controller)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        def cleanup():
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        self.addCleanup(cleanup)
        return f"http://127.0.0.1:{server.server_port}"

    def test_listener_is_loopback_and_occupied_port_blocks_startup(self):
        server = visual.create_server(port=0)
        self.addCleanup(server.server_close)
        self.assertEqual(server.server_address[0], "127.0.0.1")
        with self.assertRaises(OSError):
            visual.create_server(port=server.server_port)

    def test_only_fixed_bodyless_actions_are_accepted(self):
        calls = []

        def runner(action):
            calls.append(action)
            return visual.public_result(
                "ALLOW" if action == "allow" else "DENY",
                1 if action == "allow" else 0, "PASS", "PENDING")

        base = self.start_server(visual.GatewayVisualController(runner))
        with urllib.request.urlopen(urllib.request.Request(
                f"{base}/api/allow", data=b"", headers={"Origin": base}, method="POST")) as response:
            result = json.loads(response.read())
        self.assertEqual(result["decision"], "ALLOW")
        self.assertEqual(calls, ["allow"])
        localhost = base.replace("127.0.0.1", "localhost")
        with urllib.request.urlopen(urllib.request.Request(
                f"{localhost}/api/allow", data=b"", headers={"Origin": localhost}, method="POST")) as response:
            result = json.loads(response.read())
        self.assertEqual(result["decision"], "ALLOW")
        self.assertEqual(calls, ["allow", "allow"])
        for path, data in (("/api/unknown", b""), ("/api/allow?environment=prod", b""),
                           ("/api/allow", b'{"environment":"prod"}')):
            with self.subTest(path=path), self.assertRaises(urllib.error.HTTPError) as rejected:
                urllib.request.urlopen(urllib.request.Request(
                    f"{base}{path}", data=data, headers={"Origin": base}, method="POST"))
            self.assertIn(rejected.exception.code, {403, 404})
        self.assertEqual(calls, ["allow", "allow"])

    def test_cross_origin_or_rebound_host_never_reaches_action_runner(self):
        calls = []

        def runner(action):
            calls.append(action)
            return visual.public_result("ALLOW", 1, "PASS", "PENDING")

        base = self.start_server(visual.GatewayVisualController(runner))
        rejected_headers = (
            {},
            {"Origin": "http://attacker.invalid"},
            {"Origin": base, "Host": "attacker.invalid"},
        )
        for headers in rejected_headers:
            with self.subTest(headers=headers), self.assertRaises(urllib.error.HTTPError) as rejected:
                urllib.request.urlopen(urllib.request.Request(
                    f"{base}/api/allow", data=b"", headers=headers, method="POST"))
            self.assertEqual(rejected.exception.code, 403)
        self.assertEqual(calls, [])

    def test_page_and_blocked_result_never_expose_private_values(self):
        controller = visual.GatewayVisualController(
            lambda _action: (_ for _ in ()).throw(proof.Blocked(
                "arn:aws:iam::111122223333:role/private https://private.invalid")))
        base = self.start_server(controller)
        with urllib.request.urlopen(f"{base}/") as response:
            page = response.read().decode()
            self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertIn('data-testid="gateway-visual-demo"', page)
        self.assertNotRegex(page, visual.PRIVATE_PATTERN)
        with urllib.request.urlopen(f"{base}/favicon.ico") as response:
            self.assertEqual(response.status, 204)
            self.assertEqual(response.read(), b"")
        with urllib.request.urlopen(urllib.request.Request(
                f"{base}/api/deny", data=b"", headers={"Origin": base}, method="POST")) as response:
            blocked = response.read().decode()
        for prohibited in ("arn:aws", "111122223333", "https://private.invalid"):
            self.assertNotIn(prohibited, blocked)
        self.assertIn('"decision":"BLOCKED"', blocked)

    def test_allow_and_deny_require_exact_backend_deltas(self):
        def runner(action):
            return visual.public_result(
                "ALLOW" if action == "allow" else "DENY",
                1 if action == "allow" else 0, "PASS", "PENDING")

        controller = visual.GatewayVisualController(runner)
        self.assertEqual(controller.run("allow")["gatewayVisualResult"], "PENDING")
        self.assertEqual(controller.run("deny")["gatewayVisualResult"], "PASS")

        bad = visual.GatewayVisualController(
            lambda _action: {"decision": "ALLOW", "backendDelta": 0,
                             "retainedCostGate": "PASS"})
        self.assertEqual(bad.run("allow")["decision"], "BLOCKED")
        cost_blocked = visual.GatewayVisualController(
            lambda _action: {"decision": "ALLOW", "backendDelta": 1,
                             "retainedCostGate": "BLOCKED"})
        self.assertEqual(cost_blocked.run("allow")["decision"], "BLOCKED")
        self.assertEqual(bad.run("unknown")["decision"], "BLOCKED")

    def test_live_action_uses_only_read_invoke_helpers(self):
        aws = mock.Mock()
        gateway = {"gatewayUrl": "https://example.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com"}
        evidence = {"backend_delta": 1}
        with mock.patch.object(visual, "approved_live_environment", return_value=contextlib.nullcontext()), \
                mock.patch.object(proof, "retained_live_context", return_value=(aws, gateway, 1.01)), \
                mock.patch.object(proof, "prove_fixed_action", return_value=evidence) as invoke, \
                mock.patch.object(proof, "ensure_lambda_prerequisite") as ensure, \
                mock.patch.object(proof, "converge_native") as converge, \
                mock.patch.object(proof, "deploy_native_resources") as deploy, \
                mock.patch.object(proof, "prepare_live") as prepare:
            result = visual.run_fixed_action("allow")
        self.assertEqual(result["decision"], "ALLOW")
        invoke.assert_called_once_with(aws, gateway, "dev")
        ensure.assert_not_called()
        converge.assert_not_called()
        deploy.assert_not_called()
        prepare.assert_not_called()

    def test_identity_or_policy_drift_is_sanitized_as_blocked(self):
        controller = visual.GatewayVisualController(
            lambda _action: (_ for _ in ()).throw(proof.Blocked(
                "identity mismatch for arn:aws:iam::111122223333:role/private")))
        result = controller.run("allow")
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertFalse(result["infrastructureMutation"])
        self.assertNotRegex(json.dumps(result), visual.PRIVATE_PATTERN)


if __name__ == "__main__":
    unittest.main()
