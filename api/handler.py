import hashlib
import json
import os
import secrets
import time
from datetime import datetime, timezone
from decimal import Decimal

try:
    import boto3
    from botocore.exceptions import ClientError
except ModuleNotFoundError:  # Local policy tests do not need the AWS SDK.
    boto3 = None

    class ClientError(Exception):
        pass

PROJECT_ID = "demo-security-app"
ALLOWED_MODEL_ID = os.environ.get("ALLOWED_MODEL_ID", "apac.amazon.nova-lite-v1:0")
DENIED_MODEL_ID = "model-premium"
TABLE_NAME = os.environ.get("TABLE_NAME", "")
ALLOWED_ORIGINS = {
    origin.strip()
    for origin in os.environ.get(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://localhost:5175",
    ).split(",")
    if origin.strip()
}

table = boto3.resource("dynamodb").Table(TABLE_NAME) if boto3 and TABLE_NAME else None
bedrock = boto3.client("bedrock-runtime") if boto3 else None


def _response(status_code, body, origin=""):
    allowed_origin = origin if origin in ALLOWED_ORIGINS else "http://localhost:5173"
    return {
        "statusCode": status_code,
        "headers": {
            "content-type": "application/json",
            "access-control-allow-origin": allowed_origin,
            "access-control-allow-headers": "content-type,x-api-key",
            "access-control-allow-methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(body, default=lambda value: int(value) if isinstance(value, Decimal) else str(value)),
    }


def _request_id():
    return f"req_{secrets.token_hex(8)}"


def _key_hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _parse_body(event):
    try:
        return json.loads(event.get("body") or "{}")
    except json.JSONDecodeError as error:
        raise ValueError("Request body must be valid JSON") from error


def _validate_key(headers):
    supplied = next(
        (value for key, value in (headers or {}).items() if key.lower() == "x-api-key"),
        "",
    )
    if not supplied or table is None:
        return False
    item = table.get_item(Key={"pk": f"KEY#{PROJECT_ID}"}).get("Item")
    return bool(item and secrets.compare_digest(item["keyHash"], _key_hash(supplied)))


def _write_log(model_id, status, request_id, latency_ms=0, input_tokens=0, output_tokens=0):
    if table is None:
        return
    timestamp = datetime.now(timezone.utc).isoformat()
    table.put_item(Item={
        "pk": f"LOG#{timestamp}#{request_id}", "entityType": "LOG",
        "timestamp": timestamp, "project": PROJECT_ID, "modelId": model_id,
        "status": status, "requestId": request_id, "latencyMs": latency_ms,
        "inputTokens": input_tokens, "outputTokens": output_tokens,
    })


def _create_key():
    platform_key = f"sk-demo-{secrets.token_urlsafe(18)}"
    try:
        table.put_item(
            Item={
                "pk": f"KEY#{PROJECT_ID}", "entityType": "KEY",
                "keyHash": _key_hash(platform_key),
                "masked": f"{platform_key[:12]}********",
                "createdAt": datetime.now(timezone.utc).isoformat(),
            },
            ConditionExpression="attribute_not_exists(pk)",
        )
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            return None
        raise
    return platform_key


def _invoke_model(prompt):
    started = time.perf_counter()
    response = bedrock.converse(
        modelId=ALLOWED_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 250, "temperature": 0.2},
    )
    latency_ms = round((time.perf_counter() - started) * 1000)
    usage = response.get("usage", {})
    text = response["output"]["message"]["content"][0]["text"]
    return text, latency_ms, usage.get("inputTokens", 0), usage.get("outputTokens", 0)


def handler(event, _context):
    origin = next(
        (value for key, value in (event.get("headers") or {}).items() if key.lower() == "origin"),
        "",
    )
    method = event.get("httpMethod", "GET")
    path = event.get("path", "/")
    if method == "OPTIONS":
        return _response(204, {}, origin)
    if method == "GET" and path.endswith("/project"):
        return _response(200, {
            "project": PROJECT_ID,
            "models": [
                {"id": ALLOWED_MODEL_ID, "name": "Amazon Nova Lite", "access": "Allowed"},
                {"id": DENIED_MODEL_ID, "name": "Premium model", "access": "Not allowed"},
            ],
        }, origin)
    if method == "POST" and path.endswith("/key"):
        platform_key = _create_key()
        if platform_key is None:
            return _response(409, {"message": "Demo key already created; redeploy to reset it."}, origin)
        return _response(201, {"apiKey": platform_key, "project": PROJECT_ID}, origin)
    if not _validate_key(event.get("headers")):
        return _response(401, {"message": "Invalid or missing platform API key."}, origin)
    if method == "GET" and path.endswith("/logs"):
        items = table.scan(
            FilterExpression="entityType = :entityType",
            ExpressionAttributeValues={":entityType": "LOG"},
        ).get("Items", [])
        items.sort(key=lambda item: item["timestamp"], reverse=True)
        return _response(200, {"items": items[:25]}, origin)
    if method == "POST" and path.endswith("/invoke"):
        try:
            body = _parse_body(event)
        except ValueError as error:
            return _response(400, {"message": str(error)}, origin)
        prompt = str(body.get("prompt", "")).strip()
        model_id = str(body.get("modelId", ""))
        request_id = _request_id()
        if not prompt or len(prompt) > 1000:
            return _response(400, {"message": "Prompt must contain 1 to 1000 characters."}, origin)
        if model_id != ALLOWED_MODEL_ID:
            _write_log(model_id or DENIED_MODEL_ID, "Denied", request_id)
            return _response(403, {
                "message": "Not allowed for this project", "status": "Denied",
                "requestId": request_id,
            }, origin)
        try:
            text, latency_ms, input_tokens, output_tokens = _invoke_model(prompt)
            _write_log(model_id, "Allowed", request_id, latency_ms, input_tokens, output_tokens)
            return _response(200, {
                "response": text, "modelId": model_id, "model": "Amazon Nova Lite",
                "latencyMs": latency_ms, "inputTokens": input_tokens,
                "outputTokens": output_tokens, "requestId": request_id, "status": "Allowed",
            }, origin)
        except ClientError as error:
            print(json.dumps({
                "event": "bedrock_error",
                "code": error.response.get("Error", {}).get("Code", "Unknown"),
            }))
            _write_log(model_id, "Error", request_id)
            return _response(502, {
                "message": "Bedrock invocation failed", "status": "Error", "requestId": request_id,
            }, origin)
    return _response(404, {"message": "Not found"}, origin)
