# Codex AWS MCP: direct OAuth resolution versus SigV4 proxy repair

**Status:** confirmed working by the operator

**Observed environment:** Codex CLI v0.153.4 on WSL, AWS MCP endpoint in
`us-east-1`, and Cloudflare WARP. This document contains no credentials, token
values, AWS account IDs, local configuration paths, or raw logs.

## Short answer

The observed working outcome was **not a repair of the local SigV4 verifier or
proxy**. It was a supported switch from the local stdio SigV4 proxy path to the
managed AWS MCP Server OAuth path:

```text
https://aws-mcp.us-east-1.api.aws/mcp?oauth=initialize
```

The local proxy path was:

```text
Codex daemon -> stdio -> mcp-proxy-for-aws -> SigV4-signed HTTPS -> AWS MCP
```

The direct OAuth path is:

```text
Codex -> HTTPS AWS MCP Server -> AWS Sign-in OAuth -> AWS MCP
```

By using the direct OAuth server, Codex no longer depends on the local
`mcp-proxy-for-aws` process for request signing or its inherited CA settings.

## Problem pattern

The earlier symptom pattern was:

1. A direct local proxy invocation could work behind WARP only when its process
   used the system CA bundle through `SSL_CERT_FILE`.
2. Codex `/mcp` still showed the same stdio server as failed with zero tools
   after a daemon restart.
3. The operator then configured the official direct OAuth endpoint and reported
   that AWS MCP in Codex works.

The likely explanation is process-bound environment/TLS behavior: the shell
that ran the direct proxy had the CA override, while the separately started
Codex daemon may not have inherited it. That is a plausible diagnosis only. It
was **not** proven by inspecting daemon logs, local configuration, proxy source,
or a TLS trace.

## What changed conceptually

| Concern | Local SigV4 proxy | Direct AWS OAuth server |
|---|---|---|
| MCP transport | Local stdio child process | Remote HTTPS MCP server |
| AWS authentication | Proxy signs requests with local AWS credentials (SigV4) | AWS Sign-in issues OAuth bearer tokens to Codex |
| Local CA dependency | Yes; proxy process must trust the WARP/TLS chain | No local proxy process; Codex and browser still need normal HTTPS connectivity/trust |
| Tool discovery failure | Can result from proxy launch, environment, CA, credential, or stdio issues | Avoids the proxy-specific failure class |
| Multi-profile workflows | Supported by named AWS profiles / SigV4 proxy design | Not supported in one OAuth session |
| Proxy-enforced read-only tool hiding | Available use case for SigV4 approach | Not the same control model |

## Correct direct OAuth endpoint for Codex

AWS documents Codex CLI/Desktop with:

```text
https://aws-mcp.us-east-1.api.aws/mcp?oauth=initialize
```

`?oauth=initialize` explicitly triggers the OAuth authorization flow. It is
useful for clients that do not reliably begin OAuth discovery automatically.

AWS's documented Codex configuration command is conceptually:

```bash
codex mcp add aws-mcp \
  --url https://aws-mcp.us-east-1.api.aws/mcp?oauth=initialize
```

Do not create duplicate AWS MCP servers using the same name. Preserve the
previous proxy configuration separately for rollback; do not leave both paths
active under conflicting names.

## Required interactive user step

The first AWS MCP tool invocation starts the browser-based OAuth flow:

1. Codex opens AWS Sign-in in the browser.
2. The user signs in with the intended IAM, IAM Identity Center, or federated
   AWS identity.
3. The user reviews the consent page and authorizes AWS MCP Server access.
4. AWS Sign-in returns an OAuth authorization code to Codex.
5. Codex receives short-lived OAuth tokens and calls AWS MCP Server on the
   user's behalf.

The identity must have these permissions:

```text
signin:AuthorizeOAuth2Access
signin:CreateOAuth2Token
```

AWS provides `AWSMCPSignInOAuthAccessPolicy` for this purpose. OAuth does not
grant extra AWS permissions: IAM policies, SCPs, permission boundaries, data
perimeters, and resource policies still control the resulting AWS actions.

Access tokens last about one hour. AWS Sign-in can refresh the session for up
to 12 hours. Browser sign-in may be required again after expiry, revocation,
or changes to the identity/session.

## What the working result proves

The operator-confirmed working result proves that, in this environment:

- Codex can discover and use AWS MCP tools through the direct OAuth endpoint.
- Browser-based AWS Sign-in/OAuth can complete successfully through the active
  network path.
- The previous Codex stdio failure is no longer blocking AWS MCP use.

It does **not** prove:

- that the local `mcp-proxy-for-aws` implementation or SigV4 verifier was
  fixed;
- that WARP/TLS interception is globally configured correctly for every local
  process;
- that every AWS account, profile, Region, or permitted AWS operation will
  work;
- that the OAuth session has broader AWS permissions than the signed-in user.

## Risks and decision guidance

Use direct OAuth when a human is working interactively with one AWS identity in
one Codex session and browser consent is acceptable.

Keep or repair the SigV4 proxy when any of these are required:

- switching among multiple named AWS profiles/accounts in one agent session;
- a fixed default region passed via proxy metadata;
- proxy-side read-only tool hiding or other local signing controls;
- an organization that blocks `signin:AuthorizeOAuth2Access` or
  `signin:CreateOAuth2Token`;
- a non-OAuth-capable MCP client.

Specific risks of the OAuth path:

- **Account selection:** Codex acts as the identity selected in the browser.
  Confirm the account/role before authorizing.
- **Session duration:** OAuth refresh can keep the session active for up to 12
  hours; revoke/sign out if the workstation or session is no longer trusted.
- **WARP/network:** direct OAuth avoids the local proxy's CA inheritance issue,
  but Codex and the browser must still reach AWS MCP and AWS Sign-in over HTTPS.
- **Tool scope:** OAuth is not read-only by default. Apply least-privilege IAM
  and use explicit task boundaries.
- **Observability:** OAuth authorization/token events and subsequent AWS API
  activity are auditable through AWS CloudTrail, subject to account logging
  configuration.

## If the direct OAuth path later fails

Do not immediately revert or repeatedly restart daemons. Identify the failure
class first:

| Symptom | Likely next check |
|---|---|
| Browser does not open / consent fails | OAuth client support, browser callback/network path, and `signin:` permissions |
| OAuth succeeds but tool calls are denied | Signed-in identity's IAM/SCP/resource permissions |
| OAuth server cannot be reached | WARP/DNS/HTTPS trust or firewall/proxy policy |
| Wrong account/role | Sign out/revoke the OAuth session and authorize again with the intended identity |
| Need multiple accounts in one session | Use the SigV4 proxy design with explicit named profiles instead |

## Official AWS references

- [Set up the AWS MCP Server](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/getting-started-aws-mcp-server.html)
- [OAuth 2.1 authentication for AWS MCP Server](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/oauth-authentication.html)

## Evidence boundary

This handoff is based on AWS documentation and the operator's report that the
direct OAuth configuration now works. No local Codex configuration, daemon
logs, AWS credentials, AWS commands, account details, or live tool output were
read or changed to create this document.
