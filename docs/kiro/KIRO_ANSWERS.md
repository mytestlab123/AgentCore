# Kiro -> ChatGPT: AWS Bedrock / AgentCore Answers

**Owner:** Kiro
**Question source:** `docs/kiro/CHATGPT_QUESTIONS.md`
**Purpose:** Persistent response file for Kiro-to-ChatGPT technical exchange.

> This response separates current documentation, current sandbox observations, dated repository evidence, and inference. Internet-source content is paraphrased; content was rephrased for compliance with licensing restrictions.

---

## Response status

- **Date:** 2026-09-07
- **AWS profile alias used:** `PERSONAL_TEST_ACCOUNT` intended; no usable AWS credentials were present in this sandbox, and no profile/account/Region was switched.
- **Region(s) inspection attempted:** `ap-southeast-1`, `us-east-2`, `us-east-1`, `us-west-2`
- **Read-only only:** YES
- **AWS documentation freshness checked:** 2026-09-07 against current official AWS pages
- **Inspection limitation:** `[ACCOUNT-EVIDENCE]` Every STS, Bedrock, AgentCore, and Service Quotas read attempted in this session stopped before authentication with `Unable to locate credentials`. Therefore this file does **not** claim a fresh account inventory. Dated successful calls recorded in the repository are labeled `REPO-TRUTH`, not current account evidence.

---

## Q1 - What access do we actually have today?

### Q1.1 Bedrock service availability

- `[AWS-DOC]` Amazon Bedrock is offered in Singapore, and the `bedrock-runtime` endpoint is the recommended endpoint for new applications. Model availability is separately Region/endpoint-specific. For the models relevant here, Singapore is a supported source Region for Nova and for GPT-5.6 Luna/Terra through Bedrock Runtime cross-Region inference. GPT-5.6 Luna's in-Region `bedrock-mantle` endpoint is instead limited to US Regions. See [Bedrock endpoint availability](https://docs.aws.amazon.com/bedrock/latest/userguide/endpoints-region-availability.html), [model Region compatibility](https://docs.aws.amazon.com/bedrock/latest/userguide/models-region-compatibility.html), and the [GPT-5.6 Luna model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-openai-gpt-56-luna.html).
- `[ACCOUNT-EVIDENCE]` Current control-plane access cannot be established because the sandbox has no usable AWS credentials. `ListFoundationModels`, `ListInferenceProfiles`, and STS authentication were attempted read-only and did not reach AWS authorization.
- `[REPO-TRUTH]` On 2026-08-31, `docs/ISSUE_9_BEDROCK_API_KEYS.md` and `docs/evidence/issue-9-live-proof.json` recorded an HTTP 200 Nova Lite invocation and corresponding successful CloudTrail `Converse` event in `ap-southeast-1`. On 2026-09-01, `docs/HARNESS_MVP_PROOF.md` recorded a successful AgentCore Harness invocation of Nova 2 Lite in Singapore.
- `[INFERENCE]` The Issue #9 proof remains internally consistent with the repository's later Nova successes; nothing in the repository contradicts it. It is not proof that the key, IAM policy, entitlement, quota, or account state is unchanged on 2026-09-07.

**Direct answers:** Historical **runtime** model invocation is proven; neither historical nor current `ListFoundationModels`/`ListInferenceProfiles` success is committed. Singapore, Ohio, N. Virginia, and Oregon expose relevant Bedrock endpoints, but the exact model/endpoint path matters. Current control-plane access and current ability to list models/profiles in Singapore are **unverified due to absent credentials**.

### Q1.2 Model availability vs entitlement

`[AWS-DOC]` These are separate gates, in increasing order of evidentiary strength:

| Signal | What it proves | What it does not prove |
|---|---|---|
| Model in AWS documentation | AWS publishes/supports the model somewhere | Region, account access, IAM, quota, or successful use |
| Model in console catalog | Console metadata exposes it in the selected context | Entitlement or runtime success |
| `ListFoundationModels` result | Control-plane caller can discover a base model in that Region | Agreement, inference-profile access, IAM invocation, quota, or endpoint correctness |
| Visible inference profile | A system/application profile can be discovered | Permission on both profile and project/model resources, entitlement, or capacity |
| `GetFoundationModelAvailability` | Reports agreement, authorization, entitlement, and Region statuses for that model | It is still not an inference transaction; backend/account inconsistencies can remain |
| IAM allows invocation | No identity/resource policy, permission boundary, session policy, or SCP blocks the requested resource/action | Provider agreement, entitlement, payment, quota, capacity, endpoint correctness |
| Account/model entitlement | AWS/provider permits this account to consume that model | The invoking principal's IAM or available throughput |
| Marketplace agreement/subscription | Third-party commercial terms are accepted; first invocation can initiate this automatically | IAM invocation permission or quota. Amazon and OpenAI models are not Marketplace products |
| Quota available | Configured TPM/RPM/concurrency is nonzero and request fits remaining capacity | Entitlement or IAM; a listed quota does not prove current headroom |
| Successful invocation | The complete path worked for that request at that time | Future availability or permissions for another role, Region, endpoint, profile, or model |

`[AWS-DOC]` Current Bedrock access is default-on with correct permissions. Third-party models may trigger automatic Marketplace subscription; Anthropic additionally requires a one-time first-use case submission, except on the Mantle endpoint. AWS documents `GetFoundationModelAvailability` as the programmatic status check. See [Request access to models](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html).

`[INFERENCE]` When documentation/catalog discovery succeeds but the runtime says “unavailable” or “not entitled,” the likely class is account/model backend entitlement or agreement state—not model discovery. First exclude wrong endpoint/Region/model ID, explicit IAM/SCP denial, missing Marketplace/Anthropic prerequisites, and zero quota. The repository's Luna/Terra result is unusual because the status API reported authorized/available while Mantle returned account-unavailable; that points to an AWS-side availability inconsistency rather than normal IAM denial.

### Q1.3 Current blocker

`[ACCOUNT-EVIDENCE]` The first current blocker is environmental: this sandbox cannot authenticate to `PERSONAL_TEST_ACCOUNT`. The table therefore reports the **last dated evidence**, not invented current status.

| Model/provider | Region | Discoverable? | Entitled? | IAM allowed? | Quota usable? | Invocation tested previously? | Current/last-known blocker |
|---|---|---:|---:|---:|---:|---:|---|
| Amazon Nova Lite v1 (`apac.amazon.nova-lite-v1:0`) | `ap-southeast-1` | Not freshly checked | Proven usable 2026-08-31 | Yes for Issue #9 key then | Yes for one request then | Yes, HTTP 200 | Current state unknown because credentials are unavailable; no historical model blocker |
| Amazon Nova Pro v1 (`apac.amazon.nova-pro-v1:0`) | `ap-southeast-1` | Not freshly checked | Later invocation evidence indicates yes | **No** for the intentionally restricted Issue #9 key; yes for a separate scoped key | Historically usable on separate path | Yes | Expected IAM deny for the restricted key, not entitlement failure |
| Amazon Nova 2 Lite (`global.amazon.nova-2-lite-v1:0`) via Harness | Harness in `ap-southeast-1` | Harness/model worked 2026-09-01 | Historically yes | Temporary Harness role allowed it | Historically usable | Yes | No historical blocker; current state unverified |
| Amazon Nova 2 Lite native probe from retained LibreChat EC2 role | Singapore source/global profile | Model family historically usable | Historically yes elsewhere | **No** on that EC2 role | Not reached | Attempted, denied pre-inference | Identity policy lacked `bedrock:InvokeModel` on the inference profile |
| OpenAI GPT-5.6 Luna | `us-east-2` Mantle in repo test; Singapore supported through Runtime CRIS in current docs | Yes in docs; repo availability API said Region available | Repo API said available | Repo API said authorized | Not established; inference never started | Yes, failed | AWS-side account/model availability discrepancy: HTTP 401 account-unavailable despite availability API statuses |
| OpenAI GPT-5.6 Terra | `us-east-2` Mantle in repo test | Same as Luna | Same as Luna | Same as Luna | Not established | Yes, failed | Same AWS-side account/model availability discrepancy |
| GPT-5.6 Luna through protected GovTechAI provider | External provider | Provider listed it | Historically yes | Provider credential allowed | Historically usable | Yes, including tool calls | No dated blocker; this does not prove Bedrock entitlement |
| Azure Claude Haiku 4.5 through protected provider | External/Azure route | Yes on allowed route | Historically yes | Allowed route succeeded | Historically usable | Yes | A `bedrock.*` route was rejected by the provider allow-list before AWS inference; not a Bedrock entitlement result |

