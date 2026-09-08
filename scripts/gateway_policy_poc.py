#!/usr/bin/env python3
"""Native AgentCore Gateway Policy ALLOW/DENY proof for Issue #31."""

import argparse
import base64
import hashlib
import io
import json
import math
import os
import re
import subprocess
import sys
import time
import zipfile
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

PROFILE = "amit"
REGION = "ap-southeast-1"
CLI_VERSION = "0.28.1"
MCP_VERSION = "2025-03-26"
TOOL_NAME = "check_demo_scope"
FULL_TOOL_NAME = "Issue31Target___check_demo_scope"
PRIVATE_ROOT = Path.home() / ".AGENTS-temp/AgentCore/issue-31-gateway-policy"
TEMPLATE = Path(__file__).parents[1] / "config/issue31-agentcore.template.json"
TOOL_SCHEMA = Path(__file__).parents[1] / "config/issue31-check-demo-scope-tool.json"
CLI_BIN = Path(__file__).parents[1] / "tools/issue31-agentcore/node_modules/.bin/agentcore"
COST_LIMIT = 2.00
KMS_KEY_MONTHLY_USD = 1.00
OTHER_IDLE_BUFFER_USD = 0.01
S3_GB_MONTH_USD = 0.03
ECR_GB_MONTH_USD = 0.12
LOGS_GB_MONTH_USD = 0.60
FUNCTION_NAME = "agentcore-issue31-backend"
ROLE_NAME = "agentcore-issue31-lambda"
STACK_NAME = "AgentCore-Issue31Policy-default"
GATEWAY_NAME = "Issue31Gateway"
TARGET_NAME = "Issue31Target"
ENGINE_NAME = "Issue31PolicyEngine"
POLICY_NAME = "Issue31DevPermit"
EXPECTED_APP_COUNTS = Counter({
    "AWS::BedrockAgentCore::Gateway": 1,
    "AWS::BedrockAgentCore::GatewayTarget": 1,
    "AWS::BedrockAgentCore::Policy": 1,
    "AWS::BedrockAgentCore::PolicyEngine": 1,
    "AWS::CDK::Metadata": 1,
    "AWS::IAM::Policy": 1,
    "AWS::IAM::Role": 1,
})
EXPECTED_BOOTSTRAP_COUNTS = Counter({
    "AWS::ECR::Repository": 1,
    "AWS::IAM::Policy": 2,
    "AWS::IAM::Role": 5,
    "AWS::KMS::Alias": 1,
    "AWS::KMS::Key": 1,
    "AWS::S3::Bucket": 1,
    "AWS::S3::BucketPolicy": 1,
    "AWS::SSM::Parameter": 1,
})
TAGS = {
    "Name": "agentcore-issue31-policy-proof", "dev": "amit",
    "project": "AgentCore", "created": "2026-09-08", "tools": "cdx",
    "environment": "dev", "owner": "amit", "version": "v1",
    "TTL": "08-10-26", "purpose": "issue31-policy-proof", "phase": "poc",
    "retention": "retain-under-usd2-month", "review-after": "2026-10-08",
}


class Blocked(RuntimeError):
    """A fail-closed proof gate."""


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def scoped_aws_env(source=None):
    env = dict(os.environ if source is None else source)
    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
                 "AWS_SECURITY_TOKEN", "AWS_WEB_IDENTITY_TOKEN_FILE", "AWS_ROLE_ARN",
                 "AWS_ROLE_SESSION_NAME", "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI",
                 "AWS_CONTAINER_CREDENTIALS_FULL_URI"):
        env.pop(name, None)
    env.update({"AWS_PROFILE": PROFILE, "AWS_REGION": REGION,
                "AWS_DEFAULT_REGION": REGION, "AWS_PAGER": ""})
    return env


def sanitize(value):
    text = str(value)
    rules = (
        (r"https?://[^\s\"']+", "<URL>"),
        (r"\b\d{12}\b", "<ACCOUNT>"),
        (r"arn:(?:aws|aws-us-gov|aws-cn):[^\s\"']+", "<ARN>"),
        (r"(?i)(?:aws)?accesskeyid[\"']?\s*[:=]\s*[\"']?[^\s,\"']+", "AccessKeyId=<REDACTED>"),
        (r"(?i)(?:aws)?secretaccesskey[\"']?\s*[:=]\s*[\"']?[^\s,\"']+", "SecretAccessKey=<REDACTED>"),
        (r"(?i)(?:aws)?sessiontoken[\"']?\s*[:=]\s*[\"']?[^\s,\"']+", "SessionToken=<REDACTED>"),
        (r"(?i)(access[_-]?key|secret[_-]?key|session[_-]?token)\s*[=:]\s*[^\s,]+", r"\1=<REDACTED>"),
        (re.escape(str(Path.home())), "<HOME>"),
    )
    for pattern, replacement in rules:
        text = re.sub(pattern, replacement, text)
    return text


def private_path(path):
    root = PRIVATE_ROOT.resolve()
    candidate = Path(path)
    candidate.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    candidate.parent.chmod(0o700)
    resolved_parent = candidate.parent.resolve()
    if root != resolved_parent and root not in resolved_parent.parents:
        raise Blocked("private evidence path escaped approved root")
    if candidate.is_symlink():
        raise Blocked("private evidence path is a symlink")
    return candidate


def write_private_text(path, value):
    path = private_path(path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "w") as handle:
        handle.write(value)
    path.chmod(0o600)


