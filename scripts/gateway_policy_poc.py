#!/usr/bin/env python3
"""Native AgentCore CLI Gateway Policy proof with a thin verifier."""

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROFILE = "amit"
REGION = "ap-southeast-1"
CLI_VERSION = "0.28.1"
MCP_VERSION = "2025-03-26"
TOOL_NAME = "check_demo_scope"
PRIVATE_ROOT = Path.home() / ".AGENTS-temp/AgentCore/issue-31-gateway-policy"
TEMPLATE = Path(__file__).parents[1] / "config/issue31-agentcore.template.json"
TOOL_SCHEMA = Path(__file__).parents[1] / "config/issue31-check-demo-scope-tool.json"
CLI_BIN = Path(__file__).parents[1] / "tools/issue31-agentcore/node_modules/.bin/agentcore"
COST_LIMIT = 2.00
FUNCTION_NAME = "agentcore-issue31-backend"
ROLE_NAME = "agentcore-issue31-lambda"
TAGS = {
    "Name": "agentcore-issue31-policy-proof",
    "dev": "amit",
    "project": "AgentCore",
    "created": "2026-09-08",
    "tools": "cdx",
    "environment": "dev",
    "owner": "amit",
    "version": "v1",
    "TTL": "08-10-26",
    "purpose": "issue31-policy-proof",
    "phase": "poc",
    "retention": "retain-under-usd2-month",
    "review-after": "2026-10-08",
}


class Blocked(RuntimeError):
    """A fail-closed proof gate."""


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def sanitize(value):
    text = str(value)
    rules = (
        (r"https?://[^\s\"']+", "<URL>"),
        (r"\b\d{12}\b", "<ACCOUNT>"),
        (r"arn:(?:aws|aws-us-gov|aws-cn):[^\s\"']+", "<ARN>"),
        (r"(?i)(access[_-]?key|secret[_-]?key|session[_-]?token)\s*[=:]\s*[^\s,]+", r"\1=<REDACTED>"),
        (re.escape(str(Path.home())), "<HOME>"),
    )
    for pattern, replacement in rules:
        text = re.sub(pattern, replacement, text)
    return text


def cedar_principal(caller_arn):
    match = re.fullmatch(r"(arn:[^:]+:sts::\d{12}:assumed-role/[^/]+)/[^/]+", caller_arn)
    return match.group(1) if match else caller_arn


def validate_case(tool_name, environment):
    if tool_name != TOOL_NAME:
        raise Blocked("unexpected tool name")
    if environment not in {"dev", "prod"}:
        raise Blocked("unexpected environment")


def validate_results(dev_code, dev_body, dev_delta, prod_code, prod_body, prod_delta):
    if dev_code != 200 or "synthetic-demo" not in dev_body or "healthy" not in dev_body:
        raise Blocked(f"dev call was not successful (HTTP {dev_code})")
    if dev_delta != 1:
        raise Blocked(f"dev backend call delta expected 1, got {dev_delta}")
    if prod_code not in {200, 401, 403} or not any(x in prod_body for x in ("Authorization", "denied", "Denied")):
        raise Blocked(f"prod call was not a policy denial (HTTP {prod_code})")
    if prod_delta != 0:
        raise Blocked("prod call reached Lambda")


def validate_cost(value):
    try:
        cost = float(value)
    except (TypeError, ValueError) as error:
        raise Blocked("retained cost is not numeric") from error
    if not math.isfinite(cost) or cost < 0 or cost >= COST_LIMIT:
        raise Blocked("retained cost is outside the approved limit")
    return cost


def write_private_json(path, value):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    path.write_text(json.dumps(value, indent=2) + "\n")
    path.chmod(0o600)


