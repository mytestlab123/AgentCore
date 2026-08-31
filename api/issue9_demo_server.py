#!/usr/bin/env python3

import hashlib
import json
import os
import signal
import subprocess
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


REPO_DIR = Path(__file__).resolve().parents[1]
PROOF_SCRIPT = REPO_DIR / "scripts" / "bedrock-api-key-poc.sh"
CODEX_KEY_SCRIPT = REPO_DIR / "scripts" / "create-codex-bedrock-key.sh"
DEFAULT_EVIDENCE_ROOT = Path.home() / ".AGENTS-temp" / "AgentCore" / "issue9-gui"
DEFAULT_RETAINED_CREDENTIAL = Path.home() / ".AGENTS-temp" / "AgentCore" / "issue9-retained" / "credential.json"
DEFAULT_CODEX_RETAINED_DIR = Path.home() / ".AGENTS-temp" / "AgentCore" / "issue12-codex-key"
ALLOWED_MODEL = "apac.amazon.nova-lite-v1:0"
RESTRICTED_MODEL = "apac.amazon.nova-pro-v1:0"


def _read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _request_hash(value):
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _public_event(event):
    return {
        "eventTime": event.get("eventTime"),
        "eventSource": event.get("eventSource"),
        "eventName": event.get("eventName"),
        "errorCode": event.get("errorCode"),
        "modelId": event.get("modelId"),
        "bearerToken": event.get("bearerToken"),
        "actorType": event.get("actorType"),
        "requestIdSha256": _request_hash(event.get("requestId")),
    }


def build_public_status(evidence_dir, process_running=False, return_code=None):
    key = _read_json(evidence_dir / "key-metadata.json")
    allowed = _read_json(evidence_dir / "allow.json")
    denied = _read_json(evidence_dir / "deny.json")
    cleanup = _read_json(evidence_dir / "cleanup.json")
    audit = _read_json(evidence_dir / "cloudtrail.json")
    result = _read_json(evidence_dir / "result.json")
    raw_allowed = _read_json(evidence_dir / "private" / "allowed-response.json")

    response_text = None
    if raw_allowed:
        try:
            response_text = raw_allowed["output"]["message"]["content"][0]["text"]
        except (KeyError, IndexError, TypeError):
            response_text = None

    lifecycle_verified = bool(
        cleanup
        and not cleanup.get("cleanupFailed")
        and (
            cleanup.get("intentionallyRetained")
            or (cleanup.get("credentialDeleted") and cleanup.get("userDeleted"))
        )
    )
    core_proof_complete = bool(
        allowed
        and allowed.get("httpStatus") == 200
        and denied
        and denied.get("httpStatus") == 403
        and lifecycle_verified
    )
    audit_verified = bool(result and result.get("cloudTrail"))

    if result and result.get("status") == "PASS" and return_code in (None, 0):
        state = "PASS"
    elif core_proof_complete:
        state = "PASS"
    elif process_running:
        state = "RUNNING"
    elif return_code is None:
        state = "READY"
    else:
        state = "FAIL"

    if not key:
        phase = "Creating Bedrock API key" if process_running else "Ready to start"
    elif not allowed:
        phase = "Invoking approved model"
    elif not denied:
        phase = "Testing restricted model"
    elif not cleanup:
        phase = "Applying credential lifecycle"
    elif core_proof_complete and not audit_verified:
        phase = "Core proof complete; CloudTrail pending"
    else:
        phase = "Proof complete"

    public_allowed = None
    if allowed:
        public_allowed = {
            "decision": allowed.get("result"),
            "model": allowed.get("model"),
            "httpStatus": allowed.get("httpStatus"),
            "inputTokens": allowed.get("inputTokens"),
            "outputTokens": allowed.get("outputTokens"),
            "response": response_text,
            "requestIdSha256": _request_hash(allowed.get("requestId")),
        }

    public_denied = None
    if denied:
        public_denied = {
            "decision": denied.get("result"),
            "enforcedBy": denied.get("enforcedBy"),
            "model": denied.get("model"),
            "httpStatus": denied.get("httpStatus"),
            "requestIdSha256": _request_hash(denied.get("requestId")),
        }

    fingerprint = key.get("keyFingerprint") if key else None
    return {
        "state": state,
        "phase": phase,
        "auditState": "VERIFIED" if audit_verified else "PENDING" if core_proof_complete else "NOT_STARTED",
        "runId": evidence_dir.name,
        "profileAlias": "amit",
        "region": "ap-southeast-1",
        "key": {
            "created": bool(key),
            "masked": f"bedrock-{fingerprint}********" if fingerprint else None,
            "type": key.get("keyType") if key else None,
            "ageDays": key.get("credentialAgeDays") if key else None,
            "deleted": bool(cleanup and cleanup.get("credentialDeleted")),
        },
        "steps": {
            "keyCreated": bool(key),
            "approvedModelAllowed": bool(allowed and allowed.get("httpStatus") == 200),
            "restrictedModelDenied": bool(denied and denied.get("httpStatus") == 403),
            "cloudTrailCaptured": bool(result and result.get("cloudTrail")),
            "cleanupVerified": lifecycle_verified,
        },
        "allowed": public_allowed,
        "denied": public_denied,
        "cloudTrail": [_public_event(event) for event in (audit or [])],
        "cleanup": cleanup,
        "error": None if state != "FAIL" else "Live proof failed. Inspect protected local evidence.",
    }


