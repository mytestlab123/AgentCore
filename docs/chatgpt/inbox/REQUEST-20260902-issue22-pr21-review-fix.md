# STRICT EXECUTION CONTRACT — Issue #22 post-merge PR #21 review fixes

Status: IMPLEMENTATION HANDOFF
Owner of architecture/acceptance: ChatGPT
Implementation worker: Codex
GitHub Issue: #22
Target branch: `fix/issue-22-pr21-nova-guide`

## Objective

Correct exactly two post-merge documentation defects left in `docs/NOVA_FAMILY_GUIDE.md` after PR #21 merged before its Codex review completed.

This is documentation-only maintenance. Do not broaden scope.

## Repository truth to reuse

The existing verified implementation in `scripts/bedrock-api-key-poc.sh` is authoritative for Bedrock long-term API-key creation and secret handling.

It uses:

```bash
umask 077

aws iam create-service-specific-credential \
  --profile "$profile" \
  --user-name "$user_name" \
  --service-name bedrock.amazonaws.com \
  --credential-age-days "$credential_age_days" \
  >"$credential_file"
```

The guide must align with that pattern rather than inventing another AWS CLI operation.

## MUST fix

1. Replace the nonexistent `aws bedrock create-long-term-api-key` example with the IAM service-specific credential command used by the repository.
2. Remove the predictable `/tmp/nova-2-pro-key.json` secret path.
3. Demonstrate restrictive file creation with `umask 077` or an equally explicit mode-600 mechanism.
4. Use a private per-user directory/file path in the example.
5. State that the one-time credential response contains secret material and must not be committed or logged.
6. Include explicit cleanup/removal guidance for the local secret file when no longer needed.
7. Preserve the existing entitlement-first ordering: do not create a key until model/account availability is confirmed.
8. Run `./scripts/check.sh` with no AWS calls and record the result in the PR.

## MUST NOT

- Do not change `scripts/bedrock-api-key-poc.sh` unless a genuine contradiction is found; if so, STOP and report a blocker.
- Do not make AWS calls.
- Do not create, rotate, or reveal a real credential.
- Do not add account IDs, ARNs, keys, endpoints, or raw AWS output.
- Do not change unrelated Nova guidance.
- Do not revisit AgentCore Harness, LibreChat, LiteLLM, Gateway, MCP, or other milestones.
- Do not create another issue/branch/PR for this fix.

## Expected diff

Prefer one changed documentation file plus this contract file:

```text
docs/NOVA_FAMILY_GUIDE.md
docs/chatgpt/inbox/REQUEST-20260902-issue22-pr21-review-fix.md
```

If more files are necessary, explain why in the existing Draft PR before changing them.

## Acceptance criteria

- [ ] No `aws bedrock create-long-term-api-key` command remains in the actionable guide path.
- [ ] The guide uses `aws iam create-service-specific-credential --service-name bedrock.amazonaws.com`.
- [ ] No credential example writes to predictable default-permission `/tmp`.
- [ ] Restrictive local permissions are explicit.
- [ ] Secret-file cleanup is explicit.
- [ ] No real secret/private AWS identifier is committed.
- [ ] `./scripts/check.sh` passes without AWS calls.
- [ ] Diff remains documentation-only apart from this contract.

## Codex protocol

Codex must continue only the existing Draft PR created for Issue #22.

If the required correction conflicts with current AWS CLI behavior or repository truth, do not invent an alternative. Report:

```text
BLOCKER
Expected contract: ...
Repository/AWS reality: ...
Why blocked: ...
Smallest options: ...
Architecture changed: NO
Alternative implementation started: NO
Decision required: ChatGPT / human
```

Do not mark ready, merge, or close Issue #22 until ChatGPT/human reviews the final diff.
