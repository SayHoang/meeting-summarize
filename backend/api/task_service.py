import json
import os
import socket
import sys
from pathlib import Path
from urllib import error, request
from dotenv import load_dotenv
import os

load_dotenv()
from .types import CreateTaskWebhookParams, CreateTaskWebhookResult

DEFAULT_N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")


def _ensure_core_on_path() -> None:
    core_dir = Path(__file__).resolve().parents[1] / "core"
    if str(core_dir) not in sys.path:
        sys.path.append(str(core_dir))


def _resolve_webhook_url(params: CreateTaskWebhookParams) -> str:
    if params.webhook_url:
        return params.webhook_url

    _ensure_core_on_path()
    from utils import get_config

    configured_url = get_config("n8n_webhook_url")
    if isinstance(configured_url, str) and configured_url.strip():
        return configured_url.strip()

    env_url = os.getenv("N8N_WEBHOOK_URL")
    if env_url:
        return env_url.strip()

    return DEFAULT_N8N_WEBHOOK_URL


def _parse_response_body(response_text: str):
    if not response_text.strip():
        return None
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return response_text


def send_create_task_webhook(
    params: CreateTaskWebhookParams,
) -> CreateTaskWebhookResult:
    summary_text = params.summary_text.strip()
    if not summary_text:
        return CreateTaskWebhookResult(
            ok=False,
            status_code=400,
            message="summary_text must not be empty.",
        )

    if params.timeout_seconds <= 0:
        return CreateTaskWebhookResult(
            ok=False,
            status_code=400,
            message="timeout_seconds must be greater than 0.",
        )

    webhook_url = _resolve_webhook_url(params)
    if not webhook_url:
        return CreateTaskWebhookResult(
            ok=False,
            status_code=500,
            message="Webhook URL is not configured.",
        )

    payload = {"summary_text": summary_text}
    if params.job_id:
        payload["job_id"] = params.job_id

    request_body = json.dumps(payload).encode("utf-8")
    webhook_request = request.Request(
        url=webhook_url,
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(webhook_request, timeout=params.timeout_seconds) as response:
            status_code = response.getcode() or 200
            response_text = response.read().decode("utf-8", errors="replace")
            return CreateTaskWebhookResult(
                ok=200 <= status_code < 300,
                status_code=status_code,
                message="Webhook request completed.",
                raw_response=_parse_response_body(response_text),
            )
    except error.HTTPError as http_error:
        response_text = http_error.read().decode("utf-8", errors="replace")
        return CreateTaskWebhookResult(
            ok=False,
            status_code=http_error.code,
            message=f"Webhook returned HTTP {http_error.code}.",
            raw_response=_parse_response_body(response_text),
        )
    except (error.URLError, TimeoutError, socket.timeout) as network_error:
        return CreateTaskWebhookResult(
            ok=False,
            status_code=504,
            message=f"Webhook request failed: {network_error}",
        )
    except Exception as unexpected_error:
        return CreateTaskWebhookResult(
            ok=False,
            status_code=500,
            message=f"Unexpected webhook error: {unexpected_error}",
        )