def write_private_bytes(path, value):
    path = private_path(path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(value)
    path.chmod(0o600)


def write_private_json(path, value):
    write_private_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def harden_private_artifacts(project):
    """Protect generated state/evidence without changing tool executables."""
    project = Path(project)
    for path in (project / "agentcore.json", project / "aws-targets.json"):
        if path.exists():
            path.chmod(0o600)
    for root in (project / ".cli", project / "cdk" / "cdk.out"):
        if not root.exists():
            continue
        for directory, names, files in os.walk(root, followlinks=False):
            directory_path = Path(directory)
            if directory_path.is_symlink():
                raise Blocked("generated private directory is a symlink")
            directory_path.chmod(0o700)
            for name in names:
                child = directory_path / name
                if child.is_symlink():
                    raise Blocked("generated private directory contains a symlink")
            for name in files:
                child = directory_path / name
                if child.is_symlink():
                    raise Blocked("generated private evidence contains a symlink")
                child.chmod(0o600)


def read_json(path, label):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError, TypeError) as error:
        raise Blocked(f"{label} is missing or malformed") from error


def _json_object(value, label):
    try:
        parsed = json.loads(value) if isinstance(value, str) else value
    except json.JSONDecodeError as error:
        raise Blocked(f"{label} is not JSON") from error
    if not isinstance(parsed, dict):
        raise Blocked(f"{label} is not a JSON object")
    return parsed


def cedar_principal(caller_arn):
    match = re.fullmatch(r"(arn:[^:]+:sts::\d{12}:assumed-role/[^/]+)/[^/]+", caller_arn)
    return match.group(1) if match else caller_arn


def cedar_statement(caller_arn, gateway_arn):
    caller = cedar_principal(caller_arn)
    return (f'permit(principal == AgentCore::IamEntity::"{caller}", '
            f'action == AgentCore::Action::"{FULL_TOOL_NAME}", '
            f'resource == AgentCore::Gateway::"{gateway_arn}") '
            'when { context.input.environment == "dev" };')


def validate_case(tool_name, environment):
    if tool_name != TOOL_NAME:
        raise Blocked("unexpected tool name")
    if environment not in {"dev", "prod"}:
        raise Blocked("unexpected environment")


def parse_dev_response(http_code, body):
    if http_code != 200:
        raise Blocked(f"dev Gateway HTTP status was {http_code}")
    envelope = _json_object(body, "dev Gateway response")
    if envelope.get("jsonrpc") != "2.0" or envelope.get("id") != "dev" or "error" in envelope:
        raise Blocked("dev Gateway response envelope is not a successful dev result")
    result = envelope.get("result")
    if not isinstance(result, dict) or result.get("isError") is not False:
        raise Blocked("dev Gateway tool result reported an error")
    content = result.get("content")
    if (not isinstance(content, list) or len(content) != 1
            or not isinstance(content[0], dict) or content[0].get("type") != "text"):
        raise Blocked("dev Gateway tool content is ambiguous")
    lambda_result = _json_object(content[0].get("text"), "dev Lambda result")
    if lambda_result.get("statusCode") != 200:
        raise Blocked("dev Lambda status is not 200")
    payload = _json_object(lambda_result.get("body"), "dev Lambda body")
    expected = {"environment": "dev", "status": "healthy", "source": "synthetic-demo"}
    if payload != expected:
        raise Blocked("dev Lambda payload does not match the fixed synthetic result")
    return payload


def parse_prod_response(http_code, body):
    if http_code != 200:
        raise Blocked(f"prod Gateway HTTP status was {http_code}; policy denial was not proven")
    envelope = _json_object(body, "prod Gateway response")
    if envelope.get("jsonrpc") != "2.0" or envelope.get("id") != "prod" or "result" in envelope:
        raise Blocked("prod Gateway response envelope is not a policy error")
    error = envelope.get("error")
    if not isinstance(error, dict) or error.get("code") != -32002:
        raise Blocked("prod Gateway response is not the expected policy denial code")
    message = str(error.get("message", "")).lower()
    required = ("tool execution denied", "policy enforcement", "denied by default")
    if not all(fragment in message for fragment in required):
        raise Blocked("prod Gateway response is not an unambiguous deny-by-default decision")
    return error


def validate_results(dev_code, dev_body, dev_delta, prod_code, prod_body, prod_delta):
    parse_dev_response(dev_code, dev_body)
    if dev_delta != 1:
        raise Blocked(f"dev backend call delta expected 1, got {dev_delta}")
    parse_prod_response(prod_code, prod_body)
    if prod_delta != 0:
        raise Blocked(f"prod backend call delta expected 0, got {prod_delta}")


def validate_cost(value):
    try:
        cost = float(value)
    except (TypeError, ValueError) as error:
        raise Blocked("retained cost is not numeric") from error
    if not math.isfinite(cost) or cost < 0 or cost >= COST_LIMIT:
        raise Blocked("retained cost is outside the approved limit")
    return cost


