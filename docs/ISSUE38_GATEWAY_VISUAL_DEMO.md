# Issue #38 Gateway Policy visual demo

This loopback-only page is the visual verifier for the retained model-free
AgentCore Gateway Policy proof. It is not the Issue #15 model-comparison
portal and it is not LibreChat.

## Start

The private approved identity record must already exist from the retained Issue
#31 proof. The server derives only its SHA-256 gates from that mode-600 local
record; it never sends the record to the browser.

```bash
cd /home/user/git/AgentCore
python3 scripts/gateway_visual_demo.py --serve
```

Open `http://localhost:3334/`.

The server binds only to `127.0.0.1:3334`. Stop it with `Ctrl+C`. It creates,
updates, deploys, bootstraps, deletes, and cleans up nothing.

Every action POST must originate from the local TCP loopback peer and use one
of the two exact paired loopback authorities: `127.0.0.1:<port>` or
`localhost:<port>`. A missing, foreign, or mismatched `Host`/`Origin` returns
only a static `403` BLOCKED result and never reaches the action runner.

## Demo

1. Select **Run ALLOW test**. Expected visible result:

   ```text
   ALLOW
   BACKEND DELTA 1
   RETAINED COST GATE PASS
   NO INFRASTRUCTURE MUTATION
   ```

2. Select **Run DENY test**. Expected visible result:

   ```text
   DENY
   BACKEND DELTA 0
   BACKEND WAS NOT INVOKED
   NO INFRASTRUCTURE MUTATION
   ```

3. The page then displays:

   ```text
   GATEWAY_VISUAL_RESULT=PASS
   ```

The first call can take up to a few minutes because the verifier waits for a
quiet CloudWatch minute and then verifies the bounded metric. The browser sends
no request outside loopback. The browser never receives AWS credentials,
identity hashes, managed URLs, ARNs, account or caller identifiers, policy
text, raw AWS responses, or arbitrary request controls.

## BLOCKED means stop

`BLOCKED` is an expected safe outcome when the local approved identity record,
current AWS identity, retained Gateway/Policy/Lambda linkage, metrics, cost
gate, or port is unavailable or has drifted. It does not attempt to repair the
retained resources. Inspect the mode-600 private evidence directory; do not
retry by deploying, changing IAM, or copying credentials.

## Validation

```bash
./scripts/check.sh
APP_URL=http://localhost:3334/ ./scripts/browser-e2e.sh
```

The browser run records screenshots and sanitized results under the private
browser-E2E evidence directory. Screenshots support the browser claim; the
server-side retained-Gateway and CloudWatch checks remain the AWS proof.
