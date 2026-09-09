#!/usr/bin/env python3
"""Bind both retained Gateway permits to the exact approved remediation tuple.

This approved migration may update only the two known legacy environment-only
policies when they exactly match their prior reviewed statements. It never
changes the Gateway, target, Lambda, IAM role, or policy inventory. For a
retained LibreChat policy, it can recover the already-authorized stable
principal from that private policy definition; it never lists or guesses a
role. All result details stay in the existing private evidence directory.
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
PRINCIPAL_IN_STATEMENT = re.compile(
    r'principal == AgentCore::IamEntity::"(arn:[^"\\]+)"')


def librechat_statement(principal: str, gateway_arn: str) -> str:
    if not STABLE_ASSUMED_ROLE.fullmatch(principal):
        raise poc.Blocked("LibreChat principal must be a stable assumed-role ARN")
    return (f'permit(principal == AgentCore::IamEntity::"{principal}", '
            f'action == AgentCore::Action::"{poc.FULL_TOOL_NAME}", '
            f'resource == AgentCore::Gateway::"{gateway_arn}") '
            'when { context.input.environment == "dev" && '
            'context.input.action == "remove_unrestricted_ssh" && '
            'context.input.target == "demo-security-group" };')


def legacy_librechat_statement(principal: str, gateway_arn: str) -> str:
    if not STABLE_ASSUMED_ROLE.fullmatch(principal):
        raise poc.Blocked("LibreChat principal must be a stable assumed-role ARN")
    return (f'permit(principal == AgentCore::IamEntity::"{principal}", '
            f'action == AgentCore::Action::"{poc.FULL_TOOL_NAME}", '
            f'resource == AgentCore::Gateway::"{gateway_arn}") '
            'when { context.input.environment == "dev" };')


def require_principal() -> str:
    return os.environ.get(PRINCIPAL_ENV, "")


def principal_from_statement(statement: object) -> str:
    """Extract only the one stable existing LibreChat principal, or fail closed."""
    if not isinstance(statement, str):
        raise poc.Blocked("existing LibreChat Gateway policy statement is malformed")
    match = PRINCIPAL_IN_STATEMENT.search(statement)
    if not match or not STABLE_ASSUMED_ROLE.fullmatch(match.group(1)):
        raise poc.Blocked("existing LibreChat Gateway policy has no stable role principal")
    return match.group(1)


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
    """Prove the retained human permit is bound to the exact remediation tuple."""
    policy = aws.call("bedrock-agentcore-control", "get-policy", {
        "policyEngineId": engine_id, "policyId": policy_id})
    expected = poc.cedar_statement(human_caller_arn, gateway_arn)
    actual = policy.get("definition", {}).get("policy", {}).get("statement")
    if (policy.get("name") != poc.POLICY_NAME or policy.get("status") != "ACTIVE"
            or policy.get("enforcementMode") != "ACTIVE" or actual != expected):
        raise poc.Blocked("retained human Gateway policy differs from its exact approved statement")


def migrate_known_policy(
    aws: poc.Aws,
    *,
    engine_id: str,
    policy_id: str,
    expected: str,
    legacy: str,
    label: str,
) -> tuple[dict, bool]:
    """Update only a known old policy, otherwise fail closed on drift."""
    current = wait_active(aws, engine_id, policy_id)
    actual = current.get("definition", {}).get("policy", {}).get("statement")
    if current.get("enforcementMode") == "ACTIVE" and actual == expected:
        return current, False
    if current.get("enforcementMode") != "ACTIVE" or actual != legacy:
        raise poc.Blocked(f"{label} Gateway policy differs from exact or known legacy statement")
    aws.call("bedrock-agentcore-control", "update-policy", {
        "policyEngineId": engine_id,
        "policyId": policy_id,
        "definition": {"policy": {"statement": expected}},
        "validationMode": "FAIL_ON_ANY_FINDINGS",
        "enforcementMode": "ACTIVE",
    })
    updated = wait_active(aws, engine_id, policy_id)
    if (updated.get("enforcementMode") != "ACTIVE"
            or updated.get("definition", {}).get("policy", {}).get("statement") != expected):
        raise poc.Blocked(f"{label} Gateway policy did not converge to the exact tuple")
    return updated, True


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
    _original, original_migrated = migrate_known_policy(
        aws,
        engine_id=engine_id,
        policy_id=original_policy_id,
        expected=poc.cedar_statement(identity["Arn"], gateway_arn),
        legacy=poc.legacy_cedar_statement(identity["Arn"], gateway_arn),
        label="retained human",
    )
    policies = aws.call("bedrock-agentcore-control", "list-policies", {
        "policyEngineId": engine_id}).get("policies", [])
    matches = [item for item in policies if item.get("name") == POLICY_NAME]
    if len(matches) > 1:
        raise poc.Blocked("LibreChat Gateway policy name is ambiguous")
    assert_policy_names(policies, allow_new=bool(matches))
    existing = None
    if matches:
        existing = wait_active(aws, engine_id, matches[0]["policyId"])
        if not principal:
            principal = principal_from_statement(
                existing.get("definition", {}).get("policy", {}).get("statement"))
    if not principal:
        raise poc.Blocked("configured LibreChat principal is required when creating the policy")
    expected = librechat_statement(principal, gateway_arn)
    if matches:
        policy, migrated = migrate_known_policy(
            aws,
            engine_id=engine_id,
            policy_id=matches[0]["policyId"],
            expected=expected,
            legacy=legacy_librechat_statement(principal, gateway_arn),
            label="LibreChat",
        )
        created = False
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
        migrated = False
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
        "original_policy_exact_tuple_migrated": original_migrated,
        "librechat_policy_exact_tuple_migrated": migrated,
    }
    poc.write_private_json(private_dir / "issue40-librechat-gateway-policy.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approve-librechat-role", action="store_true",
                        help="apply the reviewed single-policy authorization change")
    args = parser.parse_args(argv)
    if not args.approve_librechat_role:
        print("PLAN=bind the two known retained permits to the exact dev/remediation/demo-target tuple")
        print("AWS_CALLS=0")
        return 0
    try:
        result = authorize(require_principal())
    except (poc.Blocked, KeyError) as error:
        print(f"BLOCKED={poc.sanitize(error)}")
        return 2
    print("LIBRECHAT_GATEWAY_POLICY=ACTIVE")
    print(f"LIBRECHAT_GATEWAY_POLICY_CREATED={'true' if result['created'] else 'false'}")
    print("ORIGINAL_HUMAN_POLICY=exact-tuple")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
