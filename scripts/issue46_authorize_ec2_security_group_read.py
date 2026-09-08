#!/usr/bin/env python3
"""Grant the LibreChat EC2 role its required read-only EC2 List action.

`ec2:DescribeSecurityGroups` does not support a resource type in the AWS
service authorization reference, so this exact List action requires
``Resource: "*"``. The governed MCP server separately hard-binds its single
runtime query to the configured dedicated demo Security Group ID.
"""

from __future__ import annotations

import argparse
import json
import os
from urllib.parse import unquote

import gateway_policy_poc as poc


POLICY_NAME = "Issue46ReadSecurityGroups"
ROLE_ENV = "AGENTCORE_LIBRECHAT_ROLE_NAME"


def require_role_name() -> str:
    value = os.environ.get(ROLE_ENV, "")
    if not value or "/" in value or value.startswith("-"):
        raise poc.Blocked("LibreChat EC2 role name is invalid")
    return value


def policy_document() -> dict:
    return {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "ReadIssue46SecurityGroupCompliance",
            "Effect": "Allow",
            "Action": "ec2:DescribeSecurityGroups",
            "Resource": "*",
        }],
    }


def normalize_document(value: object) -> dict:
    if isinstance(value, str):
        value = json.loads(unquote(value))
    if not isinstance(value, dict):
        raise poc.Blocked("existing EC2 Security Group IAM policy document is malformed")
    return value


def authorize(role_name: str) -> dict:
    private_dir, aws, _ = poc.live_context()
    expected = policy_document()
    existing = aws.optional("iam", "get-role-policy", {
        "RoleName": role_name, "PolicyName": POLICY_NAME,
    })
    if existing is None:
        aws.call("iam", "put-role-policy", {
            "RoleName": role_name,
            "PolicyName": POLICY_NAME,
            "PolicyDocument": json.dumps(expected, separators=(",", ":")),
        })
        created = True
    else:
        if poc.canonical(normalize_document(existing.get("PolicyDocument"))) != poc.canonical(expected):
            raise poc.Blocked("existing EC2 Security Group IAM policy differs from the approved statement")
        created = False
    verified = aws.call("iam", "get-role-policy", {
        "RoleName": role_name, "PolicyName": POLICY_NAME,
    })
    if poc.canonical(normalize_document(verified.get("PolicyDocument"))) != poc.canonical(expected):
        raise poc.Blocked("EC2 Security Group IAM policy was not retained exactly")
    result = {
        "policy_name": POLICY_NAME,
        "created": created,
        "role_sha256": poc.digest(role_name),
        "action": "ec2:DescribeSecurityGroups",
        "resource": "* (required EC2 List action)",
    }
    poc.write_private_json(private_dir / "issue46-ec2-security-group-iam-policy.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--approve-ec2-security-group-read", action="store_true",
        help="apply the reviewed one-role / one-read-only-action IAM policy",
    )
    args = parser.parse_args(argv)
    if not args.approve_ec2_security_group_read:
        print("PLAN=add one EC2 inline IAM policy for DescribeSecurityGroups")
        print("AWS_CALLS=0")
        return 0
    try:
        result = authorize(require_role_name())
    except (poc.Blocked, KeyError, json.JSONDecodeError) as error:
        print(f"BLOCKED={poc.sanitize(error)}")
        return 2
    print("LIBRECHAT_EC2_SECURITY_GROUP_IAM=ACTIVE")
    print(f"LIBRECHAT_EC2_SECURITY_GROUP_IAM_CREATED={'true' if result['created'] else 'false'}")
    print("IAM_ACTION=DescribeSecurityGroups-read-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
