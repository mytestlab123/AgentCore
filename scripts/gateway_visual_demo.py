#!/usr/bin/env python3
"""Loopback-only visual verifier for the retained Issue #31 Gateway Policy."""

import argparse
import contextlib
import json
import os
import re
import stat
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import gateway_policy_poc as proof

HOST = "127.0.0.1"
PORT = 3334
ACTIONS = {"allow": "dev", "deny": "prod"}
PRIVATE_MARKER = "latest-preflight-path"
PRIVATE_PATTERN = re.compile(
    r"(?i)(arn:|https?://|\b\d{12}\b|access.?key|secret|session.?token|"
    r"gatewayurl|policyengine|resourceid|caller)"
)


def blocked_result():
    return {
        "decision": "BLOCKED",
        "backendDelta": None,
        "retainedCostGate": "BLOCKED",
        "infrastructureMutation": False,
        "message": "Gateway verification is blocked. Inspect private server evidence.",
        "gatewayVisualResult": "BLOCKED",
    }


def public_result(decision, backend_delta, retained_cost_gate, overall):
    if decision not in {"ALLOW", "DENY"}:
        raise proof.Blocked("unexpected visual decision")
    expected_delta = 1 if decision == "ALLOW" else 0
    if backend_delta != expected_delta:
        raise proof.Blocked("visual backend delta does not match fixed action")
    result = {
        "decision": decision,
        "backendDelta": backend_delta,
        "retainedCostGate": retained_cost_gate,
        "infrastructureMutation": False,
        "message": (
            "Allowed fixed synthetic check completed."
            if decision == "ALLOW"
            else "Denied fixed synthetic check completed; backend was not invoked."
        ),
        "gatewayVisualResult": overall,
    }
    encoded = json.dumps(result, sort_keys=True)
    if PRIVATE_PATTERN.search(encoded):
        raise proof.Blocked("public visual result contains a prohibited identifier")
    return result


def expected_identity_hashes():
    """Derive the existing private identity gate without exposing its values."""
    root = proof.PRIVATE_ROOT.resolve()
    marker = root / PRIVATE_MARKER
    if marker.is_symlink() or not marker.is_file():
        raise proof.Blocked("approved identity record is unavailable")
    if stat.S_IMODE(marker.stat().st_mode) & 0o077:
        raise proof.Blocked("approved identity marker permissions are unsafe")
    candidate = Path(marker.read_text(encoding="utf-8").strip()).resolve()
    identity_file = candidate / "identity.json" if candidate.is_dir() else candidate
    if identity_file.is_symlink() or root not in identity_file.parents:
        raise proof.Blocked("approved identity record path is unsafe")
    if not identity_file.is_file() or stat.S_IMODE(identity_file.stat().st_mode) & 0o077:
        raise proof.Blocked("approved identity record permissions are unsafe")
    identity = json.loads(identity_file.read_text(encoding="utf-8"))
    account = identity.get("Account")
    caller = identity.get("Arn")
    if not isinstance(account, str) or not isinstance(caller, str) or not account or not caller:
        raise proof.Blocked("approved identity record is malformed")
    return proof.digest(account), proof.digest(caller)


