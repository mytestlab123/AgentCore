import * as fs from 'node:fs';
import * as path from 'node:path';
import * as cdk from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';

const MODEL_ID = 'apac.amazon.nova-lite-v1:0';

export class PlatformStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const table = new dynamodb.Table(this, 'PlatformTable', {
      tableName: 'agentcore-issue4-mvp',
      partitionKey: { name: 'pk', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      pointInTimeRecoverySpecification: { pointInTimeRecoveryEnabled: false },
    });

    const logGroup = new logs.LogGroup(this, 'PlatformApiLogs', {
      logGroupName: '/aws/lambda/agentcore-issue4-platform-api',
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const handler = new lambda.Function(this, 'PlatformApi', {
      functionName: 'agentcore-issue4-platform-api',
      runtime: lambda.Runtime.PYTHON_3_13,
      architecture: lambda.Architecture.ARM_64,
      handler: 'index.handler',
      code: lambda.Code.fromInline(fs.readFileSync(path.join(__dirname, '../../api/handler.py'), 'utf8')),
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      logGroup,
      environment: {
        TABLE_NAME: table.tableName,
        ALLOWED_MODEL_ID: MODEL_ID,
        ALLOWED_ORIGINS: 'http://localhost:5173,http://localhost:5174,http://localhost:5175',
      },
    });

    table.grantReadWriteData(handler);
    handler.addToRolePolicy(new iam.PolicyStatement({
      actions: ['bedrock:InvokeModel'],
      resources: [
        `arn:${cdk.Aws.PARTITION}:bedrock:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:inference-profile/${MODEL_ID}`,
        `arn:${cdk.Aws.PARTITION}:bedrock:*::foundation-model/amazon.nova-lite-v1:0`,
      ],
    }));

    const api = new apigateway.LambdaRestApi(this, 'PlatformGateway', {
      restApiName: 'agentcore-issue4-platform-api',
      handler,
      proxy: true,
      deployOptions: {
        stageName: 'demo', throttlingBurstLimit: 2, throttlingRateLimit: 1,
        metricsEnabled: false, tracingEnabled: false,
      },
      defaultCorsPreflightOptions: {
        allowOrigins: ['http://localhost:5173', 'http://localhost:5174', 'http://localhost:5175'],
        allowMethods: ['GET', 'POST', 'OPTIONS'],
        allowHeaders: ['content-type', 'x-api-key'],
      },
    });

    new cdk.CfnOutput(this, 'ApiUrl', { value: api.url });
    new cdk.CfnOutput(this, 'TableName', { value: table.tableName });
    new cdk.CfnOutput(this, 'ModelId', { value: MODEL_ID });
  }
}
