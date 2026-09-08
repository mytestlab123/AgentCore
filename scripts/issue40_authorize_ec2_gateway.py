#!/usr/bin/env python3
"""Grant the LibreChat EC2 role only InvokeGateway on the retained Gateway.

The Gateway's Cedar policy remains the second boundary: this IAM policy allows
transport to the retained Gateway but cannot permit the target tool itself.
The helper is idempotent, verifies the exact existing document before reuse,
and writes only hashed role evidence under the private Issue #31 directory.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import unquote

import gateway_policy_poc as poc


POLICY_NAME = "Issue40InvokeRetainedGateway"
ROLE_ENV = "AGENTCORE_LIBRECHAT_ROLE_NAME"


def require_role_name() -> str:
    value = os.environ.get(ROLE_ENV, "")
    if not value or "/" in value or value.startswith("-"):
        raise poc.Blocked("LibreChat EC2 role name is invalid")
    return value


def policy_document(gateway_arn: str) -> dict:
    return {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "InvokeRetainedIssue31Gateway",
            "Effect": "Allow",
            "Action": "bedrock-agentcore:InvokeGateway",
            "Resource": gateway_arn,
        }],
    }


def normalize_document(value: object) -> dict:
    if isinstance(value, str):
        value = unquote(value)
        value = json.loads(value)
    if not isinstance(value, dict):
        raise poc.Blocked("existing EC2 Gateway IAM policy document is malformed")
    return value


def authorize(role_name: str) -> dict:
    private_dir, aws, _ = poc.live_context()
    project = private_dir / "Issue31Policy" / "agentcore"
    _, _, gateway_state = poc.native_resources(project, complete=True)
    expected = policy_document(gateway_state["gatewayArn"])
    existing = aws.optional("iam", "get-role-policy", {
        "RoleName": role_name, "PolicyName": POLICY_NAME})
    if existing is None:
        aws.call("iam", "put-role-policy", {
            "RoleName": role_name,
            "PolicyName": POLICY_NAME,
            "PolicyDocument": json.dumps(expected, separators=(",", ":")),
        })
        created = True
    else:
        if poc.canonical(normalize_document(existing.get("PolicyDocument"))) != poc.canonical(expected):
            raise poc.Blocked("existing EC2 Gateway IAM policy differs from the approved statement")
        created = False
    verified = aws.call("iam", "get-role-policy", {
        "RoleName": role_name, "PolicyName": POLICY_NAME})
    if poc.canonical(normalize_document(verified.get("PolicyDocument"))) != poc.canonical(expected):
        raise poc.Blocked("EC2 Gateway IAM policy was not retained exactly")
    result = {
        "policy_name": POLICY_NAME,
        "created": created,
        "role_sha256": poc.digest(role_name),
        "action": "bedrock-agentcore:InvokeGateway",
        "resource": "retained-gateway",
    }
    poc.write_private_json(private_dir / "issue40-ec2-gateway-iam-policy.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approve-ec2-gateway-invoke", action="store_true",
                        help="apply the reviewed one-role / one-Gateway IAM policy")
    args = parser.parse_args(argv)
    if not args.approve_ec2_gateway_invoke:
        print("PLAN=add one EC2 inline IAM policy for InvokeGateway on the retained Gateway")
        print("AWS_CALLS=0")
        return 0
    try:
        result = authorize(require_role_name())
    except (poc.Blocked, KeyError, json.JSONDecodeError) as error:
        print(f"BLOCKED={poc.sanitize(error)}")
        return 2
    print("LIBRECHAT_EC2_GATEWAY_IAM=ACTIVE")
    print(f"LIBRECHAT_EC2_GATEWAY_IAM_CREATED={'true' if result['created'] else 'false'}")
    print("IAM_ACTION=InvokeGateway-retained-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
