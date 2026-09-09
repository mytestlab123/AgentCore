# Issue #48 — Exact action/target-bound remediation policy

Purpose: complete M9–M13 as one cohesive governance milestone on top of merged M8.

## Target outcome

`real SG finding -> native ASK -> exact Gateway action/target policy -> exact AWS action or DENY -> provider verification -> compact audit`

## Milestone checkpoints

- **M9 — policy context:** fixed server-owned `environment=dev`, `action=remove_unrestricted_ssh`, `target=demo-security-group` reach the retained Gateway.
- **M10 — exact Cedar permit:** ALLOW requires the complete expected action/target/environment tuple, not `dev` alone.
- **M11 — hard DENY matrix:** wrong action, wrong target, and synthetic `prod` all DENY with zero AWS revoke calls.
- **M12 — UI/audit truth:** LibreChat approval copy and compact audit show the same bounded action/target decision as Gateway Policy.
- **M13 — COMPLIANT no-op:** if unrestricted SSH is already absent, return no-remediation-required and perform no AWS mutation.

## Current provider state

The dedicated demo Security Group was left **COMPLIANT** after the final M8 native UI proof. Do not silently recreate the bad rule. The operator-only direct AWS CLI reset remains the only intentional way to restore the NON_COMPLIANT demo state.

## KISS

Reuse M8. No second AWS service, generic SG tool, caller-selected target/action, new frontend, browser framework, RAG, FAST, or observability system. Simple AWS/IAM/setup work uses direct AWS CLI first; runtime Python is only for existing application logic and focused tests.

See Issue #48 for the full acceptance contract.