class ProofController:
    def __init__(self, evidence_root=DEFAULT_EVIDENCE_ROOT, retained_credential=DEFAULT_RETAINED_CREDENTIAL):
        self.evidence_root = Path(evidence_root)
        self.retained_credential = Path(retained_credential)
        self.lock = threading.Lock()
        self.process = None
        self.evidence_dir = None
        self.return_code = None
        self.running = False
        if self.evidence_root.is_dir():
            for candidate in sorted(self.evidence_root.iterdir(), reverse=True):
                result = _read_json(candidate / "result.json") if candidate.is_dir() else None
                cleanup = _read_json(candidate / "cleanup.json") if candidate.is_dir() else None
                if result and result.get("status") == "PASS" and cleanup and cleanup.get("intentionallyRetained"):
                    self.evidence_dir = candidate
                    self.return_code = 0
                    break

    def reveal_key(self):
        try:
            mode = self.retained_credential.stat().st_mode & 0o777
        except OSError as error:
            raise RuntimeError("The retained demo key is not available.") from error
        if mode != 0o600:
            raise RuntimeError("The retained demo key must have mode 600.")
        credential = _read_json(self.retained_credential)
        if not credential:
            raise RuntimeError("The retained demo key is unreadable.")
        value = credential.get("ServiceSpecificCredential", {}).get("ServiceApiKeyValue")
        if not value:
            value = credential.get("ServiceSpecificCredential", {}).get("ServiceCredentialSecret")
        if not value:
            raise RuntimeError("The retained demo key has an unsupported format.")
        return {"key": value, "expiresInSeconds": 15}

    def start(self):
        with self.lock:
            if self.process and self.process.poll() is None:
                raise RuntimeError("A live proof is already running.")
            if self.evidence_dir:
                current = build_public_status(self.evidence_dir, False, self.return_code)
                if current["state"] == "PASS" and current["cleanup"] and current["cleanup"].get("intentionallyRetained"):
                    raise RuntimeError("A retained live proof already exists. Reuse it or run the explicit cleanup command.")
            run_id = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
            self.evidence_dir = self.evidence_root / run_id
            self.evidence_dir.mkdir(parents=True, mode=0o700, exist_ok=False)
            self.return_code = None
            self.running = True
            worker = threading.Thread(target=self._run, daemon=True)
            worker.start()
        return self.status()

    def _run(self):
        evidence_dir = self.evidence_dir
        env = os.environ.copy()
        env.update({
            "AWS_PROFILE": "amit",
            "AWS_REGION": "ap-southeast-1",
            "EVIDENCE_DIR": str(evidence_dir),
        })
        stdout_path = evidence_dir / "runner.stdout"
        stderr_path = evidence_dir / "runner.stderr"
        return_code = 1
        try:
            with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open(
                "w", encoding="utf-8"
            ) as stderr:
                process = subprocess.Popen(
                    ["/usr/bin/bash", str(PROOF_SCRIPT), "--approve-run"],
                    cwd=REPO_DIR,
                    env=env,
                    stdout=stdout,
                    stderr=stderr,
                    start_new_session=True,
                    text=True,
                )
                with self.lock:
                    self.process = process
                return_code = process.wait()
        finally:
            with self.lock:
                self.return_code = return_code
                self.running = False

    def status(self):
        with self.lock:
            evidence_dir = self.evidence_dir
            return_code = self.return_code
            running = self.running
        if not evidence_dir:
            return {
                "state": "READY",
                "phase": "Ready to start",
                "auditState": "NOT_STARTED",
                "profileAlias": "amit",
                "region": "ap-southeast-1",
                "key": {"created": False, "masked": None, "deleted": False},
                "steps": {
                    "keyCreated": False,
                    "approvedModelAllowed": False,
                    "restrictedModelDenied": False,
                    "cloudTrailCaptured": False,
                    "cleanupVerified": False,
                },
                "allowed": None,
                "denied": None,
                "cloudTrail": [],
                "cleanup": None,
                "error": None,
            }
        return build_public_status(evidence_dir, running, return_code)

    def stop(self):
        with self.lock:
            process = self.process
        if not process or process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signal.SIGINT)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=45)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                return
            process.wait(timeout=15)