class Aws:
    def __init__(self, private_dir):
        self.private_dir = Path(private_dir)
        self.env = scoped_aws_env()

    def call(self, service, operation, payload=None):
        command = ["aws", "--profile", PROFILE, "--region", REGION, service, operation,
                   "--no-cli-pager", "--output", "json"]
        if payload is not None:
            request = self.private_dir / f"request-{service}-{operation}.json"
            write_private_json(request, payload)
            command += ["--cli-input-json", f"file://{request}"]
        result = subprocess.run(command, env=self.env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=120)
        if result.returncode:
            raise Blocked(f"{service} {operation}: {sanitize(result.stderr.strip())}")
        try:
            return json.loads(result.stdout or "{}")
        except json.JSONDecodeError as error:
            raise Blocked(f"{service} {operation} returned malformed JSON") from error

    def optional(self, service, operation, payload):
        try:
            return self.call(service, operation, payload)
        except Blocked as error:
            if any(marker in str(error) for marker in
                   ("ResourceNotFound", "NoSuchEntity", "not found", "does not exist")):
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
    if digest(identity.get("Account", "")) != expected_account or digest(identity.get("Arn", "")) != expected_caller:
        raise Blocked("AWS identity gate mismatch")
    if not CLI_BIN.exists():
        raise Blocked("pinned AgentCore CLI is absent; run npm ci --force in tools/issue31-agentcore")
    version = subprocess.run([str(CLI_BIN), "--version"], text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if version.returncode or CLI_VERSION not in version.stdout + version.stderr:
        raise Blocked("pinned AgentCore CLI version gate failed")
    return identity


def role_tags():
    return [{"Key": key, "Value": value} for key, value in TAGS.items()]


def assert_tags(actual, label="resource"):
    missing = [key for key, value in TAGS.items() if actual.get(key) != value]
    if missing:
        raise Blocked(f"{label} ownership/tag drift: {','.join(sorted(missing))}")


def lambda_source():
    return (
        "import json\n"
        "def lambda_handler(event, context):\n"
        "    custom = context.client_context.custom if context and context.client_context else {}\n"
        "    name = custom.get('bedrockAgentCoreToolName', '')\n"
        "    if not name.endswith('___check_demo_scope'):\n"
        "        return {'statusCode': 400, 'body': json.dumps({'error': 'unknown tool'})}\n"
        "    environment = event.get('environment')\n"
        "    if environment not in ('dev', 'prod'):\n"
        "        return {'statusCode': 400, 'body': json.dumps({'error': 'unknown environment'})}\n"
        "    return {'statusCode': 200, 'body': json.dumps({'environment': environment, 'status': 'healthy', 'source': 'synthetic-demo'})}\n"
    )


def lambda_bundle():
    payload = io.BytesIO()
    info = zipfile.ZipInfo("lambda_function.py", (2026, 1, 1, 0, 0, 0))
    info.external_attr = 0o600 << 16
    with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(info, lambda_source())
    return payload.getvalue()


def expected_trust():
    return {"Version": "2012-10-17", "Statement": [{"Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}


def expected_logging_policy(account):
    log_arn = f"arn:aws:logs:{REGION}:{account}:log-group:/aws/lambda/{FUNCTION_NAME}:*"
    return {"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": "logs:CreateLogGroup",
         "Resource": log_arn.rsplit(":*", 1)[0]},
        {"Effect": "Allow", "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
         "Resource": log_arn}]}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def wait_lambda_ready(aws, timeout=120):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = aws.call("lambda", "get-function", {"FunctionName": FUNCTION_NAME})
        config = result["Configuration"]
        if config.get("State") == "Active" and config.get("LastUpdateStatus") in {None, "Successful"}:
            return result
        if config.get("State") == "Failed" or config.get("LastUpdateStatus") == "Failed":
            raise Blocked("synthetic Lambda entered a failed state")
        time.sleep(5)
    raise Blocked("synthetic Lambda did not become ready")


def ensure_log_group(aws):
    name = f"/aws/lambda/{FUNCTION_NAME}"
    result = aws.call("logs", "describe-log-groups", {"logGroupNamePrefix": name, "limit": 10})
    exact = [item for item in result.get("logGroups", []) if item.get("logGroupName") == name]
    if len(exact) > 1:
        raise Blocked("synthetic Lambda log group is ambiguous")
    if not exact:
        aws.call("logs", "create-log-group", {"logGroupName": name, "tags": TAGS})
    else:
        aws.call("logs", "tag-resource", {
            "resourceArn": exact[0]["arn"].removesuffix(":*"), "tags": TAGS})
    aws.call("logs", "put-retention-policy", {"logGroupName": name, "retentionInDays": 1})


def ensure_lambda_prerequisite(aws, identity):
    role = aws.optional("iam", "get-role", {"RoleName": ROLE_NAME})
    function = aws.optional("lambda", "get-function", {"FunctionName": FUNCTION_NAME})
    if bool(role) != bool(function):
        raise Blocked("partial stable Lambda prerequisite exists")
    bundle_bytes = lambda_bundle()
    write_private_text(aws.private_dir / "lambda_function.py", lambda_source())
    write_private_bytes(aws.private_dir / "lambda.zip", bundle_bytes)
    policy = expected_logging_policy(identity["Account"])
    if role and function:
        role_tags_data = aws.call("iam", "list-role-tags", {"RoleName": ROLE_NAME})
        function_tags = aws.call("lambda", "list-tags", {
            "Resource": function["Configuration"]["FunctionArn"]})
        assert_tags({item["Key"]: item["Value"] for item in role_tags_data.get("Tags", [])}, "Lambda role")
        assert_tags(function_tags.get("Tags", {}), "Lambda function")
        actual_trust = role["Role"].get("AssumeRolePolicyDocument", {})
        if isinstance(actual_trust, str):
            actual_trust = json.loads(unquote(actual_trust))
        if canonical(actual_trust) != canonical(expected_trust()):
            raise Blocked("Lambda role trust policy drift")
        actual_policy = aws.call("iam", "get-role-policy", {
            "RoleName": ROLE_NAME, "PolicyName": "Issue31LambdaLogsOnly"}).get("PolicyDocument", {})
        if isinstance(actual_policy, str):
            actual_policy = json.loads(unquote(actual_policy))
        if canonical(actual_policy) != canonical(policy):
            aws.call("iam", "put-role-policy", {"RoleName": ROLE_NAME,
                "PolicyName": "Issue31LambdaLogsOnly", "PolicyDocument": json.dumps(policy)})
        config = function["Configuration"]
        expected_config = {"Runtime": "python3.12", "Handler": "lambda_function.lambda_handler",
            "Role": role["Role"]["Arn"], "Timeout": 3, "MemorySize": 128,
            "Description": "Issue 31 retained synthetic policy backend"}
        drift = {key: value for key, value in expected_config.items() if config.get(key) != value}
        if drift:
            aws.call("lambda", "update-function-configuration", {"FunctionName": FUNCTION_NAME, **drift})
            function = wait_lambda_ready(aws)
            config = function["Configuration"]
        expected_hash = base64.b64encode(hashlib.sha256(bundle_bytes).digest()).decode()
        if config.get("CodeSha256") != expected_hash:
            aws.call("lambda", "update-function-code", {"FunctionName": FUNCTION_NAME,
                "ZipFile": base64.b64encode(bundle_bytes).decode(), "Publish": False})
            wait_lambda_ready(aws)
        ensure_log_group(aws)
        return function["Configuration"]["FunctionArn"]
    created = aws.call("iam", "create-role", {"RoleName": ROLE_NAME,
        "AssumeRolePolicyDocument": json.dumps(expected_trust()),
        "Description": "Issue 31 retained synthetic Lambda role", "Tags": role_tags()})
    role_arn = created["Role"]["Arn"]
    aws.call("iam", "put-role-policy", {"RoleName": ROLE_NAME,
        "PolicyName": "Issue31LambdaLogsOnly", "PolicyDocument": json.dumps(policy)})
    request = {"FunctionName": FUNCTION_NAME, "Runtime": "python3.12", "Role": role_arn,
        "Handler": "lambda_function.lambda_handler",
        "Code": {"ZipFile": base64.b64encode(bundle_bytes).decode()}, "Timeout": 3,
        "MemorySize": 128, "Description": "Issue 31 retained synthetic policy backend",
        "Tags": TAGS}
    for attempt in range(12):
        try:
            result = aws.call("lambda", "create-function", request)
            ensure_log_group(aws)
            return result["FunctionArn"]
        except Blocked:
            if attempt == 11:
                raise
            time.sleep(5)
    raise Blocked("Lambda prerequisite creation failed")


def ensure_private_scaffold(private_dir):
    project = Path(private_dir) / "Issue31Policy" / "agentcore"
    if project.exists():
        return project
    command = [str(CLI_BIN), "create", "--name", "Issue31Policy",
               "--project-name", "Issue31Policy", "--no-agent",
               "--output-dir", str(private_dir), "--skip-git",
               "--skip-python-setup", "--skip-install"]
    result = subprocess.run(command, cwd=private_dir, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    write_private_text(Path(private_dir) / "create.log", result.stdout + result.stderr)
    if result.returncode or not project.exists():
        raise Blocked(f"native AgentCore CLI scaffold failed: {sanitize(result.stderr)}")
    return project


def render_private_project(private_dir, lambda_arn, identity, gateway_arn=None,
                           include_policy=True):
    project = ensure_private_scaffold(private_dir)
    data = json.loads(TEMPLATE.read_text())
    target = data["agentCoreGateways"][0]["targets"][0]["lambdaFunctionArn"]
    target["lambdaArn"] = lambda_arn
    target["toolSchemaFile"] = str(TOOL_SCHEMA.resolve())
    if include_policy:
        if not gateway_arn:
            raise Blocked("Gateway ARN is required to render the Cedar policy")
        data["policyEngines"][0]["policies"][0]["statement"] = cedar_statement(
            identity["Arn"], gateway_arn)
    else:
        data["policyEngines"][0]["policies"] = []
    write_private_json(project / "agentcore.json", data)
    write_private_json(project / "aws-targets.json", [{
        "name": "default", "account": identity["Account"], "region": REGION}])
    return project


def validate_rendered_project(project, require_policy=True):
    data = read_json(Path(project) / "agentcore.json", "private AgentCore project")
    prohibited = ("runtimes", "harnesses", "memories", "knowledgeBases", "credentials")
    if any(data.get(key) for key in prohibited):
        raise Blocked("Runtime, Harness, Memory, knowledge base, or credentials are prohibited")
    if len(data.get("agentCoreGateways", [])) != 1 or len(data.get("policyEngines", [])) != 1:
        raise Blocked("expected exactly one Gateway and Policy Engine")
    gateway = data["agentCoreGateways"][0]
    if gateway.get("name") != GATEWAY_NAME or gateway.get("authorizerType") != "AWS_IAM":
        raise Blocked("Gateway name or IAM authorization configuration mismatch")
    if gateway.get("policyEngineConfiguration", {}).get("mode") != "ENFORCE":
        raise Blocked("Gateway Policy Engine mode is not ENFORCE")
    targets = gateway.get("targets", [])
    if (len(targets) != 1 or targets[0].get("name") != TARGET_NAME
            or targets[0].get("targetType") != "lambdaFunctionArn"):
        raise Blocked("expected exactly one named Lambda ARN target")
    policies = data["policyEngines"][0].get("policies", [])
    if require_policy and (len(policies) != 1 or policies[0].get("name") != POLICY_NAME):
        raise Blocked("expected exactly one named Cedar policy")
    if not require_policy and policies:
        raise Blocked("phase-one configuration unexpectedly contains a policy")
    if any(key in json.dumps(data).lower() for key in ('"model"', "modelprovider", "foundationmodel")):
        raise Blocked("model configuration is prohibited")
    return data


def deploy_native_resources(project, dry_run=False, phase="converge"):
    validate_rendered_project(project, require_policy=phase != "phase1")
    command = [str(CLI_BIN), "deploy", "--yes"]
    if dry_run:
        command.append("--dry-run")
    result = subprocess.run(command, cwd=Path(project).parent, env=scoped_aws_env(), text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1800)
    suffix = "dry-run" if dry_run else phase
    write_private_text(Path(project).parents[1] / f"deploy-{suffix}.log",
                       result.stdout + result.stderr)
    if result.returncode:
        raise Blocked(f"native AgentCore CLI deploy failed: {sanitize(result.stderr)}")
    harden_private_artifacts(project)
    return result.stdout


def native_resources(project, complete=True):
    state = read_json(Path(project) / ".cli/deployed-state.json", "native deployed state")
    try:
        resources = state["targets"]["default"]["resources"]
        gateways = resources["mcp"]["gateways"]
        gateway = gateways[GATEWAY_NAME]
    except (KeyError, TypeError) as error:
        raise Blocked("native deployed state is incomplete") from error
    if set(gateways) != {GATEWAY_NAME} or set(gateway.get("targets", {})) != {TARGET_NAME}:
        raise Blocked("native Gateway/target state is ambiguous")
    if set(resources.get("policyEngines", {})) != {ENGINE_NAME}:
        raise Blocked("native Policy Engine state is ambiguous")
    policies = resources.get("policies", {})
    expected_policy = f"{ENGINE_NAME}/{POLICY_NAME}"
    if complete and set(policies) != {expected_policy}:
        raise Blocked("native policy state is incomplete or ambiguous")
    if not complete and policies and set(policies) != {expected_policy}:
        raise Blocked("native phase-one policy state is ambiguous")
    if resources.get("stackName") != STACK_NAME:
        raise Blocked("native CloudFormation stack name mismatch")
    return state, resources, gateway


def converge_native(private_dir, lambda_arn, identity):
    project = ensure_private_scaffold(private_dir)
    if not (project / ".cli/deployed-state.json").exists():
        render_private_project(private_dir, lambda_arn, identity, include_policy=False)
        deploy_native_resources(project, phase="phase1")
    _, _, gateway = native_resources(project, complete=False)
    render_private_project(private_dir, lambda_arn, identity,
                           gateway_arn=gateway["gatewayArn"], include_policy=True)
    deploy_native_resources(project, phase="phase2")
    return project


def validate_gateway_url(value):
    parsed = urlparse(value)
    suffix = f".gateway.bedrock-agentcore.{REGION}.amazonaws.com"
    if (parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(suffix)
            or parsed.username or parsed.password or parsed.port not in {None, 443}
            or parsed.query or parsed.fragment):
        raise Blocked("deployed Gateway URL is not the approved AWS-managed endpoint")
    return value


def invoke_gateway(aws, gateway_url, environment):
    validate_case(TOOL_NAME, environment)
    gateway_url = validate_gateway_url(gateway_url)
    exported = subprocess.run(["aws", "--profile", PROFILE, "--region", REGION,
        "configure", "export-credentials"], env=aws.env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if exported.returncode:
        raise Blocked("credential provider failed")
    credentials = _json_object(exported.stdout, "credential provider response")
    if any(not credentials.get(key) for key in ("AccessKeyId", "SecretAccessKey")):
        raise Blocked("credential provider response is incomplete")
    request = aws.private_dir / f"proof-{environment}-request.json"
    response = aws.private_dir / f"proof-{environment}-response.txt"
    write_private_json(request, {"jsonrpc": "2.0", "id": environment,
        "method": "tools/call", "params": {"name": FULL_TOOL_NAME,
        "arguments": {"environment": environment}}})
    write_private_text(response, "")
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
        'write-out = "%{http_code}"', 'silent', 'show-error',
        'connect-timeout = 15', 'max-time = 60']
    if credentials.get("SessionToken"):
        lines.append(f'header = "X-Amz-Security-Token: {credentials["SessionToken"]}"')
    result = subprocess.run(["curl", "--config", "-"], input="\n".join(lines) + "\n",
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=75)
    credentials.clear()
    if result.returncode:
        raise Blocked(f"Gateway request failed: {sanitize(result.stderr)}")
    try:
        http_code = int(result.stdout[-3:])
    except ValueError as error:
        raise Blocked("Gateway response did not include an HTTP status") from error
    return http_code, response.read_text()


def metric_sum(aws, start, samples=None):
    end = datetime.now(timezone.utc) + timedelta(minutes=1)
    result = aws.call("cloudwatch", "get-metric-statistics", {
        "Namespace": "AWS/Lambda", "MetricName": "Invocations",
        "Dimensions": [{"Name": "FunctionName", "Value": FUNCTION_NAME}],
        "StartTime": start.isoformat(), "EndTime": end.isoformat(),
        "Period": 60, "Statistics": ["Sum"]})
    value = int(sum(point.get("Sum", 0) for point in result.get("Datapoints", [])))
    if samples is not None:
        samples.append({"at": datetime.now(timezone.utc).isoformat(), "sum": value})
    return value


def wait_for_metric(aws, start, expected, samples, timeout=300, stable_samples=1):
    deadline = time.monotonic() + timeout
    consecutive = 0
    while time.monotonic() < deadline:
        value = metric_sum(aws, start, samples)
        if value > expected:
            raise Blocked(f"Lambda invocation count exceeded expected value {expected}")
        consecutive = consecutive + 1 if value == expected else 0
        if consecutive >= stable_samples:
            return value
        time.sleep(10)
    raise Blocked(f"Lambda invocation metric did not stabilize at {expected}")


def quiet_metric_boundary(aws, samples):
    now = datetime.now(timezone.utc)
    boundary = now.replace(second=0, microsecond=0)
    if now.second >= 5:
        boundary += timedelta(minutes=1)
        time.sleep(max(0, (boundary - now).total_seconds() + 2))
    if metric_sum(aws, boundary, samples) != 0:
        raise Blocked("Lambda was not quiet at the start of the proof window")
    return boundary


def prove_deltas(aws, gateway):
    samples = []
    start = quiet_metric_boundary(aws, samples)
    dev_code, dev_body = invoke_gateway(aws, gateway["gatewayUrl"], "dev")
    parse_dev_response(dev_code, dev_body)
    after_dev = wait_for_metric(aws, start, 1, samples)
    prod_started = datetime.now(timezone.utc)
    prod_code, prod_body = invoke_gateway(aws, gateway["gatewayUrl"], "prod")
    parse_prod_response(prod_code, prod_body)
    minimum_observation = prod_started + timedelta(seconds=120)
    if datetime.now(timezone.utc) < minimum_observation:
        time.sleep((minimum_observation - datetime.now(timezone.utc)).total_seconds())
    after_prod = wait_for_metric(aws, start, 1, samples, stable_samples=2)
    validate_results(dev_code, dev_body, after_dev, prod_code, prod_body,
                     after_prod - after_dev)
    evidence = {"proof_started": start.isoformat(), "prod_started": prod_started.isoformat(),
        "proof_finished": datetime.now(timezone.utc).isoformat(),
        "dev_http_code": dev_code, "prod_http_code": prod_code,
        "dev_backend_delta": after_dev, "prod_backend_delta": after_prod - after_dev,
        "metric_samples": samples, "dev_response": json.loads(dev_body),
        "prod_response": json.loads(prod_body)}
    write_private_json(aws.private_dir / "proof-evidence.json", evidence)
    return evidence


def prove_fixed_action(aws, gateway, environment):
    """Invoke one fixed Gateway case and verify its bounded Lambda delta.

    This is deliberately read/invoke-only: it never creates, repairs, deploys,
    updates, or deletes any retained resource.
    """
    validate_case(TOOL_NAME, environment)
    samples = []
    start = quiet_metric_boundary(aws, samples)
    code, body = invoke_gateway(aws, gateway["gatewayUrl"], environment)
    if environment == "dev":
        parse_dev_response(code, body)
        delta = wait_for_metric(aws, start, 1, samples)
        if delta != 1:
            raise Blocked("dev backend delta is not exactly one")
    else:
        parse_prod_response(code, body)
        minimum_observation = datetime.now(timezone.utc) + timedelta(seconds=120)
        if datetime.now(timezone.utc) < minimum_observation:
            time.sleep((minimum_observation - datetime.now(timezone.utc)).total_seconds())
        delta = wait_for_metric(aws, start, 0, samples, stable_samples=2)
        if delta != 0:
            raise Blocked("prod backend delta is not exactly zero")
    evidence = {
        "environment": environment,
        "proof_started": start.isoformat(),
        "proof_finished": datetime.now(timezone.utc).isoformat(),
        "backend_delta": delta,
        "metric_samples": samples,
        "response": json.loads(body),
    }
    write_private_json(aws.private_dir / f"visual-{environment}-evidence.json", evidence)
    return evidence


def verify_retained_action(environment):
    """Verify one existing Gateway decision without any create or repair path.

    This is the narrow bridge used by the governed local demo action. It calls
    the retained Gateway once and validates its response, but intentionally
    does not wait for or interpret Lambda metrics; the full proof owns that
    execution-count evidence.
    """
    validate_case(TOOL_NAME, environment)
    aws, gateway, cost = retained_live_context()
    code, body = invoke_gateway(aws, gateway["gatewayUrl"], environment)
    if environment == "dev":
        parse_dev_response(code, body)
        decision = "ALLOW"
    else:
        parse_prod_response(code, body)
        decision = "DENY"
    result = {
        "environment": environment,
        "decision": decision,
        "retained_cost_gate": "PASS" if validate_cost(cost) < COST_LIMIT else "BLOCKED",
    }
    write_private_json(aws.private_dir / f"m1-gateway-{environment}.json", result)
    return result


def stack_resources(aws, stack_name):
    stack = aws.call("cloudformation", "describe-stacks", {"StackName": stack_name})
    items = aws.call("cloudformation", "describe-stack-resources", {"StackName": stack_name})
    stacks = stack.get("Stacks", [])
    if len(stacks) != 1 or stacks[0].get("StackStatus") not in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}:
        raise Blocked(f"retained stack {stack_name} is not complete")
    return stacks[0], items.get("StackResources", [])


def assert_resource_counts(items, expected, label):
    actual = Counter(item.get("ResourceType") for item in items)
    if actual != expected:
        raise Blocked(f"{label} resource counts differ from the reviewed topology")
    return actual


def one_physical_id(items, resource_type):
    matches = [item.get("PhysicalResourceId") for item in items
               if item.get("ResourceType") == resource_type]
    if len(matches) != 1 or not matches[0]:
        raise Blocked(f"retained {resource_type} inventory is ambiguous")
    return matches[0]


def retained_storage_bytes(aws, bootstrap_items, log_group):
    bucket = one_physical_id(bootstrap_items, "AWS::S3::Bucket")
    repository = one_physical_id(bootstrap_items, "AWS::ECR::Repository")
    s3_bytes = 0
    token = None
    while True:
        payload = {"Bucket": bucket}
        if token:
            payload["ContinuationToken"] = token
        page = aws.call("s3api", "list-objects-v2", payload)
        s3_bytes += sum(item.get("Size", 0) for item in page.get("Contents", []))
        token = page.get("NextContinuationToken") if page.get("IsTruncated") else None
        if not token:
            break
    ecr_bytes = 0
    token = None
    while True:
        payload = {"repositoryName": repository}
        if token:
            payload["nextToken"] = token
        page = aws.call("ecr", "describe-images", payload)
        ecr_bytes += sum(item.get("imageSizeInBytes", 0) for item in page.get("imageDetails", []))
        token = page.get("nextToken")
        if not token:
            break
    return {"s3_bytes": s3_bytes, "ecr_bytes": ecr_bytes,
            "log_bytes": int(log_group.get("storedBytes", 0))}


def retained_cost(kms_count, storage):
    gib = 1024 ** 3
    return validate_cost(
        kms_count * KMS_KEY_MONTHLY_USD
        + storage["s3_bytes"] / gib * S3_GB_MONTH_USD
        + storage["ecr_bytes"] / gib * ECR_GB_MONTH_USD
        + storage["log_bytes"] / gib * LOGS_GB_MONTH_USD
        + OTHER_IDLE_BUFFER_USD)


def validate_live_links(gateway, target, engine, policy, gateway_state,
                        lambda_arn, identity):
    if (gateway.get("status") != "READY" or gateway.get("authorizerType") != "AWS_IAM"
            or gateway.get("protocolType") != "MCP"):
        raise Blocked("live Gateway configuration is not READY/AWS_IAM/MCP")
    validate_gateway_url(gateway.get("gatewayUrl", ""))
    policy_configuration = gateway.get("policyEngineConfiguration", {})
    if (policy_configuration.get("arn") != engine["policyEngineArn"]
            or policy_configuration.get("mode") != "ENFORCE"):
        raise Blocked("live Gateway is not linked to the expected ENFORCE Policy Engine")
    if target.get("status") != "READY" or target.get("name") != TARGET_NAME:
        raise Blocked("live Gateway target is not the expected READY target")
    target_lambda = (target.get("targetConfiguration", {}).get("mcp", {})
                     .get("lambda", {}).get("lambdaArn"))
    if target.get("gatewayArn") != gateway_state["gatewayArn"] or target_lambda != lambda_arn:
        raise Blocked("live Gateway target linkage does not match the retained Lambda")
    if engine.get("status") != "ACTIVE" or policy.get("status") != "ACTIVE":
        raise Blocked("live Policy Engine or policy is not ACTIVE")
    if policy.get("enforcementMode") != "ACTIVE":
        raise Blocked("live policy enforcement mode is not ACTIVE")
    live_statement = policy.get("definition", {}).get("policy", {}).get("statement")
    expected_statement = cedar_statement(identity["Arn"], gateway_state["gatewayArn"])
    if live_statement != expected_statement:
        raise Blocked("live Cedar statement is not exactly the reviewed permit")


def inventory_and_cost(aws, project, lambda_arn, identity):
    _, resources, gateway_state = native_resources(project, complete=True)
    gateway_id = gateway_state["gatewayId"]
    target_id = gateway_state["targets"][TARGET_NAME]["targetId"]
    engine = resources["policyEngines"][ENGINE_NAME]
    policy = resources["policies"][f"{ENGINE_NAME}/{POLICY_NAME}"]
    gateway = aws.call("bedrock-agentcore-control", "get-gateway",
                       {"gatewayIdentifier": gateway_id})
    target = aws.call("bedrock-agentcore-control", "get-gateway-target",
                      {"gatewayIdentifier": gateway_id, "targetId": target_id})
    engine_live = aws.call("bedrock-agentcore-control", "get-policy-engine",
                           {"policyEngineId": engine["policyEngineId"]})
    policy_live = aws.call("bedrock-agentcore-control", "get-policy", {
        "policyEngineId": engine["policyEngineId"], "policyId": policy["policyId"]})
    validate_live_links(gateway, target, engine_live, policy_live, gateway_state,
                        lambda_arn, identity)
    function = aws.call("lambda", "get-function", {"FunctionName": FUNCTION_NAME})
    if function["Configuration"].get("FunctionArn") != lambda_arn:
        raise Blocked("Lambda ARN linkage drift")
    assert_tags(aws.call("lambda", "list-tags", {"Resource": lambda_arn}).get("Tags", {}),
                "Lambda function")
    role_tags_data = aws.call("iam", "list-role-tags", {"RoleName": ROLE_NAME}).get("Tags", [])
    assert_tags({item["Key"]: item["Value"] for item in role_tags_data}, "Lambda role")
    tag_arns = [gateway_state["gatewayArn"], engine["policyEngineArn"]]
    mappings = aws.call("resourcegroupstaggingapi", "get-resources",
                        {"ResourceARNList": tag_arns}).get("ResourceTagMappingList", [])
    by_arn = {item["ResourceARN"]: {tag["Key"]: tag["Value"] for tag in item.get("Tags", [])}
              for item in mappings}
    if set(by_arn) != set(tag_arns):
        raise Blocked("Gateway/Policy Engine tag inventory is incomplete")
    for tags in by_arn.values():
        assert_tags(tags, "native AgentCore resource")
    app_stack, app_items = stack_resources(aws, resources["stackName"])
    app_counts = assert_resource_counts(app_items, EXPECTED_APP_COUNTS, "application stack")
    bootstrap_stack, bootstrap_items = stack_resources(aws, "CDKToolkit")
    bootstrap_counts = assert_resource_counts(
        bootstrap_items, EXPECTED_BOOTSTRAP_COUNTS, "CDKToolkit")
    kms_count = bootstrap_counts["AWS::KMS::Key"]
    log_name = f"/aws/lambda/{FUNCTION_NAME}"
    logs = aws.call("logs", "describe-log-groups", {"logGroupNamePrefix": log_name, "limit": 10})
    exact_logs = [item for item in logs.get("logGroups", []) if item.get("logGroupName") == log_name]
    if len(exact_logs) != 1 or exact_logs[0].get("retentionInDays") != 1:
        raise Blocked("Lambda log group retention inventory is incomplete")
    log_arn = exact_logs[0]["arn"].removesuffix(":*")
    log_tags = aws.call("logs", "list-tags-for-resource", {"resourceArn": log_arn}).get("tags", {})
    assert_tags(log_tags, "Lambda log group")
    storage = retained_storage_bytes(aws, bootstrap_items, exact_logs[0])
    estimated_cost = retained_cost(kms_count, storage)
    summary = {"checked_at": datetime.now(timezone.utc).isoformat(),
        "application_stack_status": app_stack["StackStatus"],
        "application_resource_counts": dict(sorted(app_counts.items())),
        "bootstrap_stack_status": bootstrap_stack["StackStatus"],
        "bootstrap_resource_counts": dict(sorted(bootstrap_counts.items())),
        "kms_key_count": kms_count, "retained_storage_bytes": storage,
        "estimated_monthly_idle_cost_usd": estimated_cost,
        "gateway_status": gateway["status"], "target_status": target["status"],
        "policy_engine_status": engine_live["status"], "policy_status": policy_live["status"],
        "tag_gap": "Policy and GatewayTarget are stack-owned; current get APIs expose no tag map."}
    write_private_json(aws.private_dir / "retained-inventory.json", summary)
    return gateway_state, estimated_cost


def plan():
    print(f"PROFILE={PROFILE}")
    print(f"REGION={REGION}")
    print(f"TOOL={TOOL_NAME}")
    print(f"NATIVE_AGENTCORE_CLI={CLI_VERSION}")
    print(f"MCP_PROTOCOL_VERSION={MCP_VERSION}")
    print("PLAN=converge native stack; one dev ALLOW; one prod DENY; verify retention")
    print("PRECREATE_ESTIMATED_MONTHLY_IDLE_COST_USD=1.01")
    print("AWS_CALLS=0")


def live_context():
    private_dir = PRIVATE_ROOT / "cli"
    private_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    private_dir.chmod(0o700)
    aws = Aws(private_dir)
    identity = require_live_gates(aws)
    validate_cost(KMS_KEY_MONTHLY_USD + OTHER_IDLE_BUFFER_USD)
    return private_dir, aws, identity


def retained_live_context():
    """Read and verify the retained proof topology without any repair path."""
    private_dir, aws, identity = live_context()
    project = private_dir / "Issue31Policy" / "agentcore"
    if not project.is_dir():
        raise Blocked("retained native AgentCore project is unavailable")
    function = aws.call("lambda", "get-function", {"FunctionName": FUNCTION_NAME})
    lambda_arn = function.get("Configuration", {}).get("FunctionArn")
    if not lambda_arn:
        raise Blocked("retained synthetic Lambda ARN is unavailable")
    gateway, cost = inventory_and_cost(aws, project, lambda_arn, identity)
    return aws, gateway, cost


def prepare_live():
    private_dir, aws, identity = live_context()
    lambda_arn = ensure_lambda_prerequisite(aws, identity)
    project = render_private_project(private_dir, lambda_arn, identity,
        gateway_arn="arn:aws:bedrock-agentcore:ap-southeast-1:000000000000:gateway/DRYRUN0000")
    validate_rendered_project(project)
    deploy_native_resources(project, dry_run=True, phase="dry-run")
    print("PRIVATE_PROJECT_RENDER=PASS")
    print("NATIVE_CLI_DRY_RUN=PASS")
    print("GATEWAY_POLICY_RESULT=PREPARED")


def prove_live(converge=False):
    private_dir, aws, identity = live_context()
    lambda_arn = ensure_lambda_prerequisite(aws, identity)
    project = (converge_native(private_dir, lambda_arn, identity) if converge
               else private_dir / "Issue31Policy" / "agentcore")
    gateway, _ = inventory_and_cost(aws, project, lambda_arn, identity)
    evidence = prove_deltas(aws, gateway)
    _, cost = inventory_and_cost(aws, project, lambda_arn, identity)
    print("DEV_DECISION=ALLOW")
    print(f"DEV_BACKEND_CALLS={evidence['dev_backend_delta']}")
    print("PROD_DECISION=DENY")
    print(f"PROD_BACKEND_DELTA={evidence['prod_backend_delta']}")
    print("RESOURCE_RETENTION=PASS")
    print(f"ESTIMATED_MONTHLY_IDLE_COST_USD={cost:.2f}")
    print("GATEWAY_POLICY_RESULT=PASS")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-live", action="store_true",
                        help="create/verify Lambda and run the native CLI dry run")
    parser.add_argument("--prove-live", action="store_true",
                        help="prove the already-deployed retained stack")
    parser.add_argument("--approve-live", action="store_true",
                        help="converge the native stack and run the complete live proof")
    parser.add_argument("--verify-retained-action", choices=("dev", "prod"),
                        help="verify one retained Gateway decision without resource mutation")
    args = parser.parse_args()
    try:
        if sum((args.prepare_live, args.prove_live, args.approve_live,
                bool(args.verify_retained_action))) > 1:
            raise Blocked("select one live mode")
        if args.prepare_live:
            prepare_live()
        elif args.prove_live:
            prove_live()
        elif args.approve_live:
            prove_live(converge=True)
        elif args.verify_retained_action:
            result = verify_retained_action(args.verify_retained_action)
            print(f"GATEWAY_DECISION={result['decision']}")
            print(f"RETAINED_COST_GATE={result['retained_cost_gate']}")
            print("GATEWAY_ACTION_VERIFIED=PASS")
        else:
            plan()
    except (Blocked, subprocess.TimeoutExpired) as error:
        print(f"BLOCKED_REASON={sanitize(error)}", file=sys.stderr)
        print("GATEWAY_POLICY_RESULT=BLOCKED")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