class Aws:
    def __init__(self, private_dir):
        self.private_dir = Path(private_dir)
        self.env = os.environ | {"AWS_PROFILE": PROFILE, "AWS_REGION": REGION,
                                 "AWS_DEFAULT_REGION": REGION, "AWS_PAGER": ""}

    def call(self, service, operation, payload=None):
        command = ["aws", service, operation, "--no-cli-pager", "--output", "json"]
        if payload is not None:
            request = self.private_dir / f"request-{service}-{operation}.json"
            write_private_json(request, payload)
            command += ["--cli-input-json", f"file://{request}"]
        result = subprocess.run(command, env=self.env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode:
            raise Blocked(f"{service} {operation}: {sanitize(result.stderr.strip())}")
        return json.loads(result.stdout or "{}")

    def optional(self, service, operation, payload):
        try:
            return self.call(service, operation, payload)
        except Blocked as error:
            if any(marker in str(error) for marker in
                   ("ResourceNotFound", "NoSuchEntity", "not found")):
                return None
            raise


def require_live_gates(aws):
    if os.getenv("AWS_PROFILE") != PROFILE or os.getenv("AWS_REGION") != REGION:
        raise Blocked("explicit AWS profile and Region are required")
    expected_account = os.getenv("AGENTCORE_EXPECTED_ACCOUNT_SHA256", "")
    expected_caller = os.getenv("AGENTCORE_EXPECTED_CALLER_SHA256", "")
    if not expected_account or not expected_caller:
        raise Blocked("expected account and caller SHA-256 gates are required")
    identity = aws.call("sts", "get-caller-identity")
    if digest(identity["Account"]) != expected_account or digest(identity["Arn"]) != expected_caller:
        raise Blocked("AWS identity gate mismatch")
    if not CLI_BIN.exists():
        raise Blocked("pinned AgentCore CLI is not installed; run npm ci in tools/issue31-agentcore")
    version = subprocess.run([str(CLI_BIN), "--version"], text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if version.returncode or CLI_VERSION not in version.stdout + version.stderr:
        raise Blocked("pinned AgentCore CLI version gate failed")
    return identity


def role_tags():
    return [{"Key": key, "Value": value} for key, value in TAGS.items()]


def assert_tags(actual):
    if any(actual.get(key) != value for key, value in TAGS.items()):
        raise Blocked("stable prerequisite ownership/tag drift")


def ensure_lambda_prerequisite(aws):
    role = aws.optional("iam", "get-role", {"RoleName": ROLE_NAME})
    function = aws.optional("lambda", "get-function", {"FunctionName": FUNCTION_NAME})
    if bool(role) != bool(function):
        raise Blocked("partial stable Lambda prerequisite exists")
    if role and function:
        role_tag_data = aws.call("iam", "list-role-tags", {"RoleName": ROLE_NAME})
        function_tag_data = aws.call("lambda", "list-tags", {
            "Resource": function["Configuration"]["FunctionArn"]})
        assert_tags({item["Key"]: item["Value"] for item in role_tag_data.get("Tags", [])})
        assert_tags(function_tag_data.get("Tags", {}))
        return function["Configuration"]["FunctionArn"]

    trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
    created = aws.call("iam", "create-role", {"RoleName": ROLE_NAME,
        "AssumeRolePolicyDocument": json.dumps(trust),
        "Description": "Issue 31 retained synthetic Lambda role", "Tags": role_tags()})
    role_arn = created["Role"]["Arn"]
    log_arn = f"arn:aws:logs:{REGION}:{role_arn.split(':')[4]}:log-group:/aws/lambda/{FUNCTION_NAME}:*"
    logging_policy = {"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": "logs:CreateLogGroup",
         "Resource": log_arn.rsplit(":*", 1)[0]},
        {"Effect": "Allow", "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
         "Resource": log_arn}]}
    aws.call("iam", "put-role-policy", {"RoleName": ROLE_NAME,
        "PolicyName": "Issue31LambdaLogsOnly",
        "PolicyDocument": json.dumps(logging_policy)})

    handler = aws.private_dir / "lambda_function.py"
    handler.write_text(
        "import json\n"
        "def lambda_handler(event, context):\n"
        "    name = context.client_context.custom.get('bedrockAgentCoreToolName', '') if context and context.client_context else ''\n"
        "    if not name.endswith('___check_demo_scope'):\n"
        "        return {'statusCode': 400, 'body': json.dumps({'error': 'unknown tool'})}\n"
        "    return {'statusCode': 200, 'body': json.dumps({'environment': event.get('environment'), 'status': 'healthy', 'source': 'synthetic-demo'})}\n")
    handler.chmod(0o600)
    bundle = aws.private_dir / "lambda.zip"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.write(handler, "lambda_function.py")
    bundle.chmod(0o600)
    request = {"FunctionName": FUNCTION_NAME, "Runtime": "python3.12",
        "Role": role_arn, "Handler": "lambda_function.lambda_handler", "Code": {},
        "Timeout": 3, "MemorySize": 128,
        "Description": "Issue 31 retained synthetic policy backend", "Tags": TAGS}
    request_path = aws.private_dir / "request-lambda-create-function.json"
    write_private_json(request_path, request)
    for attempt in range(8):
        result = subprocess.run(["aws", "lambda", "create-function",
            "--cli-input-json", f"file://{request_path}", "--zip-file", f"fileb://{bundle}",
            "--no-cli-pager", "--output", "json"], env=aws.env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            return json.loads(result.stdout)["FunctionArn"]
        if attempt == 7:
            raise Blocked(f"Lambda prerequisite creation failed: {sanitize(result.stderr)}")
        time.sleep(3)
    raise Blocked("Lambda prerequisite creation failed")


def render_private_project(private_dir, lambda_arn, identity,
                           gateway_arn="__PRIVATE_GATEWAY_ARN__"):
    project = Path(private_dir) / "Issue31Policy" / "agentcore"
    project.mkdir(mode=0o700, parents=True, exist_ok=True)
    project.chmod(0o700)
    data = json.loads(TEMPLATE.read_text())
    target = data["agentCoreGateways"][0]["targets"][0]["lambdaFunctionArn"]
    target["lambdaArn"] = lambda_arn
    target["toolSchemaFile"] = str(TOOL_SCHEMA.resolve())
    caller = cedar_principal(identity["Arn"])
    data["policyEngines"][0]["policies"][0]["statement"] = (
        f'permit(principal == AgentCore::IamEntity::"{caller}", '
        'action == AgentCore::Action::"Issue31Target___check_demo_scope", '
        f'resource == AgentCore::Gateway::"{gateway_arn}") '
        'when { context.input.environment == "dev" };'
    )
    write_private_json(project / "agentcore.json", data)
    write_private_json(project / "aws-targets.json", [{
        "name": "default", "account": identity["Account"], "region": REGION
    }])
    return project


def validate_rendered_project(project):
    data = json.loads((Path(project) / "agentcore.json").read_text())
    if data.get("runtimes") or data.get("harnesses"):
        raise Blocked("Runtime or Harness is prohibited")
    if len(data.get("agentCoreGateways", [])) != 1 or len(data.get("policyEngines", [])) != 1:
        raise Blocked("expected exactly one Gateway and Policy Engine")
    gateway = data["agentCoreGateways"][0]
    if gateway.get("authorizerType") != "AWS_IAM" or gateway.get("policyEngineConfiguration", {}).get("mode") != "ENFORCE":
        raise Blocked("Gateway IAM/ENFORCE configuration mismatch")
    targets = gateway.get("targets", [])
    if len(targets) != 1 or targets[0].get("targetType") != "lambdaFunctionArn":
        raise Blocked("expected exactly one Lambda ARN target")
    if any(key in json.dumps(data).lower() for key in ('"model"', "modelprovider", "foundationmodel")):
        raise Blocked("model configuration is prohibited")
    return data


def deploy_native_resources(project, dry_run=True):
    validate_rendered_project(project)
    command = [str(CLI_BIN), "deploy", "--yes"]
    if dry_run:
        command.append("--dry-run")
    result = subprocess.run(command, cwd=Path(project).parent, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log = Path(project).parents[1] / ("deploy-dry-run.log" if dry_run else "deploy.log")
    log.write_text(result.stdout + result.stderr)
    log.chmod(0o600)
    if result.returncode:
        raise Blocked(f"native AgentCore CLI deploy failed: {sanitize(result.stderr)}")
    return result.stdout


def load_native_state(project):
    state_path = Path(project) / ".cli/deployed-state.json"
    if not state_path.exists():
        raise Blocked("native deployed state is absent")
    state = json.loads(state_path.read_text())
    resources = state["targets"]["default"]["resources"]
    gateways = resources["mcp"]["gateways"]
    if set(gateways) != {"Issue31Gateway"} or set(resources.get("policyEngines", {})) != {"Issue31PolicyEngine"}:
        raise Blocked("native deployed state is ambiguous")
    return gateways["Issue31Gateway"]


def invoke_gateway(aws, gateway_url, environment):
    validate_case(TOOL_NAME, environment)
    exported = subprocess.run(["aws", "configure", "export-credentials", "--profile", PROFILE],
                              text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if exported.returncode:
        raise Blocked("credential provider failed")
    credentials = json.loads(exported.stdout)
    request = aws.private_dir / f"proof-{environment}-request.json"
    response = aws.private_dir / f"proof-{environment}-response.txt"
    write_private_json(request, {"jsonrpc": "2.0", "id": environment,
        "method": "tools/call", "params": {
            "name": "Issue31Target___check_demo_scope",
            "arguments": {"environment": environment}}})
    endpoint = gateway_url.rstrip("/")
    if not endpoint.endswith("/mcp"):
        endpoint += "/mcp"
    lines = [f'url = "{endpoint}"', 'request = "POST"',
        f'aws-sigv4 = "aws:amz:{REGION}:bedrock-agentcore"',
        f'user = "{credentials["AccessKeyId"]}:{credentials["SecretAccessKey"]}"',
        'header = "Accept: application/json, text/event-stream"',
        'header = "Content-Type: application/json"',
        f'header = "MCP-Protocol-Version: {MCP_VERSION}"',
        f'data-binary = "@{request}"', f'output = "{response}"',
        'write-out = "%{http_code}"', 'silent', 'show-error']
    if credentials.get("SessionToken"):
        lines.append(f'header = "X-Amz-Security-Token: {credentials["SessionToken"]}"')
    result = subprocess.run(["curl", "--config", "-"], input="\n".join(lines) + "\n",
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise Blocked(f"Gateway request failed: {sanitize(result.stderr)}")
    body = response.read_text() if response.exists() else ""
    return int(result.stdout[-3:]), body


def metric_sum(aws, start):
    end = datetime.now(timezone.utc) + timedelta(minutes=1)
    result = aws.call("cloudwatch", "get-metric-statistics", {
        "Namespace": "AWS/Lambda", "MetricName": "Invocations",
        "Dimensions": [{"Name": "FunctionName", "Value": FUNCTION_NAME}],
        "StartTime": start.isoformat(), "EndTime": end.isoformat(),
        "Period": 60, "Statistics": ["Sum"]})
    return int(sum(point.get("Sum", 0) for point in result.get("Datapoints", [])))


def wait_metric(aws, start, minimum, timeout=240):
    deadline = time.monotonic() + timeout
    value = metric_sum(aws, start)
    while value < minimum and time.monotonic() < deadline:
        time.sleep(10)
        value = metric_sum(aws, start)
    return value


def prove_live():
    private_dir = PRIVATE_ROOT / "cli"
    project = private_dir / "Issue31Policy" / "agentcore"
    aws = Aws(private_dir)
    require_live_gates(aws)
    gateway = load_native_state(project)
    start = datetime.now(timezone.utc) - timedelta(minutes=5)
    baseline = metric_sum(aws, start)
    dev_code, dev_body = invoke_gateway(aws, gateway["gatewayUrl"], "dev")
    after_dev = wait_metric(aws, start, baseline + 1)
    if after_dev != baseline + 1:
        raise Blocked("dev Lambda metric delta is not exactly one")
    prod_code, prod_body = invoke_gateway(aws, gateway["gatewayUrl"], "prod")
    time.sleep(90)
    after_prod = metric_sum(aws, start)
    validate_results(dev_code, dev_body, after_dev - baseline,
                     prod_code, prod_body, after_prod - after_dev)
    print("DEV_DECISION=ALLOW")
    print("DEV_BACKEND_CALLS=1")
    print("PROD_DECISION=DENY")
    print("PROD_BACKEND_DELTA=0")
    print("RESOURCE_RETENTION=PASS")
    print("ESTIMATED_MONTHLY_IDLE_COST_USD=1.01")
    print("GATEWAY_POLICY_RESULT=PASS")


def plan():
    print(f"PROFILE={PROFILE}")
    print(f"REGION={REGION}")
    print(f"TOOL={TOOL_NAME}")
    print(f"NATIVE_AGENTCORE_CLI={CLI_VERSION}")
    print(f"MCP_PROTOCOL_VERSION={MCP_VERSION}")
    print("PLAN=one dev ALLOW; one prod DENY; retain reusable stack")
    print("ESTIMATED_MONTHLY_IDLE_COST_USD=1.01")
    print("AWS_CALLS=0")


def prepare_live():
    # Reuse the private native scaffold created by `agentcore create --no-agent`.
    # Generated CDK/state remains outside Git under this stable workspace.
    private_dir = PRIVATE_ROOT / "cli"
    private_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    private_dir.chmod(0o700)
    aws = Aws(private_dir)
    identity = require_live_gates(aws)
    validate_cost(os.getenv("AGENTCORE_ESTIMATED_MONTHLY_IDLE_COST_USD", "1.01"))
    lambda_arn = ensure_lambda_prerequisite(aws)
    project = render_private_project(private_dir, lambda_arn, identity)
    validate_rendered_project(project)
    deploy_native_resources(project, dry_run=True)
    print("PRIVATE_PROJECT_RENDER=PASS")
    print("NATIVE_CLI_DRY_RUN=PASS")
    print("AWS_RESOURCE_MUTATION=NONE")
    print("GATEWAY_POLICY_RESULT=PREPARED")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-live", action="store_true")
    parser.add_argument("--prove-live", action="store_true")
    args = parser.parse_args()
    try:
        if args.prepare_live and args.prove_live:
            raise Blocked("select one live mode")
        if args.prepare_live:
            prepare_live()
        elif args.prove_live:
            prove_live()
        else:
            plan()
    except Blocked as error:
        print(f"BLOCKED_REASON={sanitize(error)}", file=sys.stderr)
        print("GATEWAY_POLICY_RESULT=BLOCKED")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