class CodexKeyController:
    def __init__(self, retained_dir=DEFAULT_CODEX_RETAINED_DIR):
        self.retained_dir = Path(retained_dir)
        self.credential_file = self.retained_dir / "credential.json"
        self.metadata_file = self.retained_dir / "metadata.json"
        self.lock = threading.Lock()
        self.process = None
        self.running = False
        self.return_code = None

    def status(self):
        metadata = _read_json(self.metadata_file)
        with self.lock:
            running = self.running
            return_code = self.return_code
        if metadata and self.credential_file.is_file():
            return {
                "state": "CREATED", "model": metadata.get("model", ""),
                "masked": f"bedrock-{metadata.get('keyFingerprint', '')}********",
                "message": "Dedicated 30-day Codex key retained with cleanup=review.",
            }
        if running:
            return {"state": "RUNNING", "model": "", "masked": None, "message": "Creating dedicated AWS credential..."}
        if return_code not in (None, 0):
            return {"state": "FAIL", "model": "", "masked": None, "message": "Creation failed. Inspect protected local evidence."}
        return {"state": "READY", "model": "", "masked": None, "message": "Ready to create one dedicated Codex key."}

    def start(self, model):
        if not isinstance(model, str) or not model.startswith("openai.") or not all(
            character.isalnum() or character in ".-_" for character in model
        ):
            raise RuntimeError("Use an exact openai.* Bedrock model ID.")
        with self.lock:
            if self.running:
                raise RuntimeError("Codex key creation is already running.")
            if self.credential_file.exists():
                raise RuntimeError("A retained Codex key already exists.")
            self.running = True
            self.return_code = None
            threading.Thread(target=self._run, args=(model,), daemon=True).start()
        return self.status()

    def _run(self, model):
        env = os.environ.copy()
        env["ISSUE12_CODEX_MODEL"] = model
        evidence_dir = Path.home() / ".AGENTS-temp" / "AgentCore" / "issue12-codex-key-gui" / datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
        evidence_dir.mkdir(parents=True, mode=0o700, exist_ok=False)
        with (evidence_dir / "runner.stdout").open("w", encoding="utf-8") as stdout, (evidence_dir / "runner.stderr").open("w", encoding="utf-8") as stderr:
            process = subprocess.Popen(
                ["/usr/bin/bash", str(CODEX_KEY_SCRIPT), "--approve-run"],
                cwd=REPO_DIR, env=env, stdout=stdout, stderr=stderr,
                start_new_session=True, text=True,
            )
            with self.lock:
                self.process = process
            return_code = process.wait()
        with self.lock:
            self.return_code = return_code
            self.running = False

    def reveal_key(self):
        controller = ProofController(retained_credential=self.credential_file)
        return controller.reveal_key()

    def stop(self):
        with self.lock:
            process = self.process
        if process and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGINT)
                process.wait(timeout=30)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                return


