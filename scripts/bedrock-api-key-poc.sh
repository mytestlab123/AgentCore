#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail
umask 077

mode=${1:---plan}
profile=${AWS_PROFILE:-amit}
region=${AWS_REGION:-ap-southeast-1}
expected_account=${EXPECTED_AWS_ACCOUNT:-}
expected_caller_arn=${EXPECTED_AWS_CALLER_ARN:-}
user_name=agentcore-issue9-bedrock-api-key-user-r1
policy_name=AgentCoreIssue9BedrockApiKeyPolicy
allowed_model=apac.amazon.nova-lite-v1:0
restricted_model=apac.amazon.nova-pro-v1:0
credential_age_days=1
ttl=${ISSUE9_TTL:-$(date -d '+1 day' '+%d-%m-%y')}
run_id=$(date '+%Y%m%dT%H%M%S%z')
evidence_dir=${EVIDENCE_DIR:-$HOME/.AGENTS-temp/AgentCore/bedrock-api-key/$run_id}
private_dir=$evidence_dir/private

usage() {
  cat <<'USAGE'
Usage: bedrock-api-key-poc.sh [--plan|--approve-run]

--plan         Print the fixed proof scope. Makes no AWS calls.
--approve-run  Create one one-day Bedrock API key, prove ALLOW and DENY,
               collect CloudTrail evidence, then delete the key and IAM user.

Required for --approve-run:
  AWS_PROFILE
  EXPECTED_AWS_ACCOUNT
  EXPECTED_AWS_CALLER_ARN
USAGE
}

print_plan() {
  cat <<PLAN
Issue #9 native Bedrock API-key POC
Profile alias: $profile
Region: $region
IAM user: $user_name
Key type: long-term service-specific credential
Key expiry: $credential_age_days day
Resource TTL: $ttl
Allowed model: $allowed_model
Restricted model: $restricted_model
Cleanup: always delete the credential, inline policy, and IAM user
Estimated AWS cost: below USD 0.01 for one tiny successful inference
PLAN
}

case "$mode" in
  --plan)
    print_plan
    exit 0
    ;;
  --approve-run) ;;
  -h|--help)
    usage
    exit 0
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac

if [[ -z $expected_account || -z $expected_caller_arn ]]; then
  echo 'NO-GO: set EXPECTED_AWS_ACCOUNT and EXPECTED_AWS_CALLER_ARN.' >&2
  exit 2
