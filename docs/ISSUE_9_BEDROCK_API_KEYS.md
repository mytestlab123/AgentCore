# Native Amazon Bedrock API Keys POC

Issue: [#9](https://github.com/mytestlab123/AgentCore/issues/9)

## Outcome

The POC question is answered **yes**. On 31 August 2026, the repo-owned script
used one native Bedrock API key to invoke an approved model and receive an AWS
IAM denial for a restricted model. The client received no general AWS access
key, session credential, or console login.

Live proof in `ap-southeast-1`:

- approved `apac.amazon.nova-lite-v1:0`: HTTP 200 and a real model response;
- restricted `apac.amazon.nova-pro-v1:0`: HTTP 403 enforced by AWS IAM;
- CloudTrail: one successful `Converse` event and one `AccessDenied` event;
- credential: long-term Bedrock service-specific credential, limited to one
  day;
- cleanup: credential, inline policy, and disposable IAM user all deleted.

This is a learning POC, not a production credential-distribution design.

## Verified AWS behavior

The implementation was checked against current AWS documentation before the
live run.

| Property | Short-term key | Long-term key |
| --- | --- | --- |
| Mechanism | Pre-signed AWS Signature Version 4 bearer token | IAM service-specific credential for Bedrock |
| Lifetime | Shorter of the source session lifetime or 12 hours | Configurable from 1 to 36,600 days, or no expiry |
| Revocation | End or invalidate the source session, or deny the identity | Deactivate, reset, or delete the individual credential |
| Best fit | Temporary workloads and the preferred production direction | Exploration and development |

AWS explicitly documents short-term keys as usable only in the Region where
they were generated. Long-term keys are IAM service-specific credentials; the
client still selects a supported Bedrock Runtime Region, and IAM resource
permissions can scope that Region. This proof sets and tests
`ap-southeast-1` only. A bearer key can call supported Amazon Bedrock and
Bedrock Runtime APIs when the owning identity also has the required Bedrock
permissions. It does not add support for Agents for Amazon Bedrock, Bedrock
Data Automation, or bidirectional streaming.

AWS documents these relevant permissions:

- credential lifecycle operations use IAM service-specific credential actions;
- bearer authentication requires `bedrock:CallWithBearerToken`;
- the requested operation still requires its normal Bedrock permission, such
  as model invocation permission.

Sources:

- [Amazon Bedrock API key overview](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys.html)
- [Generate API keys](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys-generate.html)
- [Use API keys](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys-use.html)
- [Supported APIs and Regions](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys-supported.html)
- [API key permissions](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys-permissions.html)
- [IAM service-specific credentials](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_api_keys_for_aws_services.html)

## Why this key type

The POC uses a one-day long-term key because it provides the smallest
individually managed credential for an exploration exercise. It can be deleted
without invalidating another session. The script immediately deletes it after
the proof, so the configured expiry is a fallback rather than the cleanup
mechanism.

For production, prefer short-term credentials and an approved identity/session
delivery mechanism. Do not create non-expiring keys for this POC.

## Developer experience

A developer needs only:

1. the Bedrock Runtime HTTPS endpoint or a supported AWS SDK;
2. the Region used to create the key;
3. the Bedrock API key, supplied as `Authorization: Bearer <key>` for HTTP or
   through `AWS_BEARER_TOKEN_BEDROCK` where the SDK supports it;
4. an approved model identifier.

The key is Bedrock-specific. It is not an AWS access-key pair and cannot be
used to sign normal EC2, S3, Lambda, or other AWS service requests. Its usable
Bedrock operations and models remain governed by IAM permissions attached to
the key's identity.

The tested policy grants bearer-token use for long-term keys, allows invocation
of the Nova Lite inference profile and underlying foundation model, and
explicitly denies the Nova Pro inference profile and underlying foundation
model. The script constructs account-scoped resource identifiers only at run
time; no account-specific identifier is committed.

## Repeatable proof

Plan mode is local-only and does not resolve the AWS profile:

```bash
AWS_PROFILE=amit ./scripts/bedrock-api-key-poc.sh --plan
```

Live mode requires explicit expected-account and expected-caller gates:

```bash
export EXPECTED_AWS_ACCOUNT='<exact-target-account-id>'
export EXPECTED_AWS_CALLER_ARN='<exact-target-caller-arn>'
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 \
  ./scripts/bedrock-api-key-poc.sh --approve-run
```

The script stops if the caller changes, either model is unavailable, the
disposable user already exists, an unexpected general credential or managed
policy appears, ALLOW/DENY differs from the contract, audit events do not
arrive within the bound, or cleanup cannot be verified.

## Secret handling and cleanup

- The full key is written once by AWS into an ignored local directory with
  process umask `077`.
- `curl` reads the bearer header from a protected file, keeping the secret out
  of process arguments.
- The raw credential and header files are deleted before audit polling.
- An exit trap attempts targeted deletion on errors and interrupts.
- Success requires zero service-specific credentials and a `NoSuchEntity`
  result for the disposable IAM user.

Revocation for this long-term key is `update-service-specific-credential` to
set it inactive or `delete-service-specific-credential` to remove it. This POC
uses deletion.

## Audit evidence and observed limitation

CloudTrail event history recorded both Runtime calls with event source
`bedrock.amazonaws.com` and operation `Converse`.

The successful event included the model identifier, actor context, request
identifier, and `callWithBearerToken=true`. The denied event included
`AccessDenied`, actor context, and a request identifier, but the observed AWS
event omitted the target model and bearer marker. The local sanitized denial
record preserves the target model and HTTP status so the request identifiers
can be correlated without exposing the key.

CloudTrail proves AWS API activity; it does not reveal the bearer token.

## Local evidence

The committed [public-safe live proof](evidence/issue-9-live-proof.json)
contains the tested outcomes and sanitized CloudTrail fields. SHA-256 hashes
show that each client response correlates to its CloudTrail event without
publishing raw request identifiers.

Final successful run:
`~/.AGENTS-temp/AgentCore/bedrock-api-key/20260831T212021+0800/`

Public-safe evidence files:

- `result.json`: overall PASS, Region, model policy outcome, and cleanup state;
- `allow.json`: approved model, HTTP 200, request identifier, and token counts;
- `deny.json`: restricted model, HTTP 403, and AWS IAM enforcement;
- `cloudtrail.json`: sanitized audit fields for success and denial;
- `cleanup.json`: credential and user deletion booleans;
- `key-metadata.json`: key type, one-day lifetime, and timestamps, without the
  key or credential identifier.

Raw AWS responses and identity evidence remain local under the protected
`private/` subdirectory and are not committed.

## Cost and non-goals

The live proof used one seven-input-token, six-output-token Nova Lite response
plus one denied request. IAM user and service-specific credential operations
and CloudTrail event history add no dedicated POC infrastructure. The expected
cost is below USD 0.01, excluding taxes and unrelated account usage.

This issue adds no GUI, custom API gateway, DynamoDB service, LiteLLM, Open
WebUI, AgentCore service, multi-provider routing, RAG, quotas, billing, SSO,
containers, or production multi-tenancy.
