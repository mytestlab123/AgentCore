#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { PlatformStack } from '../lib/platform-stack';

const app = new cdk.App();
const ttl = app.node.tryGetContext('ttl') ?? 'NOT-DEPLOYED';
const tags: Record<string, string> = {
  Name: 'agentcore-issue4-mvp-r1',
  dev: 'amit',
  project: 'AgentCore',
  created: app.node.tryGetContext('created') ?? new Date().toISOString().slice(0, 10),
  tools: 'cdx',
  environment: 'dev',
  owner: 'amit',
  version: 'issue-4-r1',
  TTL: ttl,
  purpose: 'Three-view governed Bedrock access POC',
  phase: 'issue-4-mvp',
  cleanup: 'delete',
};

for (const [key, value] of Object.entries(tags)) {
  cdk.Tags.of(app).add(key, value);
}

new PlatformStack(app, 'AgentCoreMvp', {
  synthesizer: new cdk.LegacyStackSynthesizer(),
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION ?? 'ap-southeast-1',
  },
  description: 'Issue 4 MVP: API Gateway, Lambda, DynamoDB, and one Bedrock model',
});
