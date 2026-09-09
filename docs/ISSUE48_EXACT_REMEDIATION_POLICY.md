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

The M13 application behavior remains fail-safe: if unrestricted SSH is absent,
an approved request returns `NO_REMEDIATION_REQUIRED` and performs no AWS
mutation. After the M9–M13 proof, the operator intentionally re-armed the
dedicated, unattached demo Security Group with its one TCP/22-from-`0.0.0.0/0`
rule so the next demonstration starts `NON_COMPLIANT` and can exercise the
real exact revoke. This reset is operator-only direct AWS CLI work; it is never
performed by LibreChat, the MCP server, or an automatic cleanup job.

## KISS

Reuse M8. No second AWS service, generic SG tool, caller-selected target/action, new frontend, browser framework, RAG, FAST, or observability system. Simple AWS/IAM/setup work uses direct AWS CLI first; runtime Python is only for existing application logic and focused tests.

See Issue #48 for the full acceptance contract.