`[REPO-TRUTH]` Sources: `docs/ISSUE_9_BEDROCK_API_KEYS.md`, `docs/HARNESS_MVP_PROOF.md`, `docs/TEST_PROOF.md`, `docs/ISSUE24_GOVERNANCE_PROOF.md`, and `docs/evidence/issue-12-codex-bedrock-smoke.md`.

### Q1.4 Account-level requirements

`[AWS-DOC]` A normal commercial standalone AWS account has no separate “enable Amazon Bedrock” switch.

| Requirement | Required when? |
|---|---|
| Account verification | Normal AWS account standing may affect service use/quotas, but there is no general Bedrock enablement application |
| Payment method/billing | Valid payment is needed for Marketplace-backed third-party subscriptions; account/payment history can influence quotas |
| Organizations/SCP | Not required to enable; an SCP can block Bedrock, Marketplace, IAM, or Region use |
| IAM | Always required for control-plane and runtime actions/resources; inference commonly needs profile/model/project permissions |
| Service-linked role | Not required for a basic direct model invocation; specific features such as managed entitlements or other managed workflows may create/require service roles |
| Bedrock model-access request | The old select-and-request workflow is not the normal commercial path; access is default/automatic subject to prerequisites |
| Use-case submission | One-time for first Anthropic use in the account/organization, except Anthropic through Mantle |
| Marketplace subscription | Automatic on first use for Marketplace-backed third-party models if the caller/account has prerequisites; not used by Amazon or OpenAI models |
| Service quota increase | Only when assigned throughput/concurrency is inadequate; it does not grant entitlement |
| Support/Sales approval | For unexplained AWS-side entitlement inconsistency, non-console quota increases, Reserved tier/account-team offerings, or explicitly gated programs—not routine Bedrock activation |
| Allow-list/preview entitlement | Only where a feature/model explicitly documents it; not a general Bedrock or AgentCore prerequisite |