@contextlib.contextmanager
def approved_live_environment():
    """Pin only the approved profile, Region, and private identity hashes."""
    account_hash, caller_hash = expected_identity_hashes()
    values = {
        "AWS_PROFILE": proof.PROFILE,
        "AWS_REGION": proof.REGION,
        "AGENTCORE_EXPECTED_ACCOUNT_SHA256": account_hash,
        "AGENTCORE_EXPECTED_CALLER_SHA256": caller_hash,
    }
    previous = {name: os.environ.get(name) for name in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def run_fixed_action(action):
    """Run exactly one retained Gateway request; never invoke a repair path."""
    environment = ACTIONS.get(action)
    if environment is None:
        raise proof.Blocked("only fixed visual actions are permitted")
    with approved_live_environment():
        aws, gateway, cost = proof.retained_live_context()
        evidence = proof.prove_fixed_action(aws, gateway, environment)
    return public_result(
        "ALLOW" if environment == "dev" else "DENY",
        evidence["backend_delta"],
        "PASS" if proof.validate_cost(cost) < proof.COST_LIMIT else "BLOCKED",
        "PENDING",
    )


class GatewayVisualController:
    def __init__(self, action_runner=run_fixed_action):
        self._action_runner = action_runner
        self._lock = threading.Lock()
        self._passed_actions = set()

    def run(self, action):
        if action not in ACTIONS:
            return blocked_result()
        with self._lock:
            try:
                result = self._action_runner(action)
                decision = result.get("decision")
                expected = "ALLOW" if action == "allow" else "DENY"
                expected_delta = 1 if action == "allow" else 0
                if (decision != expected or result.get("backendDelta") != expected_delta
                        or result.get("retainedCostGate") != "PASS"):
                    raise proof.Blocked("fixed visual result is incomplete")
                self._passed_actions.add(action)
                result["gatewayVisualResult"] = (
                    "PASS" if self._passed_actions == set(ACTIONS) else "PENDING"
                )
                return public_result(
                    result["decision"], result["backendDelta"],
                    result["retainedCostGate"], result["gatewayVisualResult"],
                )
            except (proof.Blocked, OSError, ValueError, json.JSONDecodeError):
                return blocked_result()


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>AgentCore Gateway Policy Visual Demo</title>
<style>
body{margin:0;background:#08111e;color:#ecf4ff;font:16px system-ui,sans-serif}main{max-width:760px;margin:4rem auto;padding:2rem}h1{margin-top:0}.note{color:#b9c9dc}.card{border:1px solid #29425e;border-radius:12px;margin:1rem 0;padding:1.25rem;background:#0d1b2d}button{background:#3178e8;color:#fff;border:0;border-radius:7px;padding:.7rem 1rem;font-weight:700;cursor:pointer}button:disabled{opacity:.55}.result{white-space:pre-line;font-family:ui-monospace,monospace;margin-top:1rem;color:#d6e8ff}.pass{color:#5ee6a8}.blocked{color:#ffb3b3}</style>
</head><body><main data-testid="gateway-visual-demo">
<h1>AgentCore Gateway Policy Visual Demo</h1>
<p class="note">Loopback-only visual verification. No model, LibreChat, or infrastructure mutation.</p>
<p class="result" data-testid="overall-result">GATEWAY_VISUAL_RESULT=PENDING</p>
<section class="card"><h2>Allowed synthetic check</h2><button data-testid="run-allow" type="button">Run ALLOW test</button><p class="result" data-testid="allow-result">Not run</p></section>
<section class="card"><h2>Denied synthetic check</h2><button data-testid="run-deny" type="button">Run DENY test</button><p class="result" data-testid="deny-result">Not run</p></section>
</main><script>
const overall=document.querySelector('[data-testid="overall-result"]');
function render(action,result){const target=document.querySelector(`[data-testid="${action}-result"]`);target.textContent=`${result.decision}\nBACKEND DELTA ${result.backendDelta ?? 'N/A'}\n${result.retainedCostGate === 'PASS' ? 'RETAINED COST GATE PASS' : 'RETAINED COST GATE BLOCKED'}\n${result.infrastructureMutation ? 'INFRASTRUCTURE MUTATION 1' : 'NO INFRASTRUCTURE MUTATION'}\n${result.message}`;target.className=`result ${result.decision === 'BLOCKED' ? 'blocked' : 'pass'}`;overall.textContent=`GATEWAY_VISUAL_RESULT=${result.gatewayVisualResult}`;overall.className=`result ${result.gatewayVisualResult === 'PASS' ? 'pass' : result.gatewayVisualResult === 'BLOCKED' ? 'blocked' : ''}`}
async function run(action){const button=document.querySelector(`[data-testid="run-${action}"]`);button.disabled=true;try{const response=await fetch(`/api/${action}`,{method:'POST',cache:'no-store'});render(action,await response.json())}catch(_){render(action,{decision:'BLOCKED',backendDelta:null,retainedCostGate:'BLOCKED',infrastructureMutation:false,message:'Gateway verification is blocked. Inspect private server evidence.',gatewayVisualResult:'BLOCKED'})}finally{button.disabled=false}}
document.querySelector('[data-testid="run-allow"]').addEventListener('click',()=>run('allow'));document.querySelector('[data-testid="run-deny"]').addEventListener('click',()=>run('deny'));
</script></body></html>"""


class GatewayVisualHandler(BaseHTTPRequestHandler):
    controller = GatewayVisualController()

    def log_message(self, _format, *_args):
        return

    def _send_json(self, status, value):
        encoded = json.dumps(value, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'none'")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_page(self):
        encoded = PAGE.encode()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_empty(self, status):
        self.send_response(status)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _is_same_loopback_origin(self):
        host, port = self.server.server_address[:2]
        authorities = {
            (f"{host}:{port}", f"http://{host}:{port}"),
            (f"localhost:{port}", f"http://localhost:{port}"),
        }
        return (
            self.client_address[0] == HOST
            and (self.headers.get("Host"), self.headers.get("Origin")) in authorities
        )

    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.query or parsed.fragment:
            self._send_json(HTTPStatus.BAD_REQUEST, blocked_result())
        elif parsed.path == "/":
            self._send_page()
        elif parsed.path == "/favicon.ico":
            self._send_empty(HTTPStatus.NO_CONTENT)
        elif parsed.path == "/health":
            self._send_json(HTTPStatus.OK, {"state": "READY"})
        else:
            self._send_json(HTTPStatus.NOT_FOUND, blocked_result())

    def do_POST(self):
        parsed = urlsplit(self.path)
        content_length = self.headers.get("Content-Length")
        if (not self._is_same_loopback_origin() or parsed.query or parsed.fragment
                or self.headers.get("Transfer-Encoding")
                or content_length not in {None, "0"}):
            self.close_connection = True
            self._send_json(HTTPStatus.FORBIDDEN, blocked_result())
            return
        action = {"/api/allow": "allow", "/api/deny": "deny"}.get(parsed.path)
        if action is None:
            self._send_json(HTTPStatus.NOT_FOUND, blocked_result())
            return
        self._send_json(HTTPStatus.OK, self.controller.run(action))


def create_server(port=PORT, controller=None):
    if controller is not None:
        GatewayVisualHandler.controller = controller
    return ThreadingHTTPServer((HOST, port), GatewayVisualHandler)


def serve_forever():
    server = create_server()
    print(f"GATEWAY_VISUAL_URL=http://localhost:{PORT}/", flush=True)
    print("GATEWAY_VISUAL_SERVER=READY", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true", help="serve the fixed loopback visual demo")
    args = parser.parse_args()
    if not args.serve:
        parser.error("--serve is required")
    try:
        serve_forever()
    except OSError:
        print("GATEWAY_VISUAL_RESULT=BLOCKED", flush=True)
        print("BLOCKED_REASON=loopback port 3334 is unavailable", flush=True)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
