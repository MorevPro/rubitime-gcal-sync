"""FastAPI application for rubitime webhook ingestion."""

from __future__ import annotations

import asyncio
import base64
import json
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.requests import ClientDisconnect

from app.config import get_settings
from app.models.google_event import GoogleEventPayload
from app.models.webhook import WebhookPayload
from app.routes.webhook import process_webhook
from app.services.rubitime_schedule import RubitimeScheduleSyncService
from app.utils.logger import compact_json, configure_logging, get_logger

settings = get_settings()
configure_logging(settings.log_level)

log = get_logger(__name__)

app = FastAPI(
    title="rubitime to Google Calendar",
    version="1.0.0",
    redoc_url=None,
    docs_url=None,
)

_rubitime_sync_task: asyncio.Task[None] | None = None
_rubitime_shutdown_event: asyncio.Event | None = None
_webhook_tasks: set[asyncio.Task[None]] = set()


def _response(status_code: int, body: dict[str, Any] | str) -> JSONResponse:
    if isinstance(body, dict):
        content = body
    else:
        content = {"message": body}
    return JSONResponse(status_code=status_code, content=content)


def _raw_body(body: bytes, is_base64_encoded: bool = False) -> str:
    if not body:
        return ""
    if is_base64_encoded:
        try:
            return base64.b64decode(body).decode("utf-8", errors="replace")
        except Exception as exc:
            return f"<base64 decode error: {exc}> raw={body!r}"
    return body.decode("utf-8", errors="replace")


def _load_json(text: str) -> Any | None:
    candidate = text.strip().lstrip("\ufeff")
    if not candidate:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def _parse_body(raw_body: str) -> dict[str, Any] | None:
    parsed = _load_json(raw_body)
    if isinstance(parsed, dict):
        body = parsed.get("body")
        if isinstance(body, str):
            nested = _load_json(body)
            if isinstance(nested, dict):
                return nested
        return parsed

    # Some webhook relays wrap the real payload as a JSON string in the
    # top-level `body` field. Accept that shape as a fallback.
    if isinstance(parsed, str):
        nested = _load_json(parsed)
        if isinstance(nested, dict):
            return nested

    return None


def _request_meta(request: Request) -> tuple[str, str]:
    return request.method, request.url.path


async def _read_request_body(request: Request) -> bytes | None:
    try:
        # Добавляем таймаут 10 секунд, чтобы избежать зависания при неверном Content-Length
        return await asyncio.wait_for(request.body(), timeout=10.0)
    except asyncio.TimeoutError:
        method, path = _request_meta(request)
        log.error("webhook_request_body_timeout", method=method, path=path, timeout_seconds=10)
        return None
    except ClientDisconnect:
        method, path = _request_meta(request)
        log.warning("webhook_client_disconnected", method=method, path=path)
        return None


def _track_webhook_task(task: asyncio.Task[None]) -> None:
    _webhook_tasks.add(task)

    def _done(done_task: asyncio.Task[None]) -> None:
        _webhook_tasks.discard(done_task)
        try:
            done_task.result()
        except Exception as exc:
            log.exception(
                "webhook_processing_task_failed",
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

    task.add_done_callback(_done)


def _schedule_webhook_processing(
    event: str,
    record_id: int,
    data: dict[str, Any],
) -> None:
    task = asyncio.create_task(asyncio.to_thread(process_webhook, event, record_id, data))
    _track_webhook_task(task)


async def _run_rubitime_scheduler() -> None:
    shutdown_event = _rubitime_shutdown_event
    if shutdown_event is None:
        return

    sync_service = RubitimeScheduleSyncService(settings)
    if not sync_service.is_configured():
        log.info("rubitime_scheduler_disabled", reason="missing_configuration")
        return

    interval = max(settings.rubitime_sync_interval_seconds, 60)
    log.info("rubitime_scheduler_started", interval_seconds=interval)
    while not shutdown_event.is_set():
        try:
            await asyncio.to_thread(sync_service.sync_once)
        except Exception as exc:
            log.exception(
                "rubitime_scheduler_tick_failed",
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            continue


@app.on_event("startup")
async def startup_event() -> None:
    global _rubitime_sync_task, _rubitime_shutdown_event
    if _rubitime_sync_task is None or _rubitime_sync_task.done():
        _rubitime_shutdown_event = asyncio.Event()
        _rubitime_sync_task = asyncio.create_task(_run_rubitime_scheduler())


@app.on_event("shutdown")
async def shutdown_event() -> None:
    global _rubitime_sync_task, _rubitime_shutdown_event
    if _rubitime_shutdown_event is not None:
        _rubitime_shutdown_event.set()
    task = _rubitime_sync_task
    if task is not None:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    if _webhook_tasks:
        for webhook_task in list(_webhook_tasks):
            webhook_task.cancel()
        for webhook_task in list(_webhook_tasks):
            try:
                await webhook_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass
        _webhook_tasks.clear()
    _rubitime_sync_task = None
    _rubitime_shutdown_event = None


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/webhook")
async def webhook(request: Request) -> JSONResponse:
    method, path = _request_meta(request)
    body_bytes = await _read_request_body(request)
    if body_bytes is None:
        return _response(499, {"ok": False, "error": "client_disconnected"})

    raw_body = _raw_body(body_bytes, request.headers.get("x-is-base64-encoded") == "true")
    content_type = request.headers.get("content-type", "")

    log.info(
        "webhook_received",
        method=method,
        path=path,
        content_type=content_type,
        body_size=len(body_bytes),
        body=compact_json(raw_body),
    )

    payload_dict = _parse_body(raw_body)
    if not payload_dict:
        log.warning(
            "webhook_empty_body",
            content_type=content_type,
            body_size=len(body_bytes),
        )
        return _response(400, {"ok": False, "error": "empty_or_invalid_body"})

    try:
        payload = WebhookPayload.model_validate(payload_dict)
    except ValidationError as exc:
        log.warning("webhook_validation_failed", errors=exc.errors())
        return _response(400, {"ok": False, "error": "validation_failed"})

    _schedule_webhook_processing(
        payload.event,
        payload.record_id,
        payload.data.model_dump(mode="python", exclude_none=False),
    )

    log.info(
        "webhook_accepted",
        operation=payload.event,
        record_id=payload.record_id,
        google_event_id=GoogleEventPayload.google_event_id(payload.record_id, payload.event),
    )

    return _response(
        200,
        {
            "ok": True,
            "accepted": True,
            "record_id": payload.record_id,
            "event": payload.event,
        },
    )


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "rubitime-gcal-integration",
    }