fi
if [[ ! $ttl =~ ^[0-9]{2}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo 'NO-GO: ISSUE9_TTL must use DD-MM-YY.' >&2
  exit 2
fi

for command_name in aws curl date head install jq rg sed seq sleep; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "ERROR: missing command: $command_name" >&2
    exit 1
  }
done

install -d -m 700 "$private_dir"
start_time=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
policy_file=$private_dir/policy.json
credential_file=$private_dir/credential.json
auth_header_file=$private_dir/authorization.header
credential_id=''
user_created=false
user_was_created=false
policy_created=false
credential_created=false
cleanup_attempted=false
cleanup_failed=false

cleanup_resources() {
  local credential_absent=false managed_policy_arn user_absent=false

  if [[ $cleanup_attempted == true ]]; then
    return
  fi
  cleanup_attempted=true
  rm -f "$auth_header_file" "$credential_file"

  if [[ $user_was_created != true ]]; then
    jq -n \
      '{credentialDeleted:true,userDeleted:true,cleanupFailed:false}' \
      >"$evidence_dir/cleanup.json"
    return
  fi

  if [[ $credential_created == true ]]; then
    if aws iam delete-service-specific-credential \
      --profile "$profile" \
      --user-name "$user_name" \
      --service-specific-credential-id "$credential_id" \
      >"$private_dir/delete-credential.stdout" \
      2>"$private_dir/delete-credential.stderr"; then
      credential_created=false
    else
      cleanup_failed=true
    fi
  fi

  if [[ $user_created == true ]]; then
    if aws iam list-service-specific-credentials \
      --profile "$profile" \
      --user-name "$user_name" \
      --service-name bedrock.amazonaws.com \
      >"$private_dir/credentials-after-delete.json" \
      2>"$private_dir/credentials-after-delete.stderr" &&
      jq -e '.ServiceSpecificCredentials | length == 0' \
        "$private_dir/credentials-after-delete.json" >/dev/null; then
      credential_absent=true
    else
      cleanup_failed=true
    fi
  fi

  if [[ $policy_created == true ]]; then
    if aws iam delete-user-policy \
      --profile "$profile" \
      --user-name "$user_name" \
      --policy-name "$policy_name" \
      >"$private_dir/delete-policy.stdout" \
      2>"$private_dir/delete-policy.stderr"; then
      policy_created=false
    else
      cleanup_failed=true
    fi
  fi

  if [[ $user_created == true ]]; then
    managed_policy_arn=arn:aws:iam::aws:policy/AmazonBedrockLimitedAccess
    aws iam detach-user-policy \
      --profile "$profile" \
      --user-name "$user_name" \
      --policy-arn "$managed_policy_arn" \
      >"$private_dir/detach-managed-policy.stdout" \
      2>"$private_dir/detach-managed-policy.stderr" || true
    if aws iam delete-user \
      --profile "$profile" \
      --user-name "$user_name" \
      >"$private_dir/delete-user.stdout" \
      2>"$private_dir/delete-user.stderr"; then
      user_created=false
    else
      cleanup_failed=true
    fi
  fi

  if aws iam get-user --profile "$profile" --user-name "$user_name" \
    >"$private_dir/user-after-delete.json" \
    2>"$private_dir/user-after-delete.stderr"; then
    cleanup_failed=true
  elif rg -q 'NoSuchEntity' "$private_dir/user-after-delete.stderr"; then
    user_absent=true
  else
    cleanup_failed=true
  fi

  jq -n \
    --argjson credentialDeleted "$credential_absent" \
    --argjson userDeleted "$user_absent" \
    --argjson cleanupFailed "$cleanup_failed" \
    '{credentialDeleted:$credentialDeleted,userDeleted:$userDeleted,cleanupFailed:$cleanupFailed}' \
    >"$evidence_dir/cleanup.json"
}

on_exit() {
  local exit_code=$?
  trap - EXIT INT TERM
  cleanup_resources
  if [[ $cleanup_failed == true ]]; then
    echo "ERROR: cleanup incomplete; inspect $evidence_dir" >&2
    exit 1
  fi
  exit "$exit_code"
}
trap on_exit EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

aws sts get-caller-identity --profile "$profile" --region "$region" \
  >"$private_dir/identity.json"
account=$(jq -er '.Account' "$private_dir/identity.json")
caller_arn=$(jq -er '.Arn' "$private_dir/identity.json")
if [[ $account != "$expected_account" || $caller_arn != "$expected_caller_arn" ]]; then
  echo 'NO-GO: AWS profile resolved to an unexpected account or caller.' >&2
  exit 2
fi

if aws iam get-user --profile "$profile" --user-name "$user_name" \
  >"$private_dir/preexisting-user.json" 2>"$private_dir/preexisting-user.stderr"; then
  echo "NO-GO: dedicated IAM user already exists: $user_name" >&2
  exit 2
fi

aws bedrock list-inference-profiles \
  --profile "$profile" --region "$region" --type-equals SYSTEM_DEFINED \
  >"$private_dir/inference-profiles.json"
for model_id in "$allowed_model" "$restricted_model"; do
  jq -e --arg model "$model_id" \
    '.inferenceProfileSummaries[] | select(.inferenceProfileId == $model and .status == "ACTIVE")' \
    "$private_dir/inference-profiles.json" >/dev/null || {
      echo "NO-GO: required inference profile is not active: $model_id" >&2
      exit 2
    }
done

account_id=$account
jq -n \
  --arg region "$region" \
  --arg account "$account_id" \
  --arg allowed "$allowed_model" \
  --arg restricted "$restricted_model" \
  '{
    Version:"2012-10-17",
    Statement:[
      {
        Sid:"AllowLongTermBedrockBearerToken",
        Effect:"Allow",
        Action:"bedrock:CallWithBearerToken",
        Resource:"*",
        Condition:{StringEquals:{"bedrock:bearerTokenType":"LONG_TERM"}}
      },
      {
        Sid:"AllowApprovedModelOnly",
        Effect:"Allow",
        Action:["bedrock:InvokeModel","bedrock:InvokeModelWithResponseStream"],
        Resource:[
          "arn:aws:bedrock:\($region):\($account):inference-profile/\($allowed)",
          "arn:aws:bedrock:*::foundation-model/amazon.nova-lite-v1:0"
        ]
      },
      {
        Sid:"ExplicitlyDenyRestrictedModel",
        Effect:"Deny",
        Action:["bedrock:InvokeModel","bedrock:InvokeModelWithResponseStream"],
        Resource:[
          "arn:aws:bedrock:\($region):\($account):inference-profile/\($restricted)",
          "arn:aws:bedrock:*::foundation-model/amazon.nova-pro-v1:0"
        ]
      }
    ]
  }' >"$policy_file"

aws iam create-user \
  --profile "$profile" \
  --user-name "$user_name" \
  --tags \
    Key=Name,Value="$user_name" \
    Key=dev,Value=amit \
    Key=project,Value=AgentCore \
    Key=created,Value="$(date '+%Y-%m-%d')" \
    Key=tools,Value=cdx \
    Key=environment,Value=dev \
    Key=owner,Value=amit \
    Key=version,Value=issue-9-r1 \
    Key=TTL,Value="$ttl" \
    Key=purpose,Value=native-bedrock-api-key-poc \
    Key=phase,Value=issue-9 \
    Key=cleanup,Value=delete \
  >"$private_dir/create-user.json"