See [model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html), [Bedrock quotas](https://docs.aws.amazon.com/bedrock/latest/userguide/quotas.html), and [Mantle quotas](https://docs.aws.amazon.com/bedrock/latest/userguide/quotas-mantle.html).

### Q1.5 Bedrock model access UI changes

`[AWS-DOC]` In commercial Regions, the model catalog is now primarily discovery/playground and agreement management, not a universal manual enablement page. Programmatic third-party access management uses agreement APIs plus `GetFoundationModelAvailability`.

1. **Amazon Nova:** choose a supported Nova model/profile, grant `bedrock:InvokeModel`/`Converse` permissions on the exact resources, and invoke. Access is automatic; no Marketplace subscription or provider use-case form. Quotas/capacity still apply.
2. **Anthropic Claude:** submit the first-time use-case details once (unless using Mantle), ensure Marketplace subscribe/view prerequisites and valid payment, accept/create the agreement if not auto-created, grant model/profile IAM, then invoke. Access is agreement-based and normally immediate after successful form submission; quota-limited.
3. **OpenAI on Bedrock:** use a supported model, Region, endpoint, and model/profile ID. GPT-5.6 Luna/Terra are supported in Singapore via Bedrock Runtime cross-Region inference; Luna Mantle in-Region is US-only. OpenAI Bedrock models are not Marketplace products. Access is IAM/entitlement/quota-based, not Marketplace-based. The current docs show Luna model ID `openai.gpt-5.6-luna`; Runtime requests use `us.*`, `in.*`, or `global.*` inference IDs as documented.
4. **Entitlement/availability error:** do not repeatedly invoke. Read-only check model Region/endpoint compatibility, exact ID, `GetFoundationModelAvailability`, inference profiles, IAM/SCP, Marketplace/FTU status where applicable, and quotas. If all status fields are available/authorized but runtime remains account-unavailable, retain sanitized request IDs and open AWS Support; account teams/Sales may be appropriate for model-specific commercial access. There is no documented SLA for such a discrepancy.

---

## Q2 - Bedrock API keys and normal application access

### Q2.1 Native Bedrock API keys

`[AWS-DOC]` [Bedrock API keys](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys.html) are bearer-token authentication for Amazon Bedrock endpoints:

- **Short-term:** valid for the shorter of the parent IAM session or 12 hours, inherits that principal's permissions, and is bound to the Region where generated. AWS currently recommends this type for production when an API key is specifically needed.
- **Long-term:** an IAM service-specific credential backed by a generated IAM user and attached policies; expiration is configurable. AWS recommends it only for exploration, not a production secret-distribution design.
- **IAM relationship:** keys do not bypass IAM. Use requires `bedrock:CallWithBearerToken` or `bedrock-mantle:CallWithBearerToken` plus the ordinary action/resource permission such as `bedrock:InvokeModel`.
- **Runtime APIs:** the recommended `bedrock-runtime` endpoint supports Converse, Invoke, OpenAI-compatible Responses, Chat Completions, and Anthropic Messages (through the documented model API). Mantle supports Responses, Chat Completions, and Messages. The selected model must support the chosen API. See [Bedrock inference APIs](https://docs.aws.amazon.com/bedrock/latest/userguide/apis.html).
- **Regions/models:** API keys are documented in `ap-northeast-1/2/3`, `ap-south-1/2`, `ap-southeast-1/2`, `ca-central-1`, `eu-central-1/2`, `eu-north-1`, `eu-south-1/2`, `eu-west-1/2/3`, `sa-east-1`, `us-east-1`, `us-west-2`, and both US GovCloud Regions. Endpoint, model, profile, entitlement, and quota restrictions still apply. A short-term key is bound to its generation Region. See [API-key supported Regions](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys-supported.html).
- **CloudTrail:** API calls are logged; the bearer token itself is not recorded.
- **Agents/AgentCore:** native Bedrock keys are limited to Bedrock/Bedrock Runtime actions. They are not credentials for the separate `bedrock-agent-runtime` (Agents Classic) or `bedrock-agentcore` service namespaces and cannot administer/invoke AgentCore resources.
- **LibreChat suitability:** acceptable for a small direct-Bedrock lab when stored only server-side. It is not suitable as a browser-delivered key, as an AgentCore credential, or as authority for AWS remediation tools.

`[REPO-TRUTH]` Issue #9 demonstrated a long-term native key with one allowed model and one IAM-denied model, confirming that bearer authentication preserves IAM model scoping.

### Q2.2 Preferred authentication for our POC

| Mechanism | Strength | Weakness | Recommended use |
|---|---|---|---|
| Native Bedrock key | Simple OpenAI-like bearer integration; Bedrock-scoped | Long-term key creates an IAM user; not AgentCore/general AWS | Short lab demo to direct Bedrock only |
| SigV4 SDK credentials/role | Native temporary credentials, role rotation, full IAM controls | Client integration is AWS-specific | **Preferred backend model call and AWS tools** |
| AgentCore Runtime/Harness execution role | Managed workload identity and least privilege | Exists only inside AgentCore workload | **Required/preferred for AgentCore-hosted code** |
| External OpenAI key behind backend | Direct access to preferred OpenAI service | Separate provider, secret, billing, and egress boundary | Preferred external-model path if approved; keep in backend/AgentCore Identity |

`[INFERENCE]` Recommendations:

- **Direct backend model call:** workload role + AWS SDK/SigV4 for Bedrock. Use a short-term Bedrock key only when an OpenAI-compatible client cannot sign SigV4.
- **AgentCore-hosted agent:** AgentCore execution role for AWS; AgentCore Identity/API-key provider for external OpenAI. Never pass a Bedrock key from LibreChat into Runtime as general authority.
- **LibreChat integration:** LibreChat should call a thin server-side OpenAI-compatible adapter. The adapter owns provider auth; the browser receives no AWS/OpenAI key.
- **AWS tool execution:** dedicated, narrow assumed role/execution role per domain and environment. Model-provider credentials must never authorize EC2/SSM/S3 mutations.

---

## Q3 - What exactly is Amazon Bedrock AgentCore?

### Q3.1 Components

`[AWS-DOC]` AgentCore is a modular agent infrastructure platform, not one agent product. The official [AgentCore overview](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html), [Region table](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html), and [pricing page](https://aws.amazon.com/bedrock/agentcore/pricing/) support this summary. “C+D” means a control plane configures the resource and a data plane handles live work.

| Component | Infrastructure meaning / plane | Needed here? | Bedrock/external-model relationship | Main IAM/network dependency | Charging dimension | Singapore |
|---|---|---|---|---|---|---:|
| **Harness** | Managed Strands orchestration loop backed by Runtime; C+D | Optional alternative to custom Runtime | Needs a model; supports Bedrock, OpenAI, Gemini, LiteLLM-compatible providers | Harness invoke/manage + Runtime permissions; execution role; provider/network access | No harness surcharge; underlying model/Runtime/tools | Yes, GA |
| **Runtime microVMs** | Hosts custom agent/tool code with isolated serverless sessions; C+D | Optional; use only if hosting agent code adds value | No Bedrock requirement; any model inside/outside Bedrock | ECR/CodeZip, execution role, inbound IAM/OAuth, VPC/egress | Active CPU/memory seconds | Yes |
| **Runtime Instances** | Hosts longer-lived agents on AWS-managed EC2 capacity in the customer account; C+D | Not needed for this small MVP | No Bedrock requirement | Capacity provider, EC2/EBS/VPC quotas and roles | EC2/EBS/transfer plus AgentCore management fee | Yes |
| **Gateway** | Aggregates MCP tools; proxies HTTP agents and model inference; C+D | Valuable next milestone, not MVP-required | No model required for tool gateway; can also route model providers | Inbound IAM/OAuth; outbound role/API key/OAuth; target networking | API/tool/search calls and indexed targets | Yes |
| **Identity** | Workload identities and outbound OAuth/API-key vault; C+D | Optional; useful for external providers/user delegation | Model-independent | IdP/OIDC, token vault, workload access tokens | Included through Runtime/Gateway; otherwise successful token/key requests | Yes |
| **Memory** | Short-term events and long-term extracted memories; C+D | Omit initially; LibreChat already stores chat | Model-independent for raw events; extraction strategies can consume models | Actor/session scoping, IAM; optional custom strategy network | Events, stored records, retrieval, optional model use | Yes |
| **Policy** | Deterministic Gateway authorization engine using Cedar/Dogwood; C+D | Valuable for server-side ALLOW/DENY | Model-independent | Gateway association, principal claims/IAM, WAT for temporal policy | Authorization requests; NL policy-authoring tokens; guardrails | Yes; temporal also yes |
| **Observability** | OTEL/CloudWatch traces, metrics, logs; data/telemetry plane | A minimal trace is useful | Model-independent | CloudWatch/OTEL permissions and instrumentation | CloudWatch ingestion, storage, query, masking | Yes |
| **Browser** | Isolated managed browser sessions; C+D | Not needed for this MVP | Model-independent tool | Session APIs, network/proxy allow-list | Active CPU/memory seconds, storage/transfer | Yes |
| **Code Interpreter** | Isolated Python/JS/TS execution sessions; C+D | Not needed for this MVP | Model-independent tool | Session APIs; carefully scoped files/network | Active CPU/memory seconds | Yes |
| **Evaluations** | On-demand/online quality evaluation over traces; C+D | Omit initially | Built-in evaluators consume managed model tokens; custom evaluators use yours | Trace access, CloudWatch, evaluator config | Tokens for built-ins; evaluations + own model for custom | Yes |
| **Optimization** | Insights, recommendations, configuration bundles, A/B tests | Omit | Depends on traces/evaluations/models | Observability, Gateway/Runtime for tests | Underlying evaluations/Gateway/Runtime; Failure Insights explicitly public preview/free in current pricing | Yes, with preview caveat |
| **Registry** | Governed catalog of agents, tools, MCP servers, skills | Not needed for 3-4 people | Model-independent | Publisher/curator IAM | Records and search/list/get beyond free tier | **No** in Singapore |
| **Payments (Preview)** | Agent micropayment integration; C+D | Not relevant | Model-independent | Wallet provider, Gateway/Identity; Coinbase path requires Marketplace subscription | Third-party wallet operations | Yes, Preview |

`[AWS-DOC]` Web Search is another built-in capability but is not available in Singapore in the current Region table. The core use case needs only an agent endpoint, model, and narrow tool backend; all other components are optional and independently adoptable.

### Q3.2 AgentCore Runtime

- `[AWS-DOC]` Runtime deploys customer-owned agent/tool code as a compatible container or supported direct-code package. The microVM container path uses the documented Runtime packaging contract; the newer Instances compute type supports Linux on x86_64 and arm64. It is managed, session-isolated agent compute, but it has a protocol/lifecycle contract rather than accepting literally arbitrary processes.
- Python and TypeScript have first-class SDK/CLI paths. Custom containers can use other languages if they implement the required HTTP/MCP/A2A/AG-UI endpoints and health behavior.
- Strands, LangGraph/LangChain, CrewAI, Google ADK, OpenAI Agents SDK, and a custom Python loop are supported patterns.
- Runtime code may call OpenAI directly; AgentCore explicitly supports models outside Bedrock.
- A Codex app-server could be wrapped in a compatible container behind the Runtime contract. That is **technically possible but custom**, and current AWS documentation does not recommend or document Codex app-server as a native Runtime integration. For this use case, a small explicit agent service or OpenAI Agents SDK is easier to operate and audit.
- Runtime manages versioned deployments/endpoints, inbound IAM/OAuth gating, scaling, dedicated session compute, CPU/memory/filesystem isolation, idle stop/resume, streaming, and observability plumbing. It does **not** map sessions to users; the backend must do that.
- MicroVM sessions preserve in-process context while active, default to a 15-minute idle timeout, and support up to 8-hour lifecycles; Instances support longer sessions. Durable conversation state belongs in LibreChat/your database or AgentCore Memory.

See [Runtime internals](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-how-it-works.html), [sessions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-sessions.html), and [Harness vs Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-vs-runtime.html).

### Q3.3 AgentCore vs Agents for Amazon Bedrock

| Name | What it is | Relationship |
|---|---|---|
| Bedrock model inference | APIs that invoke foundation models | Base model service; can be used by any of the others |
| **Bedrock Agents Classic** | Older Bedrock-managed agent/action-group orchestration | In maintenance mode and closed to new customers from 2026-07-30; existing allow-listed accounts continue |
| AgentCore Harness | New managed, configuration-defined Strands agent loop | Closest AgentCore replacement for Agents Classic |
| AgentCore Runtime | Hosting/isolation/scaling for your code-defined agent or tools | Alternative to Harness when you own the loop; complementary to models/Gateway |
| AgentCore Gateway | MCP/HTTP/inference gateway for tools, agents, and models | Complementary to Harness/Runtime/external agents |
| Strands Agents | Open-source agent framework/library | Runs locally, in Runtime, or underneath Harness; not an AWS managed hosting service |
| Agent Toolkit for AWS | AWS MCP Server + skills/plugins/rules for **coding agents** working with AWS | Developer/operations toolkit, not an application-agent runtime |

`[AWS-DOC]` See [Agents Classic maintenance mode](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-classic-maintenance-mode.html) and [Agent Toolkit components](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/components.html). Harness and custom Runtime are partially alternative orchestration choices; model inference, Gateway, Identity, Policy, and Observability are complementary.

### Q3.4 "Harness" terminology

`[AWS-DOC]` **Amazon Bedrock AgentCore Harness is a real GA AgentCore component in current documentation.** It is a managed Strands loop where model, instructions, skills, tools, memory, and limits are configuration. See [AgentCore Harness](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness.html).

`[REPO-TRUTH]` The repository also has a successful create/invoke/delete Harness proof. Therefore do **not** rename every use of “AgentCore Harness” to generic local orchestration. Instead:

- retain **AgentCore Harness** only when referring to the AWS managed resource;
- call local deterministic orchestration the **action orchestrator**, **policy/action contract**, or **local governance layer**;
- keep `HARNESS_MVP_PLAN.md` deferred for its full tool/configuration/trace outcomes, while linking the smaller completed lifecycle proof so readers can distinguish the two scopes.

---

## Q4 - AgentCore availability and access process

### Q4.1 Is AgentCore normally available?

- `[AWS-DOC]` AgentCore Harness is explicitly GA. Runtime, Memory, Gateway, Identity, built-in tools, Observability, Policy, and Evaluations are published regional services with APIs, quotas, and pricing; no ordinary account application/allow-list step is documented.
- `[AWS-DOC]` AgentCore does not require prior Bedrock model entitlement: Runtime and Gateway can use external models, and most components are model-independent. A selected Bedrock model still has its own access requirements.
- `[AWS-DOC]` Singapore supports Harness, Runtime microVMs and Instances, Memory, Gateway, Identity, built-in Browser/Code Interpreter, Observability, Policy (including Temporal Policy), Evaluations, and Optimization. Payments is available there in **Preview**. Registry and Web Search are not supported there in the current table.
- `[AWS-DOC]` Availability status differs by capability: Harness, Registry, Recommendations, Batch Evaluations, A/B Testing, Web Search, and Runtime Gateway targets have explicit GA announcements in current [AgentCore release notes](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/release-notes.html); Payments remains Preview; Optimization Failure Insights and managed session storage are Preview. The core Runtime/Gateway/Memory/Identity/Observability services are normal regional services with APIs, quotas, and pricing. Do not infer an account entitlement request from a preview label.
- `[REPO-TRUTH]` The account successfully created/invoked/deleted a Harness in Singapore on 2026-09-01, so a blanket “this account lacks AgentCore” claim would conflict with repository evidence.

### Q4.2 Read-only account check

`[ACCOUNT-EVIDENCE]` The local AWS CLI recognizes AgentCore control/data-plane APIs for Runtime, Gateway, Memory, Identity, Browser, Code Interpreter, Policy, and Evaluations, but all account calls failed before authorization because credentials were absent. The installed CLI help did not expose Harness commands even though current official docs and the repository proof do; treat that as local CLI/service-model drift, not entitlement evidence.

| Component | Region | API/service visible locally? | Permissions sufficient to inspect? | Additional entitlement suspected? | Evidence/error category |
|---|---|---:|---:|---:|---|
| Bedrock models/profiles | Singapore + US Regions attempted | Yes | Unknown | Unknown | No AWS credentials |
| Harness | Singapore | Current AWS docs: yes; local CLI command model: absent | Unknown | No evidence; prior success | Local CLI drift + no credentials |
| Runtime | Singapore | Yes | Unknown | No evidence | No AWS credentials |
| Gateway | Singapore | Yes | Unknown | No evidence | No AWS credentials |
| Identity | Singapore | Yes | Unknown | No evidence | No AWS credentials |
| Memory | Singapore | Yes | Unknown | No evidence | No AWS credentials |
| Policy/Temporal Policy | Singapore | Yes | Unknown | No evidence | No AWS credentials |
| Browser/Code Interpreter | Singapore | Yes | Unknown | No evidence | No AWS credentials |
| Observability/Evaluations | Singapore | Yes | Unknown | No evidence | No AWS credentials |
| Registry/Web Search | Singapore | Documented unsupported | N/A | N/A | Wrong/unsupported Region, not account entitlement |

No IDs, ARNs, endpoints, or account numbers were emitted.

### Q4.3 If access is missing

| Failure class | Exact next step | Who fixes it? |
|---|---|---|
| Wrong/unsupported Region | Select a documented supported Region; keep model/tool/data-residency requirements explicit | Amit/platform owner |
| Missing IAM permission | Use CloudTrail/authorization error to add only the exact List/Get/Invoke/resource permissions and `iam:PassRole` where required | IAM admin |
| SCP restriction | Identify denying SCP/Region control and obtain an intentional exception; IAM allow cannot override SCP deny | Organizations admin |
| Service not in Region | Move only that component or choose an available substitute; do not call this entitlement | Amit/architect |
| Preview/allow-list | Follow that feature's documented application; if no process is documented, ask AWS Support/account team | AWS service team/Support/Sales |
| Bedrock model entitlement | Check agreement/authorization/entitlement/Region fields and correct model endpoint/ID | Amit first; Support for contradictory AWS state |
| Marketplace missing | Authorized Marketplace principal accepts/enables the product; complete Anthropic FTU if applicable | Marketplace/IAM admin |
| Quota zero/too low | Check Service Quotas and request increase through supported channel; Mantle/AgentCore may require Support | Amit/IAM admin, then AWS Support/account team |
| Billing/account limitation | Correct payment/account verification/standing; provide sanitized error to Support if opaque | Account owner/Billing Support |
| AWS-side entitlement pending | Preserve model, Region, endpoint, timestamp, request ID, and availability response; open a technical Support case | AWS Support/service team; Sales/account team if commercial gate |

### Q4.4 Entitlement delay

`[REPO-TRUTH]` The only concrete entitlement-like evidence is GPT-5.6 Luna and Terra through Bedrock Mantle in `us-east-2`: `GetFoundationModelAvailability` reported `AUTHORIZED` and `AVAILABLE`, while runtime returned HTTP 401 account-unavailable. The repository does not contain a request number, console status, submission type, or screenshot proving this is Amit's “long-running entitlement request.”

- **Likely service/model:** OpenAI GPT-5.6 Luna/Terra on Bedrock, but this remains `[INFERENCE]` until matched to Amit's artifact.
- **Status API/page:** `GetFoundationModelAvailability`; Bedrock model catalog/agreement status; Service Quotas for exposed quota. There is no repository evidence of a separate AgentCore entitlement status.
- **Normal workflow:** automatic/default model access, model agreement where applicable, IAM, quota, invoke. OpenAI models are not Marketplace products.
- **Wait/SLA:** AWS documents short automatic-subscription propagation windows for Marketplace models, but no SLA for this OpenAI account-unavailable discrepancy. Do not invent one.
- **Escalation:** after a fresh read-only status check and one previously authorized/recent sanitized failure artifact, AWS Support is correct. Include request IDs; account team/Sales can help route model-specific entitlement issues.

Amit must provide: sanitized exact error, model ID, endpoint (`bedrock-runtime` or `bedrock-mantle`), Region, timestamp/time zone, request ID, `GetFoundationModelAvailability` statuses, relevant quota names/values, and any entitlement/support request identifier or console screenshot with IDs removed.

---

## Q5 - How does chat actually fit with AgentCore?

### Q5.1 Does AgentCore provide a ChatGPT-like UI?

`[AWS-DOC]` No. AgentCore has consoles, testing surfaces, protocols, and observability views, but it is not an end-user conversation product comparable to LibreChat.

```text
LibreChat/custom UI
  -> authenticated backend or OpenAI-compatible adapter
  -> Harness or AgentCore Runtime endpoint
  -> model + Gateway/policy + tools
```

LibreChat/custom backend must own user-to-session mapping, UI persistence, approval UX, and protocol translation. AgentCore can own agent execution isolation, optional Memory, tool gateway, and server-side policy.

### Q5.2 LibreChat integration

`[AWS-DOC/INFERENCE]` Patterns A-C are compared below. Pattern D is the simplest AWS-supported **agent** path: use the managed Harness so this team does not own an agent container/loop; only the LibreChat protocol adapter remains custom.

| Pattern | What LibreChat sees | State | Tools / approval / policy | Streaming | Small-team complexity |
|---|---|---|---|---|---|
| **A. LibreChat -> OpenAI/Codex -> MCP** | Native model endpoint plus configured MCP servers | LibreChat/provider; local agent process as applicable | Tool schemas in LibreChat/MCP; ASK in LibreChat; hard policy only in tool/IAM unless added | Native provider/UI path | **Low**; fastest MVP |
| **B. LibreChat -> thin API -> Runtime/Harness -> Gateway** | OpenAI-compatible custom endpoint | LibreChat + mapped AgentCore session; optional Memory | Gateway owns tool catalog; LibreChat or app owns approval; Gateway Policy owns server-side ALLOW/DENY | Adapter must translate SSE/AG-UI/runtime streams | **Medium-high**; best learning/controls |
| **C. LibreChat -> model -> emitted call -> Gateway** | Model endpoint and a client-side tool executor | LibreChat/provider | The model only emits structured calls; LibreChat/adapter must execute Gateway. Approval can happen before execution; Gateway Policy is final server check | Requires tool-call and follow-up streaming support | **Medium-high**; easy to draw incorrectly |
| **D. LibreChat -> thin adapter -> AgentCore Harness -> Gateway tools** | OpenAI-compatible custom endpoint | LibreChat + mapped Harness session; optional Harness Memory | Harness/Gateway configuration owns tools; app/LibreChat renders approval; Gateway Policy enforces | Adapter translates Harness streaming | **Medium**; no custom agent loop/container |

`[REPO-TRUTH]` The current adapter's Harness and Codex routes are primarily text paths; the protected GovTechAI route is the demonstrated tool-capable path. LibreChat owns native ASK checkpoint/resume. No implemented AgentCore Gateway/Policy route exists yet.

### Q5.3 OpenAI/Codex preference

| Option | Assessment |
|---|---|
| Direct OpenAI API | **Supported/recommended** behind a backend if organization policy and billing allow it. Do not treat a ChatGPT/Codex subscription bridge as a normal production API credential |
| OpenAI GPT-5.6 on Bedrock | **AWS-supported** and documented, including Runtime CRIS from Singapore; **blocked/unverified for this account** by the last-known Luna/Terra account-availability discrepancy and current missing credentials |
| Codex app-server as agent/runtime | **Technically possible but custom**. The repo's CLI bridge proves a lab path, not a managed production integration |
| AgentCore Runtime code calling OpenAI | **Supported** by AWS; use execution role plus AgentCore Identity/secret provider and controlled egress |
| Harness using OpenAI + Gateway/Policy | **Supported architecture** in current AgentCore docs and simpler than wrapping Codex app-server |
| Codex app-server + AgentCore Gateway/Policy | **Technically possible but custom/unclear**: a bridge must map tool calls, identities, policy-session headers, results, and streaming. No native AWS recipe was found |

`[INFERENCE]` Prefer the OpenAI API or Harness's supported OpenAI provider interface over operating Codex app-server as a backend service unless Codex-specific semantics are a hard requirement.

---

## Q6 - Human-in-the-loop, ALLOW / ASK / DENY, and policy

### Q6.1 AgentCore Gateway Policy

`[AWS-DOC]` [Policy in AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html) intercepts every Gateway tool invocation and evaluates deterministic Cedar/Dogwood rules. It can decide on:

- tool/action identity and Gateway resource;
- structured tool arguments (`context.input`), including operation, environment, account/project, target ARN, or tags **if those are explicitly carried in the schema/input**;
- OAuth user claims (available as principal tags) or IAM principal identity;
- session history through Temporal Policy;
- optional information-provider/guardrail signals documented by Policy.

Important boundary: it does not automatically query arbitrary AWS resource tags or infer a target from prose. If authorization depends on real resource tags, either pass trustworthy normalized attributes from a trusted resolver or enforce AWS-native tag conditions again in the tool role/IAM. See [Policy conditions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-conditions.html).

### Q6.2 Policy enforcement point

```text
User
 -> LibreChat
 -> model/agent emits structured tool call
 -> client/orchestrator sends MCP tools/call to AgentCore Gateway
 -> Gateway authenticates principal and builds policy request
 -> Cedar/Dogwood returns ALLOW or DENY
 -> on ALLOW only: Gateway invokes MCP/Lambda/API target
 -> target calls AWS under narrow role
```

`[AWS-DOC]` Gateway Policy evaluates the structured principal, tool name, Gateway resource, arguments, and optional policy-session history. It does **not** inspect the original natural-language intent as the authorization request. Natural language can be used offline to author candidate policies, but enforcement is deterministic over structured requests. See [authorization flow](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-authorization-flow.html).

### Q6.3 Human approval

`[AWS-DOC]` AgentCore Policy/Gateway does not provide a LibreChat-style end-user Approve/Reject chat UI. Harness supports return-of-control/inline functions, but the application renders and authenticates the human step.

The proposed design can be safe with these constraints:

1. LibreChat ASK is UX, not the sole authority.
2. On approval, a trusted backend—not model text—invokes an `approve_action` Gateway tool as the authenticated approver.
3. The event binds approver, user/session, normalized tool/action, canonical arguments hash, target, environment, nonce, and expiry.
4. Temporal Policy permits remediation only after a matching successful approval event in the same policy session and within a short window.
5. The remediation backend also atomically consumes an idempotency/approval nonce and records the result. Do not rely on a UI button or session history alone for single-use semantics.

`[INFERENCE]` This gives LibreChat good ASK UX while Gateway Policy and the deterministic backend remain the security boundary.

### Q6.4 Temporal Policy

`[AWS-DOC]` **Temporal Policy is a current real AgentCore Policy feature and is supported in Singapore.** It is written in Dogwood, which is Cedar-compatible. See [Temporal policies](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-temporal.html).

- It evaluates earlier request/response/error events in a caller-supplied policy session, matching principal, action, resource, input/output fields, time windows, counts, and sums.
- An approval is normally represented as a successful prior structured Gateway tool response such as `approve_action(output.approved=true, actionHash=...)`, not as arbitrary UI text.
- It supports sequences such as `investigate -> approve -> remediate`, correlation to the same target/arguments, maximum counts, and windows up to 24 hours.
- AgentCore stores the session event history used by the policy engine. The client supplies `x-amzn-bedrock-agentcore-policy-session-id`; same-account/same-Region WAT propagation is required.
- CloudWatch metrics are automatic; detailed spans appear in `aws/spans` when Gateway traces are enabled.
- A generic “one-time approval consumed exactly once” primitive is not documented. Counts can constrain actions, but an application-managed nonce/idempotency record remains prudent, especially for retries/concurrency.
- It fits **Approve Once** if the trusted approval event and exact action are correlated and the backend provides atomic consumption. LibreChat approval alone is insufficient.

### Q6.5 Recommended defence-in-depth

| Layer | Keep? | Authority |
|---|---|---|
| LibreChat ASK | Yes | UX/checkpoint; not hard security |
| Deterministic local action contract | Yes | Canonicalizes action/target, validates schema, binds approval |
| Gateway Policy | Yes when adopted | Central server-side ALLOW/DENY for Gateway calls |
| Narrow MCP implementation | Yes | Rejects unsupported operations and revalidates invariants |
| Least-privilege IAM/SSM/service auth | **Mandatory** | Final cloud authorization boundary; limits blast radius if upstream fails |
| Verification + CloudTrail/evidence | **Mandatory** | Detection/audit; proves result but does not prevent it |

`[INFERENCE]` Layers 2-5 overlap intentionally, not redundantly. The real authority should be least-privilege IAM plus a narrow deterministic remediation backend; Gateway Policy is the centralized agent-specific guard. The model and LibreChat approval are never sole authorities.

---

## Q7 - MCP, AWS tools, and remediation engines

### Q7.1 AgentCore Gateway and MCP

`[AWS-DOC]` [Gateway core concepts](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-core-concepts.html) confirm:

- Lambda functions, OpenAPI/API Gateway APIs, Smithy-described services, integrations/connectors, and existing remote MCP servers can be exposed as one aggregated MCP server.
- Gateway supports tools and can synchronize remote MCP prompts/resources where offered.
- Any MCP-compatible client/agent sees a normal consolidated MCP endpoint.
- Inbound auth supports IAM/SigV4 and OAuth/JWT; outbound auth uses execution roles or AgentCore Identity credential providers for OAuth/API keys/SigV4.
- Policy evaluates before target invocation. Identity supplies authenticated principal context and safely retrieves outbound credentials.
- Gateway can also proxy HTTP agents and route inference providers, but those are distinct from MCP aggregation.

### Q7.2 Agent Toolkit for AWS

`[AWS-DOC]` The current **Agent Toolkit for AWS** consists of a managed AWS MCP Server, skills, plugins, and rules files for coding agents such as Kiro/Codex/Claude Code. It can search docs and execute AWS APIs/scripts under existing IAM, adds MCP-specific IAM context keys, and emits CloudTrail evidence. See [What is Agent Toolkit](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/what-is-agent-toolkit.html).

- It is not AgentCore Gateway and not an application-domain agent framework.
- Gateway can front an existing compatible MCP server, but placing the broad AWS MCP Server behind Gateway is not automatically safer and adds another layer/auth flow.
- IAM can make Toolkit read-only or block operations, but its intended AWS-building/operations surface is much broader than this assistant needs.
- The managed AWS MCP Server exposes a small set of generic but powerful capabilities, including script-based AWS operations. In the official documentation reviewed, IAM constrains what those capabilities may do; it is not presented as a way to publish a domain-specific catalog containing only two or three bespoke tools. Therefore “restricted IAM” is not the same as “narrow tool surface.”
- For this product, use Toolkit in the developer/operator workspace for discovery and approved troubleshooting—not as the production remediation API.
- Build two or three narrow typed tools (for example `get_finding`, `plan_remediation`, `execute_approved_runbook`) and expose only those. This reduces prompt surface, Cedar schema size, and IAM blast radius.

### Q7.3 Deterministic remediation

| Backend | Best use | Position |
|---|---|---|
| IaC remediation PR (CloudFormation/CDK/Terraform) | Resources already managed as code; review/rollback/drift control | First choice for durable configuration |
| ASR / existing SSM Automation playbook | Known Security Hub control with tested deterministic remediation | First/second for compliance |
| SSM Patch Manager | Patch baselines, maintenance windows, patch compliance | First for vulnerability patching |
| Custom SSM Automation document | Bounded workflow with prechecks, approvals, rollback, outputs | Next when no managed playbook fits |
| Cloud Custodian | Policy-as-code detection and simple repetitive cloud remediation | Useful selectively; avoid another platform unless demonstrated |
| Direct AWS API through MCP | Read-only investigation or tiny idempotent gap | Last for mutation; wrap in deterministic backend, never let model compose arbitrary calls |

**Compliance Agent order:** IaC PR for IaC-owned resources -> ASR/standard automation for supported Security Hub controls -> custom SSM Automation -> selective Custodian -> direct API only for narrowly bounded exceptions.

**Vulnerability Agent order:** Inspector/SSM read-only correlation -> Patch Manager maintenance window/patch policy -> custom SSM Automation for package-specific bounded cases -> image/IaC pipeline change -> direct package/API mutation last. ASR is useful only where a matching security-control playbook exists.

`[AWS-DOC]` [Automated Security Response on AWS](https://docs.aws.amazon.com/solutions/latest/automated-security-response-on-aws/solution-overview.html) deploys predefined Security Hub remediation workflows using SSM Automation and related services; it can create IaC drift, so code-managed resources should normally be fixed through code.

---

## Q8 - Proposed two-agent product architecture

`[INFERENCE]` Two **domains** are the right conceptual boundary, but two separately deployed autonomous agents are premature for a 3-4 person team.

- **Now:** one orchestrator with a Compliance skill and a Vulnerability skill, one evidence contract, and separate tool/IAM namespaces.
- **Split into two deployed agents later** only when ownership, IAM roles, approval rules, data retention, session context, or release cadence diverge materially. Compliance and package remediation are likely eventually to justify separate execution identities even if they share one UI/router.
- **Skill:** domain workflow knowledge—how to interpret a finding, evidence checklist, remediation preference order, verification procedure. Skills may guide reasoning but grant no authority.
- **Tool/MCP function:** narrow typed capability with stable input/output, such as `get_s3_control_evidence`, `get_inspector_package_finding`, `start_patch_runbook`, or `verify_control`. Mutation tools accept an approval/action token, not prose.
- **Separate agent:** a distinct autonomous loop/identity/context boundary, not merely a different AWS service API.
- **Orchestration owner:** thin application service initially; Harness or custom Runtime later. It selects domain skill, builds action proposals, pauses, resumes, and records lifecycle.
- **Authorization owner:** Gateway Policy/local deterministic policy plus backend IAM. Never the skill, prompt, or model.
- **Evidence transport:** pass a minimal typed envelope—finding alias, control/CVE, resource alias, account/environment alias, timestamps, normalized relevant fields, source URI/hash, and permitted actions. Store full raw findings in an encrypted evidence store and retrieve only needed fields server-side.
- **Cross-domain context:** share immutable evidence references and action status, not whole chat histories or raw AWS payloads.

---

## Q9 - Compare our three possible stacks

Scores are 1-5, where **5 is best**; “Ops simplicity” and “portability” are positive scores (5 means low burden/low lock-in).

| Stack | MVP ease | Security potential | Learning value | AWS integration | Ops simplicity | Portability | 3-4 engineer fit |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1. Codex-first | 5 | 3 | 3 | 2 | 4 | 4 | 4 |
| 2. AWS-native | 2 | 5 | 5 | 5 | 2 | 2 | 3 |
| 3. Hybrid | 3 | 5 | 4 | 4 | 3 | 4 | 5 |

- `[REPO-TRUTH]` Option 1 is closest to the working tool-capable Luna/LibreChat governance proof, though the current Codex CLI/Harness text routes are not equivalent production backends.
- `[INFERENCE]` Option 2 has the strongest potential controls but currently adds unproven account access, Gateway, Policy, Identity, deployment, and approval integration at once.
- `[INFERENCE]` Option 3 is the best long-term fit only if there is one common typed action/evidence contract. Without that, it becomes two platforms and doubles operations.

**Now / next 1-2 weeks:** Option 1 with a provider-neutral action contract: LibreChat -> thin backend -> one tool-capable approved model -> local deterministic policy -> synthetic/read-only narrow tools. No real mutation.

**Next learning milestone:** a bounded slice of Option 2: Harness (or tiny Runtime) -> one Gateway tool -> one Cedar/Temporal decision -> CloudWatch trace, all read-only and cleaned up.

**Long-term small-team target:** Option 3, but keep one deployed reasoning path at a time. External OpenAI or Harness/Runtime is an adapter behind the same action contract; Gateway/Policy is adopted only where its control/observability benefit is demonstrated.

---

## Q10 - Smallest real AWS AgentCore experiment

`[REPO-TRUTH]` The repository already completed a smaller Harness-only arithmetic lifecycle proof. The next experiment should add exactly the missing tool/policy/trace path.

**Proposed experiment—do not execute:** one Harness using the already proven low-cost Nova 2 Lite path, one AgentCore Gateway, one Lambda target exposing only `describe_demo_region` (returns a fixed sanitized subset of `ec2:DescribeRegions` or, if even that permission is undesirable, a static health payload), one policy engine with one explicit permit and deny-by-default, one invocation, one CloudWatch trace, then cleanup.

- **Minimum resources:** Harness-backed Runtime, Harness execution role, Gateway and execution role, one Lambda and read-only role, one Gateway target, one policy engine/policy, CloudWatch logs/spans.
- **Required components:** Harness, Gateway, Policy, target, IAM, model, Observability. Memory, Identity token vault, Browser, Code Interpreter, Registry, Evaluations, VPC, database, and UI are omitted.
- **Cost category:** cents or less for one short invocation plus tiny Lambda/Gateway/Policy/CloudWatch usage; no harness surcharge. Exact cost cannot be promised.
- **Cleanup:** delete Harness/backing resources, target/Gateway, policy/engine, Lambda/log groups if dedicated, and temporary roles/policies; verify no resources remain.
- **Stop gates:** usable read-only identity; confirm Singapore feature/model availability; inspect all IAM and resource names; confirm nonzero quotas; set one-invocation budget/log retention; ensure no mutation tool; prewrite cleanup commands; stop on any unexpected permission/entitlement/cost response.

`[ACCOUNT-EVIDENCE]` This session has no usable AWS credentials. `[INFERENCE]` Until access is restored, use the equivalent local simulation: preserve MCP `tools/list`/`tools/call`, a policy-session ID, structured Cedar-like ALLOW/DENY inputs, and append-only sanitized trace records around the existing synthetic read-only finding tool. Move the same contract to Gateway only after the access preflight. This is a design only; nothing was created.

---

## Q11 - What should we change in this repository?

No files below were edited.

### `README.md`

- `[REPO-TRUTH]` **Still correct:** Issue #4's direct React -> API Gateway -> Lambda -> Nova Lite scope, KISS implementation, and statement that AgentCore Runtime is unnecessary **for that MVP**.
- `[REPO-TRUTH]` **Scope-bound, not false:** “There is no ... second provider” appears under the Issue #4 minimal architecture. Keep it, but make “Issue #4 stack only” visually explicit so readers do not apply it to later LibreChat/Harness/provider proofs.
- `[REPO-TRUTH]` **Stale/time-sensitive:** retained-key TTL/current-state language after the documented expiry dates.
- `[INFERENCE]` **Update recommendation:** add a “POC lineage/current truth” table separating Issue #4, the smaller Harness lifecycle proof, LibreChat adapter, and synthetic governance demo.

### `docs/POC_ARCHITECTURE.md`

- `[REPO-TRUTH]` **Still correct:** it labels itself future architecture.
- `[REPO-TRUTH]` **Unverified/unimplemented:** integrated Cognito, Runtime/Strands, Gateway, Identity, telemetry, and portal path.
- `[AWS-DOC/REPO-TRUTH]` **Potentially stale:** Gateway described only as an “inference path”; current Gateway supports MCP, HTTP agents, and inference targets, while the repository has not implemented them.
- `[INFERENCE]` **Update recommendation:** distinguish Harness from custom Runtime and mark every component planned/proven/optional.

### `docs/HARNESS_MVP_PLAN.md`

- `[REPO-TRUTH]` **Still correct as a deferred full plan:** it requires a read-only tool, automatic trace evidence, a configuration change, cleanup, and explanation. The smaller 2026-09-01 arithmetic proof did not satisfy those full outcomes and explicitly did not prove a navigable CloudWatch trace.
- `[REPO-TRUTH]` **Needs clarification:** a subset—Harness create/READY/invoke/delete plus role cleanup—was completed before the 2026-09-02 maintenance note. Link that proof without calling the full plan complete.
- `[INFERENCE]` **Do not rename:** retain `HARNESS_MVP_PLAN.md` and “AgentCore Harness,” but add a short distinction between the completed lifecycle proof and the still-deferred tool/policy/trace learning experiment.

### `docs/ISSUE_9_BEDROCK_API_KEYS.md`

- `[REPO-TRUTH]` **Still correct as historical proof:** HTTP 200/403, IAM model restriction, and CloudTrail correlation.
- `[REPO-TRUTH]` **Stale if presented as current:** credential lifetime, account access, model catalog, and “current docs” statements.
- `[AWS-DOC/INFERENCE]` **Clarify:** short-term key Region binding; long-term keys are exploration-only; keys do not authenticate AgentCore/Agents Classic.

### `docs/LIBRECHAT_TOOL_APPROVAL_LIMITATIONS.md`

- `[REPO-TRUTH]` **Still correct and important:** policy begins after structured call emission; model refusal is not policy DENY.
- `[INFERENCE]` **Clarify:** LibreChat ASK is UX, not final AWS authorization. Add the trusted approval event/Temporal Policy pattern as future architecture, not implemented truth.

### Additional repository consistency fixes

- Reconcile `gemini-2.5-flash-lite` proof with adapter naming for `gemini-3.5-flash`.
- Clarify Issue #17/#19/Harness numbering chronology.
- Update `docs/CODEX_BEDROCK_KEY_DEMO.md` to state the precise Luna/Terra discrepancy: availability API authorized/available but Mantle runtime account-unavailable.
- Label the Issue #24 MCP “remediation” as synthetic local state only.
- Never collapse separated POCs into a claim that one integrated production stack exists.

---

## Evidence index

### `ACCOUNT-EVIDENCE`

- 2026-09-07 read-only AWS calls: no usable credentials; STS, Bedrock model/profile lists, AgentCore lists, and Service Quotas did not reach account authorization.
- Local AWS CLI: `aws-cli/2.33.15`; control/data-plane command models present for most AgentCore services, but Harness commands absent from local help.

### `REPO-TRUTH`

- `docs/ISSUE_9_BEDROCK_API_KEYS.md` and `docs/evidence/issue-9-live-proof.json` — 2026-08-31 Nova Lite success and intentionally IAM-denied Nova Pro.
- `docs/HARNESS_MVP_GUIDE.md` and `docs/HARNESS_MVP_PROOF.md` — 2026-09-01 Singapore Harness lifecycle and Nova 2 Lite response.
- `docs/evidence/issue-12-codex-bedrock-smoke.md` — Luna/Terra availability API vs Mantle runtime discrepancy.
- `docs/TEST_PROOF.md`, `docs/ISSUE24_GOVERNANCE_PROOF.md`, and `docs/evidence/issue-24-live-provider-tool-roundtrip.json` — providers, IAM boundaries, native LibreChat ASK, synthetic MCP scope.
- `docs/POC_ARCHITECTURE.md` — explicitly future architecture.
- `docs/LIBRECHAT_TOOL_APPROVAL_LIMITATIONS.md` — post-model-emission policy boundary.

### `AWS-DOC`

- [Bedrock model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)
- [Bedrock API keys](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys.html), [supported APIs](https://docs.aws.amazon.com/bedrock/latest/userguide/apis.html), [supported key Regions](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys-supported.html), and [how keys work](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys-how.html)
- [GPT-5.6 Luna model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-openai-gpt-56-luna.html)
- [Bedrock model Region compatibility](https://docs.aws.amazon.com/bedrock/latest/userguide/models-region-compatibility.html)
- [Mantle quotas](https://docs.aws.amazon.com/bedrock/latest/userguide/quotas-mantle.html)
- [AgentCore overview](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html)
- [AgentCore Regions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html) and [release notes](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/release-notes.html)
- [AgentCore Harness](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness.html) and [Harness vs Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-vs-runtime.html)
- [Runtime internals](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-how-it-works.html) and [sessions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-sessions.html)
- [Gateway concepts](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-core-concepts.html)
- [Policy](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html), [authorization flow](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-authorization-flow.html), and [Temporal Policy](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-temporal.html)
- [AgentCore quotas](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/bedrock-agentcore-limits.html) and [pricing](https://aws.amazon.com/bedrock/agentcore/pricing/)
- [Agents Classic maintenance mode](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-classic-maintenance-mode.html)
- [Agent Toolkit for AWS](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/what-is-agent-toolkit.html)
- [Automated Security Response on AWS](https://docs.aws.amazon.com/solutions/latest/automated-security-response-on-aws/solution-overview.html)

### `INFERENCE`

- Architecture and product recommendations are reasoned from the evidence above; they are not claims that unimplemented components currently work in this account.

---

## Q12 - Final decision summary requested from Kiro

### A. What works in this AWS account today

- `[ACCOUNT-EVIDENCE]` Present AWS-account capabilities cannot be established: this sandbox had no usable credentials on 2026-09-07.
- `[REPO-TRUTH]` Last proven AWS model path: Nova Lite direct inference succeeded in Singapore on 2026-08-31.
- `[REPO-TRUTH]` Last proven scoped authorization: Nova Pro was denied by the restricted Issue #9 IAM policy, while a separately scoped path later invoked Nova Pro successfully.
- `[REPO-TRUTH]` Last proven AgentCore path: Harness create/invoke/delete with Nova 2 Lite succeeded in Singapore on 2026-09-01.
- `[REPO-TRUTH]` Last proven governed AWS read path: narrow EC2/Inspector access succeeded and SSM was explicitly denied.

### B. What is blocked and why

- `[ACCOUNT-EVIDENCE]` **Current inspection blocker — missing credentials:** this sandbox cannot authenticate to `PERSONAL_TEST_ACCOUNT`, so present account/model/quota state is unknown.
- `[REPO-TRUTH/INFERENCE]` **OpenAI Bedrock blocker — AWS-side account/model availability discrepancy:** Luna/Terra Mantle runtime returned account-unavailable despite availability statuses reported as authorized/available.
- `[REPO-TRUTH]` **Nova EC2 path blocker — IAM identity policy:** the retained EC2 role lacked invocation permission for the Nova inference profile.
- `[REPO-TRUTH]` **Visible deletion DENY proof blocker — pre-tool model refusal:** no tool call existed for LibreChat policy to intercept; this is a proof boundary, not an unsafe execution.
- `[REPO-TRUTH]` **Real remediation blocker — intentionally not implemented:** current MCP remediation is synthetic/local only.

### C. Access/entitlement action plan

`[INFERENCE]` Ordered actions:

1. Restore a usable read-only `PERSONAL_TEST_ACCOUNT` session without switching account/profile and confirm the sanitized caller/Region.
2. Read-only list Bedrock models/profiles, check Luna/Terra/Nova availability fields, and inspect relevant Runtime/Mantle quotas.
3. Read-only list AgentCore Harness/Runtime/Gateway/Policy resources and confirm Singapore APIs/permissions; update the local CLI if Harness commands remain absent.
4. Match Amit's pending request to a sanitized model, endpoint, Region, request ID, status response, and console/support artifact.
5. If Luna/Terra still contradict `GetFoundationModelAvailability`, open AWS Support with the sanitized evidence; do not subscribe, request access, or change IAM during inspection.

### D. Recommended MVP architecture

`[INFERENCE]`

```text
LibreChat
  -> thin provider-neutral Agent API
  -> approved tool-capable model
  -> typed action/evidence contract
  -> LibreChat ASK + deterministic local policy
  -> 2-3 narrow read-only/synthetic MCP tools
  -> append-only audit evidence
```

- One orchestrator with Compliance and Vulnerability skills.
- Keep AWS mutation disabled.
- Keep provider credentials server-side.
- Treat LibreChat ASK as UX, not final authorization.
- Canonicalize exact tool, target, arguments, user, environment, and nonce.
- Pass sanitized evidence envelopes, not raw findings.
- Use narrow read-only IAM for any live inspection.
- Preserve a model/provider adapter so AgentCore can be added without rewriting tools.

### E. Recommended long-term small-team architecture

`[INFERENCE]`

```text
LibreChat
  -> thin Agent API / session mapper
  -> Compliance or Vulnerability domain orchestrator
  -> common typed action contract
  -> AgentCore Gateway + Cedar/Dogwood Policy
  -> narrow MCP -> SSM/ASR/IaC workflow
  -> least-privilege IAM
  -> verify/rescan -> CloudTrail/CloudWatch evidence
```

- Split deployed agents only when IAM/ownership boundaries justify it.
- Use Harness by default; custom Runtime only for orchestration Harness cannot express.
- Allow external OpenAI or Bedrock models behind the same adapter.
- Represent approval as a trusted structured Gateway event.
- Correlate approval and remediation with Temporal Policy.
- Atomically consume an application nonce for Approve Once.
- Prefer IaC/ASR/Patch Manager/SSM Automation over direct API mutation.
- Keep IAM and remediation backend as final authority.
- Add Memory, Identity, Evaluations, or Registry only after a demonstrated need.

### F. One next experiment

`[INFERENCE]` After read-only access is restored, create one temporary Singapore Harness using the previously proven Nova 2 Lite path, connect one Gateway Lambda tool that returns only a sanitized read-only Region result, attach one deny-by-default Cedar policy with one explicit permit, invoke it once, capture one CloudWatch trace/policy decision, and immediately delete every dedicated resource; stop before creation if credentials, IAM diff, model availability, quota, cost guard, or cleanup plan is not verified. **Do not execute this experiment as part of this response.**

### G. Open questions for ChatGPT/Amit

`[INFERENCE]` Only unresolved questions:

- What exact sanitized error/request/status artifact corresponds to the reported long-running entitlement request?
- Can Amit provide a usable read-only account session to this environment, without changing the intended account/profile?
- Is direct OpenAI API use organizationally approved, or must all production reasoning use an AWS-mediated endpoint?
- Which resources are currently IaC-owned, so remediation must produce a PR rather than mutate them?
- Who is authorized to approve production remediation, and must a second person approve high-impact actions?
