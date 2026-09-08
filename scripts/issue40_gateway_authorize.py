#!/usr/bin/env python3
"""Authorize only the LibreChat EC2 role for the retained Gateway dev tool.

This approved migration adds one independently revocable Cedar permit policy.
It never changes the original human-principal policy, Gateway, target, Lambda,
or IAM role. The exact principal stays in a private environment variable and
all result details stay in the existing private evidence directory.
"""

from __future__ import annotations

import argparse
import os
import re
import time

import gateway_policy_poc as poc


POLICY_NAME = "Issue40LibreChatDevPermit"
PRINCIPAL_ENV = "AGENTCORE_LIBRECHAT_PRINCIPAL_ARN"
STABLE_ASSUMED_ROLE = re.compile(r"arn:[^:]+:sts::\d{12}:assumed-role/[^/]+$")


def librechat_statement(principal: str, gateway_arn: str) -> str:
    if not STABLE_ASSUMED_ROLE.fullmatch(principal):
        raise poc.Blocked("LibreChat principal must be a stable assumed-role ARN")
    return (f'permit(principal == AgentCore::IamEntity::"{principal}", '
            f'action == AgentCore::Action::"{poc.FULL_TOOL_NAME}", '
            f'resource == AgentCore::Gateway::"{gateway_arn}") '
            'when { context.input.environment == "dev" };')


def require_principal() -> str:
    return os.environ.get(PRINCIPAL_ENV, "")


def wait_active(aws: poc.Aws, engine_id: str, policy_id: str) -> dict:
    for _ in range(24):
        policy = aws.call("bedrock-agentcore-control", "get-policy", {
            "policyEngineId": engine_id, "policyId": policy_id})
        if policy.get("status") == "ACTIVE":
            return policy
        if policy.get("status") in {"CREATE_FAILED", "UPDATE_FAILED", "DELETING", "DELETE_FAILED"}:
            raise poc.Blocked("LibreChat Gateway policy did not become active")
        time.sleep(5)
    raise poc.Blocked("timed out waiting for LibreChat Gateway policy")


def assert_original_human_policy(
    aws: poc.Aws,
    *,
    engine_id: str,
    policy_id: str,
    gateway_arn: str,
    human_caller_arn: str,
) -> None:
    """Prove the retained human-only permit was not changed by this migration."""
    policy = aws.call("bedrock-agentcore-control", "get-policy", {
        "policyEngineId": engine_id, "policyId": policy_id})
    expected = poc.cedar_statement(human_caller_arn, gateway_arn)
    actual = policy.get("definition", {}).get("policy", {}).get("statement")
    if (policy.get("name") != poc.POLICY_NAME or policy.get("status") != "ACTIVE"
            or policy.get("enforcementMode") != "ACTIVE" or actual != expected):
        raise poc.Blocked("retained human Gateway policy differs from its approved statement")


def assert_policy_names(policies: list[dict], *, allow_new: bool) -> None:
    names = {item.get("name") for item in policies}
    expected = {poc.POLICY_NAME}
    if allow_new:
        expected.add(POLICY_NAME)
    if names != expected:
        raise poc.Blocked("Gateway policy inventory is not the approved retained policy set")


def authorize(principal: str) -> dict:
    private_dir, aws, identity = poc.live_context()
    project = private_dir / "Issue31Policy" / "agentcore"
    _, resources, gateway_state = poc.native_resources(project, complete=True)
    engine_id = resources["policyEngines"][poc.ENGINE_NAME]["policyEngineId"]
    gateway_arn = gateway_state["gatewayArn"]
    original_policy_id = resources["policies"][f"{poc.ENGINE_NAME}/{poc.POLICY_NAME}"]["policyId"]
    assert_original_human_policy(
        aws, engine_id=engine_id, policy_id=original_policy_id,
        gateway_arn=gateway_arn, human_caller_arn=identity["Arn"])
    expected = librechat_statement(principal, gateway_arn)
    policies = aws.call("bedrock-agentcore-control", "list-policies", {
        "policyEngineId": engine_id}).get("policies", [])
    matches = [item for item in policies if item.get("name") == POLICY_NAME]
    if len(matches) > 1:
        raise poc.Blocked("LibreChat Gateway policy name is ambiguous")
    assert_policy_names(policies, allow_new=bool(matches))
    if matches:
        existing = wait_active(aws, engine_id, matches[0]["policyId"])
        actual = existing.get("definition", {}).get("policy", {}).get("statement")
        if (existing.get("enforcementMode") != "ACTIVE" or actual != expected):
            raise poc.Blocked("existing LibreChat Gateway policy differs from the approved statement")
        created = False
        policy = existing
    else:
        policy = aws.call("bedrock-agentcore-control", "create-policy", {
            "name": POLICY_NAME,
            "description": "Issue 40: permit the LibreChat EC2 role to call the retained demo tool only in dev.",
            "policyEngineId": engine_id,
            "definition": {"policy": {"statement": expected}},
            "validationMode": "FAIL_ON_ANY_FINDINGS",
            "enforcementMode": "ACTIVE",
        })
        policy = wait_active(aws, engine_id, policy["policyId"])
        created = True
    final_policies = aws.call("bedrock-agentcore-control", "list-policies", {
        "policyEngineId": engine_id}).get("policies", [])
    assert_policy_names(final_policies, allow_new=True)
    assert_original_human_policy(
        aws, engine_id=engine_id, policy_id=original_policy_id,
        gateway_arn=gateway_arn, human_caller_arn=identity["Arn"])
    result = {
        "policy_name": POLICY_NAME,
        "created": created,
        "status": policy["status"],
        "enforcement_mode": policy["enforcementMode"],
        "gateway_url": aws.call("bedrock-agentcore-control", "get-gateway", {
            "gatewayIdentifier": gateway_state["gatewayId"]})["gatewayUrl"],
        "principal_sha256": poc.digest(principal),
        "original_policy_preserved": True,
    }
    poc.write_private_json(private_dir / "issue40-librechat-gateway-policy.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approve-librechat-role", action="store_true",
                        help="apply the reviewed single-policy authorization change")
    args = parser.parse_args(argv)
    if not args.approve_librechat_role:
        print("PLAN=add one named dev-only Cedar permit for the configured LibreChat role")
        print("AWS_CALLS=0")
        return 0
    try:
        result = authorize(require_principal())
    except (poc.Blocked, KeyError) as error:
        print(f"BLOCKED={poc.sanitize(error)}")
        return 2
    print("LIBRECHAT_GATEWAY_POLICY=ACTIVE")
    print(f"LIBRECHAT_GATEWAY_POLICY_CREATED={'true' if result['created'] else 'false'}")
    print("ORIGINAL_HUMAN_POLICY=preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
