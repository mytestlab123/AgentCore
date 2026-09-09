#!/usr/bin/env bash
# Re-arm every current approved AWS-backed AgentCore demo resource.
#
# Current scope is deliberately one resource: the named, detached demo Security
# Group. This script is operator-only and never runs from LibreChat or MCP.

set -o errexit -o nounset -o pipefail
umask 077

mode=${1:-}
profile=${AWS_PROFILE:-amit}
region=${AWS_REGION:-ap-southeast-1}
demo_group_name=AgentCoreIssue46RestrictedSshDemo
public_ssh_cidr=0.0.0.0/0

usage() {
  cat <<'USAGE'
Usage:
  AWS_PROFILE=amit AWS_REGION=ap-southeast-1 \
    ./scripts/rearm-demo-security-state.sh --check

  AWS_PROFILE=amit AWS_REGION=ap-southeast-1 \
    ./scripts/rearm-demo-security-state.sh --approve-rearm

--check performs no AWS mutation.
--approve-rearm restores only TCP/22 from 0.0.0.0/0 on the fixed, unattached
demo Security Group when it is absent. It is idempotent when already present.
USAGE
}

if [[ "$mode" != --check && "$mode" != --approve-rearm ]]; then
  usage >&2
  exit 2
fi

if [[ "$profile" != amit || "$region" != ap-southeast-1 ]]; then
  echo 'NO-GO: this operator command is fixed to AWS_PROFILE=amit in ap-southeast-1.' >&2
  exit 2
fi

for command_name in aws tr; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "ERROR: missing command: $command_name" >&2
    exit 1
  }
done

# Confirm that the selected profile resolves before any resource operation,
# without printing identity data.
aws sts get-caller-identity --profile "$profile" --region "$region" --output json >/dev/null

mapfile -t group_ids < <(
  aws ec2 describe-security-groups --profile "$profile" --region "$region" \
    --filters "Name=group-name,Values=$demo_group_name" \
    --query 'SecurityGroups[].GroupId' --output text --no-cli-pager | tr '\t' '\n'
)
if [[ "${#group_ids[@]}" != 1 || ! "${group_ids[0]}" =~ ^sg-[0-9a-f]{8}([0-9a-f]{9})?$ ]]; then
  echo 'NO-GO: expected exactly one fixed demo Security Group.' >&2
  exit 2
fi
demo_group_id=${group_ids[0]}

attachment_count=$(aws ec2 describe-network-interfaces --profile "$profile" --region "$region" \
  --filters "Name=group-id,Values=$demo_group_id" \
  --query 'length(NetworkInterfaces)' --output text --no-cli-pager)
if [[ "$attachment_count" != 0 ]]; then
  echo 'NO-GO: demo Security Group is attached; public SSH will not be restored.' >&2
  exit 2
fi

ssh_sources=$(aws ec2 describe-security-groups --profile "$profile" --region "$region" \
  --group-ids "$demo_group_id" \
  --query 'SecurityGroups[0].IpPermissions[?IpProtocol==`tcp` && FromPort==`22` && ToPort==`22`].IpRanges[].CidrIp' \
  --output text --no-cli-pager)
if [[ "$ssh_sources" == *"$public_ssh_cidr"* ]]; then
  echo 'DEMO_SECURITY_STATE=NON_COMPLIANT_READY'
  echo 'REARM_ACTION=NOT_NEEDED'
  echo 'ENI_ATTACHMENTS=0'
  exit 0
fi

if [[ "$mode" == --check ]]; then
  echo 'DEMO_SECURITY_STATE=COMPLIANT'
  echo 'REARM_ACTION=REQUIRED'
  echo 'ENI_ATTACHMENTS=0'
  exit 0
fi

aws ec2 authorize-security-group-ingress --profile "$profile" --region "$region" \
  --group-id "$demo_group_id" \
  --ip-permissions '[{"IpProtocol":"tcp","FromPort":22,"ToPort":22,"IpRanges":[{"CidrIp":"0.0.0.0/0"}]}]' \
  --no-cli-pager >/dev/null

verified_sources=$(aws ec2 describe-security-groups --profile "$profile" --region "$region" \
  --group-ids "$demo_group_id" \
  --query 'SecurityGroups[0].IpPermissions[?IpProtocol==`tcp` && FromPort==`22` && ToPort==`22`].IpRanges[].CidrIp' \
  --output text --no-cli-pager)
if [[ "$verified_sources" != *"$public_ssh_cidr"* ]]; then
  echo 'ERROR: exact public SSH rule was not present after re-arm.' >&2
  exit 1
fi

echo 'DEMO_SECURITY_STATE=NON_COMPLIANT_READY'
echo 'REARM_ACTION=RESTORED_EXACT_TCP_22'
echo 'ENI_ATTACHMENTS=0'
