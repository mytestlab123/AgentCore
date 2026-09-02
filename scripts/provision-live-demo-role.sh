#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail

mode=${1:---plan}
profile=${AWS_PROFILE:-amit}
region=${AWS_REGION:-ap-southeast-1}
role_name=agentcore-live-demo-readonly-role-r1
policy_name=AgentCoreLiveDemoReadOnlyPolicy

if [[ $mode != --plan && $mode != --approve-run ]]; then
  echo 'Usage: provision-live-demo-role.sh [--plan|--approve-run]' >&2
  exit 2
fi
if [[ $profile != amit || $region != ap-southeast-1 ]]; then
  echo 'NO-GO: fixed to profile amit in ap-southeast-1.' >&2
  exit 2
fi

caller_arn=$(aws sts get-caller-identity --profile "$profile" --query Arn --output text --no-cli-pager)
if [[ $caller_arn != arn:aws:iam::*:user/* ]]; then
  echo 'NO-GO: amit must resolve to an IAM user for this POC trust policy.' >&2
  exit 2
fi

echo "Role: $role_name"
echo 'ALLOW: EC2 DescribeInstances, Inspector2 ListFindings'
echo 'DENY: SSM Parameter Store list/get actions'
echo 'Lifecycle: TTL=01-10-26, cleanup=review'
[[ $mode == --approve-run ]] || exit 0

tmp_dir=$(mktemp -d)
trap 'rm -rf -- "$tmp_dir"' EXIT

python3 - "$caller_arn" "$tmp_dir/trust.json" "$tmp_dir/policy.json" <<'PY'
import json
import sys

caller, trust_path, policy_path = sys.argv[1:]
trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"AWS": caller}, "Action": "sts:AssumeRole"}]}
policy = {"Version": "2012-10-17", "Statement": [
    {"Sid": "ReadDemoFacts", "Effect": "Allow", "Action": ["ec2:DescribeInstances", "inspector2:ListFindings"], "Resource": "*"},
    {"Sid": "DenyParameterStoreSecrets", "Effect": "Deny", "Action": ["ssm:DescribeParameters", "ssm:GetParameter", "ssm:GetParameters", "ssm:GetParametersByPath"], "Resource": "*"},
]}
with open(trust_path, "w", encoding="utf-8") as stream:
    json.dump(trust, stream)
with open(policy_path, "w", encoding="utf-8") as stream:
    json.dump(policy, stream)
PY

if aws iam get-role --profile "$profile" --role-name "$role_name" --no-cli-pager >/dev/null 2>&1; then
  aws iam update-assume-role-policy --profile "$profile" --role-name "$role_name" --policy-document "file://$tmp_dir/trust.json" --no-cli-pager
else
  aws iam create-role --profile "$profile" --role-name "$role_name" --assume-role-policy-document "file://$tmp_dir/trust.json" --tags \
    Key=Name,Value="$role_name" Key=dev,Value=amit Key=project,Value=AgentCore Key=created,Value=01-09-26 \
    Key=tools,Value=cdx Key=environment,Value=dev Key=owner,Value=amit Key=version,Value=issue12 \
    Key=TTL,Value=01-10-26 Key=purpose,Value=live-demo-readonly Key=phase,Value=POC Key=cleanup,Value=review \
    --no-cli-pager >/dev/null
fi
aws iam put-role-policy --profile "$profile" --role-name "$role_name" --policy-name "$policy_name" --policy-document "file://$tmp_dir/policy.json" --no-cli-pager
aws iam get-role --profile "$profile" --role-name "$role_name" --query 'Role.{RoleName:RoleName,Tags:Tags}' --output json --no-cli-pager