class Issue9Handler(BaseHTTPRequestHandler):
    controller = None
    codex_controller = None
    allowed_origins = {
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    }

    def _send_json(self, status, body):
        origin = self.headers.get("Origin", "")
        encoded = json.dumps(body, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(encoded)))
        if origin in self.allowed_origins:
            self.send_header("access-control-allow-origin", origin)
            self.send_header("vary", "Origin")
        self.send_header("access-control-allow-methods", "GET,POST,OPTIONS")
        self.send_header("access-control-allow-headers", "content-type")
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self):
        self._send_json(204, {})

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._send_json(200, {
                "status": "ok",
                "mode": "ISSUE9_NATIVE_BEDROCK",
                "profileAlias": "amit",
                "region": "ap-southeast-1",
            })
            return
        if path == "/proof":
            self._send_json(200, self.controller.status())
            return
        if path == "/codex-key":
            self._send_json(200, self.codex_controller.status())
            return
        self._send_json(404, {"message": "Not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        origin = self.headers.get("Origin", "")
        if self.client_address[0] not in {"127.0.0.1", "::1"}:
            self._send_json(403, {"message": "Loopback access required"})
            return
        if origin not in self.allowed_origins:
            self._send_json(403, {"message": "Origin not allowed"})
            return
        if path == "/key/reveal":
            try:
                self._send_json(200, self.controller.reveal_key())
            except RuntimeError as error:
                self._send_json(409, {"message": str(error)})
            return
        if path == "/codex-key/reveal":
            try:
                self._send_json(200, self.codex_controller.reveal_key())
            except RuntimeError as error:
                self._send_json(409, {"message": str(error)})
            return
        if path == "/codex-key":
            try:
                content_length = int(self.headers.get("content-length", "0"))
                if content_length < 1 or content_length > 512:
                    raise RuntimeError("Invalid Codex key request.")
                body = json.loads(self.rfile.read(content_length))
                self._send_json(202, self.codex_controller.start(body.get("model")))
            except (RuntimeError, json.JSONDecodeError) as error:
                self._send_json(409, {"message": str(error)})
            return
        if path != "/proof":
            self._send_json(404, {"message": "Not found"})
            return
        try:
            status = self.controller.start()
        except (RuntimeError, FileExistsError) as error:
            self._send_json(409, {"message": str(error)})
            return
        self._send_json(202, status)

    def log_message(self, _format, *_args):
        return


def main():
    os.umask(0o077)
    profile = os.environ.get("AWS_PROFILE", "amit")
    region = os.environ.get("AWS_REGION", "ap-southeast-1")
    if profile != "amit" or region != "ap-southeast-1":
        raise SystemExit("ERROR: Issue #9 GUI is fixed to profile amit in ap-southeast-1.")
    if not os.environ.get("EXPECTED_AWS_ACCOUNT") or not os.environ.get("EXPECTED_AWS_CALLER_ARN"):
        raise SystemExit("ERROR: expected AWS account and caller gates are required.")

    port = int(os.environ.get("ISSUE9_API_PORT", "9019"))
    controller = ProofController()
    Issue9Handler.controller = controller
    Issue9Handler.codex_controller = CodexKeyController()
    server = ThreadingHTTPServer(("127.0.0.1", port), Issue9Handler)

    def stop_server(_signum, _frame):
        controller.stop()
        Issue9Handler.codex_controller.stop()
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGINT, stop_server)
    signal.signal(signal.SIGTERM, stop_server)
    print(f"Issue #9 backend ready at http://127.0.0.1:{port}", flush=True)
    try:
        server.serve_forever()
    finally:
        controller.stop()
        Issue9Handler.codex_controller.stop()
        server.server_close()


if __name__ == "__main__":
    main()
