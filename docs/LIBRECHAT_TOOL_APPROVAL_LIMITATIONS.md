# LibreChat tool-approval limitations

## Purpose

This note records the boundary of the native LibreChat MCP approval mechanism
used by the AgentCore governance demo. It prevents a model response from being
mistaken for a policy-enforcement result.

## Where enforcement begins

```text
user request -> model chooses a tool call -> LibreChat policy -> MCP tool
```

`toolApproval` evaluates a tool call only after the model emits one. It does
not inspect every raw user message, classify intent before the model runs, or
force the model to invoke a tool.

## Native policy outcomes

| Policy | Native result | User interface |
| --- | --- | --- |
| `allow` | Tool runs immediately. | No approval buttons. |
| `ask` | Tool pauses before execution. | Fixed LibreChat **Approve**, **Reject**, **Edit**, **Respond**, and **Submit** controls. Reject means no tool call. |
| `deny` | An emitted tool call is blocked before the MCP implementation runs. | No approval buttons: there is no decision for the user to make. |

The approval buttons are for `ask`, not for `deny`. A user clicking **Reject**
is declining an `ask` request; it is not the same as a policy `deny`.

## Why `Delete web-01` showed only text

In the live demo, GPT-5.6 Luna refused the deletion request in natural
language before emitting `delete_demo_asset`. LibreChat therefore had no tool
call to evaluate and could not show a native DENY event. This is a safe model
refusal, but it is not visual proof that LibreChat intercepted a tool call.

The configured policy still resolves `delete_demo_asset` to `deny`, and the
MCP state confirms `delete_calls=0`. Do not label the text refusal as a live
native DENY UI result.

## Harder controls require another enforcement layer

If the product needs an immediate, visible denial for a raw user request,
native tool approval alone is insufficient. A future, separately approved
design must add a deterministic request/intent policy gateway before the
model. That is a new authorization and user-workflow architecture, not a
configuration tweak.

For defence in depth, preserve these layers:

1. pre-model request policy, if explicitly designed and approved;
2. LibreChat native tool policy for emitted calls and human approval;
3. MCP-server authorization and least-privilege IAM so a prohibited real
   mutation remains impossible even if an upstream layer is bypassed.

The current POC proves the native `ask` UI for remediation. It does not claim
a visible native DENY UI for a deletion request that the model refused before
tool emission.