user_created=true
user_was_created=true

aws iam put-user-policy \
  --profile "$profile" \
  --user-name "$user_name" \
  --policy-name "$policy_name" \
  --policy-document "file://$policy_file" \
  >"$private_dir/put-policy.stdout"
policy_created=true

access_key_count=$(aws iam list-access-keys \
  --profile "$profile" --user-name "$user_name" \
  --query 'length(AccessKeyMetadata)' --output text)
attached_policy_count=$(aws iam list-attached-user-policies \
  --profile "$profile" --user-name "$user_name" \
  --query 'length(AttachedPolicies)' --output text)
console_login=false
if aws iam get-login-profile --profile "$profile" --user-name "$user_name" \
  >"$private_dir/login-profile.json" 2>"$private_dir/login-profile.stderr"; then
  console_login=true
fi
if [[ $access_key_count != 0 || $attached_policy_count != 0 || $console_login != false ]]; then
  echo 'ERROR: dedicated user received an unexpected general credential or managed policy.' >&2
  exit 1
fi

aws iam create-service-specific-credential \
  --profile "$profile" \
  --user-name "$user_name" \
  --service-name bedrock.amazonaws.com \
  --credential-age-days "$credential_age_days" \
  >"$credential_file"
credential_created=true
credential_id=$(jq -er '.ServiceSpecificCredential.ServiceSpecificCredentialId' "$credential_file")
api_key=$(jq -er '.ServiceSpecificCredential.ServiceApiKeyValue // .ServiceSpecificCredential.ServiceCredentialSecret' "$credential_file")
jq '{keyType:"long-term",credentialAgeDays:1,created:.ServiceSpecificCredential.CreateDate,expires:.ServiceSpecificCredential.ExpirationDate,status:.ServiceSpecificCredential.Status}' \
  "$credential_file" >"$evidence_dir/key-metadata.json"
printf 'Authorization: Bearer %s\n' "$api_key" >"$auth_header_file"
unset api_key
rm -f "$credential_file"

managed_policy_arn=arn:aws:iam::aws:policy/AmazonBedrockLimitedAccess
if aws iam list-attached-user-policies \
  --profile "$profile" --user-name "$user_name" \
  --query 'AttachedPolicies[?PolicyArn == `arn:aws:iam::aws:policy/AmazonBedrockLimitedAccess`] | length(@)' \
  --output text | rg -qx '1'; then
  aws iam detach-user-policy \
    --profile "$profile" \
    --user-name "$user_name" \
    --policy-arn "$managed_policy_arn" \
    >"$private_dir/detach-managed-policy-before-test.stdout"
fi
attached_policy_count=$(aws iam list-attached-user-policies \
  --profile "$profile" --user-name "$user_name" \
  --query 'length(AttachedPolicies)' --output text)
if [[ $attached_policy_count != 0 ]]; then
  echo 'ERROR: dedicated user has an unexpected managed policy.' >&2
  exit 1
fi

endpoint="https://bedrock-runtime.${region}.amazonaws.com"
payload_file=$private_dir/request.json
jq -n '{messages:[{role:"user",content:[{text:"Reply with exactly: governed access works"}]}],inferenceConfig:{maxTokens:16,temperature:0}}' \
  >"$payload_file"

allowed_status=''
for attempt in $(seq 1 8); do
  allowed_status=$(curl --silent --show-error --max-time 45 \
    --header @"$auth_header_file" \
    --header 'content-type: application/json' \
    --request POST \
    --data-binary @"$payload_file" \
    --dump-header "$private_dir/allowed.headers" \
    --output "$private_dir/allowed-response.json" \
    --write-out '%{http_code}' \
    "$endpoint/model/$allowed_model/converse")
  [[ $allowed_status == 200 ]] && break
  sleep 5
done
if [[ $allowed_status != 200 ]]; then
  echo "ERROR: approved model did not return HTTP 200; status=$allowed_status" >&2
  exit 1
fi
jq -e '.output.message.content[0].text | type == "string" and length > 0' \
  "$private_dir/allowed-response.json" >/dev/null
allowed_request_id=$(sed -nE 's/^[Xx]-[Aa]mzn-[Rr]equest[Ii]d:[[:space:]]*([^[:space:]\r]+).*/\1/p' \
  "$private_dir/allowed.headers" | head -n 1)
