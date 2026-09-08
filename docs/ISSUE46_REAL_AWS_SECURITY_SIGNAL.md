# Issue #46 — Real Security Group SSH compliance demo

Purpose: make the existing Security Copilot demo use one real, immediate AWS security signal without depending on Inspector, Security Hub, or a slow scan pipeline.

## Chosen control

Use one dedicated demo-only Security Group with:

- TCP port `22`;
- source `0.0.0.0/0`;
- no attached EC2 instance or ENI required for this POC.

The exact claim is **unrestricted SSH ingress / non-compliant Security Group rule**. Do not call it an internet-exposed server unless routing/public-IP evidence also proves that.

AWS Config's managed `restricted-ssh` rule uses the same logic: port 22 open from `0.0.0.0/0` or `::/0` is NON_COMPLIANT. AWS Config is optional corroborating evidence only; it is not required for this milestone.

## Working plan

1. Pull current `main` and read `AGENTS.md` first.
2. Use `AWS_PROFILE=amit` by default in the approved Region. `dev` only when specifically needed. Never use an AWS prod profile/account/environment; synthetic `prod` remains deny-test data only.
3. Kiro may do read-only discovery only: identify a suitable VPC, whether the fixed demo SG already exists, and whether AWS Config + `restricted-ssh` are already enabled. Do not enable/configure Inspector, Security Hub, or AWS Config.
4. Use `ec2:DescribeSecurityGroups` as the fast primary truth and evaluate only unrestricted SSH (`TCP/22` from `0.0.0.0/0` or `::/0`).
5. Show one small sanitized result in LibreChat: rule, source, and `NON_COMPLIANT`/`COMPLIANT`; do not expose account IDs, ARNs, VPC IDs, private endpoints, credentials, or raw AWS payloads.
6. Preserve native LibreChat ASK / Approve / Reject and the retained AgentCore Gateway Policy. Reject must not invoke MCP; a Gateway `DENY` must not call AWS.
7. After native Approve and Gateway `ALLOW`, revoke only the exact TCP/22 ingress permission from `0.0.0.0/0` on the fixed dedicated demo SG, then immediately re-read it. Report `COMPLIANT` only when unrestricted TCP/22 is absent.
8. Keep one operator-only direct AWS CLI reset command that restores only the same demo rule after proof. Do not add a reset button, generic mutation path, or an AWS security scanner.

## Excluded

- Inspector / Inspector2;
- Security Hub setup;
- automatic AWS Config setup;
- EC2 instance creation just for this control;
- WAF/ACM/RAG/FAST/new frontend;
- generic AWS security scanning.

## Acceptance

- one real Security Group result is visible in LibreChat;
- `TCP/22 -> 0.0.0.0/0` is shown as NON_COMPLIANT when present;
- focused tests, `./scripts/check.sh`, and `git diff --check` pass;
- one live sanitized `DescribeSecurityGroups` proof uses profile `amit`;
- one thin authenticated browser proof shows the real result;
- Reject = no AWS change; Gateway `DENY` = no AWS change; Approve = remove only the fixed TCP/22 rule; final read = COMPLIANT; operator reset restores only the same rule.

## Operator-only reset

Run this only after a successful demonstration has verified `COMPLIANT`, and
only with the private ID of the fixed, unattached Issue #46 demo Group. It
restores the one intentional non-compliant rule; it does not create, attach,
delete, or modify any other resource.

```bash
DEMO_SG_ID='sg-<private-fixed-demo-group-id>'
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 \
  aws ec2 authorize-security-group-ingress \
    --group-id "$DEMO_SG_ID" \
    --ip-permissions '[{"IpProtocol":"tcp","FromPort":22,"ToPort":22,"IpRanges":[{"CidrIp":"0.0.0.0/0"}]}]' \
    --no-cli-pager
```

The command should return only after the Group is again `NON_COMPLIANT` for
unrestricted SSH. Re-run the read-only `check_security_finding` tool to show
the restored state; do not use the reset command from LibreChat.