jq -n \
  --arg model "$allowed_model" \
  --arg httpStatus "$allowed_status" \
  --arg requestId "$allowed_request_id" \
  --argjson inputTokens "$(jq '.usage.inputTokens' "$private_dir/allowed-response.json")" \
  --argjson outputTokens "$(jq '.usage.outputTokens' "$private_dir/allowed-response.json")" \
  '{result:"ALLOW",model:$model,httpStatus:($httpStatus|tonumber),requestId:$requestId,inputTokens:$inputTokens,outputTokens:$outputTokens}' \
  >"$evidence_dir/allow.json"

denied_status=$(curl --silent --show-error --max-time 45 \
  --header @"$auth_header_file" \
  --header 'content-type: application/json' \
  --request POST \
  --data-binary @"$payload_file" \
  --dump-header "$private_dir/denied.headers" \
  --output "$private_dir/denied-response.json" \
  --write-out '%{http_code}' \
  "$endpoint/model/$restricted_model/converse")
if [[ $denied_status != 403 ]] ||
  ! rg -q 'AccessDenied|not authorized' "$private_dir/denied-response.json"; then
  echo "ERROR: restricted model was not denied by AWS; status=$denied_status" >&2
  exit 1
fi
denied_request_id=$(sed -nE 's/^[Xx]-[Aa]mzn-[Rr]equest[Ii]d:[[:space:]]*([^[:space:]\r]+).*/\1/p' \
  "$private_dir/denied.headers" | head -n 1)
jq -n \
  --arg model "$restricted_model" \
  --arg httpStatus "$denied_status" \
  --arg requestId "$denied_request_id" \
  '{result:"DENY",enforcedBy:"AWS IAM",model:$model,httpStatus:($httpStatus|tonumber),requestId:$requestId}' \
  >"$evidence_dir/deny.json"

cleanup_resources
if [[ $cleanup_failed == true ]]; then
  echo "ERROR: cleanup failed; inspect $evidence_dir" >&2
  exit 1
fi

audit_ready=false
for attempt in $(seq 1 30); do
  aws cloudtrail lookup-events \
    --profile "$profile" \
    --region "$region" \
    --lookup-attributes AttributeKey=Username,AttributeValue="$user_name" \
    --start-time "$start_time" \
    --max-results 50 \
    >"$private_dir/cloudtrail.json"

  jq '[.Events[].CloudTrailEvent | fromjson |
    select(.eventSource == "bedrock.amazonaws.com" or .eventSource == "bedrock-runtime.amazonaws.com") |
    {
      eventTime,
      eventSource,
      eventName,
      errorCode:(.errorCode // null),
      requestId:(.requestID // null),
      modelId:(.requestParameters.modelId // null),
      bearerToken:(.additionalEventData.callWithBearerToken // null),
      actorType:(.userIdentity.type // null),
      actorName:(.userIdentity.userName // null)
    }]' "$private_dir/cloudtrail.json" >"$evidence_dir/cloudtrail.json"

  success_events=$(jq '[.[] | select(.eventName == "Converse" and .errorCode == null)] | length' \
    "$evidence_dir/cloudtrail.json")
  denied_events=$(jq '[.[] | select(.eventName == "Converse" and ((.errorCode // "") | test("AccessDenied")))] | length' \
    "$evidence_dir/cloudtrail.json")
  bearer_events=$(jq '[.[] | select(.bearerToken == true or .bearerToken == "true")] | length' \
    "$evidence_dir/cloudtrail.json")
  if ((success_events >= 1 && denied_events >= 1 && bearer_events >= 1)); then
    audit_ready=true
    break
  fi
  sleep 10
done
if [[ $audit_ready != true ]]; then
  echo "ERROR: CloudTrail did not expose both bearer-token ALLOW and DENY events in time; inspect $evidence_dir" >&2
  exit 1
fi

jq -n \
  --arg timestamp "$(date --iso-8601=seconds)" \
  --arg profile "$profile" \
  --arg region "$region" \
  --arg user "$user_name" \
  --arg allowedModel "$allowed_model" \
  --arg restrictedModel "$restricted_model" \
  --arg TTL "$ttl" \
  --argjson successEvents "$success_events" \
  --argjson deniedEvents "$denied_events" \
  '{
    status:"PASS",
    timestamp:$timestamp,
    profileAlias:$profile,
    region:$region,
    keyType:"long-term Bedrock service-specific credential",
    credentialAgeDays:1,
    iamUser:$user,
    generalAwsAccessKeysCreated:false,
    consoleLoginCreated:false,
    allowedModel:$allowedModel,
    restrictedModel:$restrictedModel,
    allowedByAws:true,
    deniedByAwsIam:true,
    cloudTrail:{successEvents:$successEvents,deniedEvents:$deniedEvents,bearerTokenSuccessMarked:true},
    TTL:$TTL,
    cleanup:"verified-delete"
  }' >"$evidence_dir/result.json"

printf 'PASS: native Bedrock API key ALLOW, DENY, audit, and cleanup verified.\n'
printf 'Evidence: %s\n' "$evidence_dir"
