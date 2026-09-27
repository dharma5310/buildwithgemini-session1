"""Minimal FastAPI proxy for a deployed A2A agent (Agent Runtime, agents-cli 1.1.0+).

The browser talks ONLY to this proxy (same origin, no CORS, no GCP creds in the
browser). The proxy authenticates with Application Default Credentials and
forwards chat to the deployed agent over the A2A protocol, returning replies as
structured parts the chat UI knows how to show:

  * {"kind": "text", "text": ...}  -> a normal chat bubble
  * {"kind": "a2ui", "data": ...}  -> one A2UI message (beginRendering /
    surfaceUpdate); static/index.html renders these as a card.
"""

import os
import uuid
from typing import Any

import google.auth
import google.auth.transport.requests
import httpx
from a2a.client import ClientConfig, ClientFactory
from a2a.client.card_resolver import A2ACardResolver
from a2a.types import (
    Message,
    Part,
    Role,
    SendMessageRequest,
    TaskArtifactUpdateEvent,
)
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

RESOURCE = os.environ["AGENT_ENGINE_RESOURCE_NAME"]
AGENT_DIRECTORY = os.environ.get("AGENT_DIRECTORY", "app")
LOCATION = RESOURCE.split("/locations/")[1].split("/")[0]

A2A_BASE = (
    f"https://{LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/"
    f"{RESOURCE}/api/a2a/{AGENT_DIRECTORY}"
)
_A2UI_MIME = "application/json+a2ui"
VERSION_HEADER = "X-A2A-Version"
PROTOCOL_VERSION_1_0 = "1.0"

_creds, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)


def _auth_headers() -> dict[str, str]:
    _creds.refresh(google.auth.transport.requests.Request())
    return {
        "Authorization": f"Bearer {_creds.token}",
        "Content-Type": "application/json",
        VERSION_HEADER: PROTOCOL_VERSION_1_0,
    }


app = FastAPI()


@app.exception_handler(Exception)
async def _json_errors(request: Request, exc: Exception):
    return JSONResponse(
        status_code=200,
        content={
            "parts": [{"kind": "text", "text": f"Error: {type(exc).__name__}: {exc}"}]
        },
    )


_contexts: dict[str, str] = {}
_card: Any | None = None


async def _get_card(client: httpx.AsyncClient) -> Any:
    global _card
    if _card is None:
        resolver = A2ACardResolver(client, A2A_BASE)
        card = await resolver.get_agent_card()
        # Override internal container interface URLs (0.0.0.0:8000) with public A2A_BASE
        if hasattr(card, "supported_interfaces"):
            for interface in card.supported_interfaces:
                interface.url = A2A_BASE
        if hasattr(card, "additional_interfaces"):
            for interface in card.additional_interfaces:
                interface.url = A2A_BASE
        _card = card
    return _card


def _extract_parts(parts: list) -> list[dict]:
    out: list[dict] = []
    for p in parts:
        text = getattr(p, "text", None)
        if text:
            out.append({"kind": "text", "text": text})
        elif getattr(p, "data", None) is not None:
            meta = getattr(p, "metadata", None) or {}
            mime = meta.get("mimeType") if isinstance(meta, dict) else None
            if mime == _A2UI_MIME:
                out.append({"kind": "a2ui", "data": p.data})
    return out


@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    message = body.get("message", "")
    user_id = body.get("user_id") or "web-user"
    parts: list[dict] = []

    async with httpx.AsyncClient(headers=_auth_headers(), timeout=120) as client:
        card = await _get_card(client)
        factory = ClientFactory(ClientConfig(httpx_client=client))
        a2a_client = factory.create(card)

        msg = Message(
            message_id=str(uuid.uuid4()),
            role=Role.ROLE_USER if hasattr(Role, "ROLE_USER") else Role.user,
            parts=[Part(text=message)],
            context_id=_contexts.get(user_id) or "",
        )

        last_task = None
        got_artifact_update = False
        async for chunk in a2a_client.send_message(SendMessageRequest(message=msg)):
            if hasattr(chunk, "HasField"):
                if chunk.HasField("artifact_update"):
                    if chunk.artifact_update.context_id:
                        _contexts[user_id] = chunk.artifact_update.context_id
                    got_artifact_update = True
                    parts.extend(_extract_parts(list(chunk.artifact_update.artifact.parts)))
                elif chunk.HasField("status_update"):
                    if chunk.status_update.context_id:
                        _contexts[user_id] = chunk.status_update.context_id
                    if chunk.status_update.status.HasField("message"):
                        parts.extend(_extract_parts(list(chunk.status_update.status.message.parts)))
                elif chunk.HasField("task"):
                    last_task = chunk.task
                    if chunk.task.context_id:
                        _contexts[user_id] = chunk.task.context_id
                    for artifact in chunk.task.artifacts:
                        parts.extend(_extract_parts(list(artifact.parts)))
                elif chunk.HasField("message"):
                    parts.extend(_extract_parts(list(chunk.message.parts)))
            elif isinstance(chunk, tuple):
                task, update = chunk
                if task is not None:
                    last_task = task
                    if getattr(task, "context_id", None):
                        _contexts[user_id] = task.context_id
                if isinstance(update, TaskArtifactUpdateEvent):
                    got_artifact_update = True
                    parts.extend(_extract_parts(getattr(update.artifact, "parts", [])))

        if not got_artifact_update and last_task is not None:
            for artifact in getattr(last_task, "artifacts", None) or []:
                parts.extend(_extract_parts(getattr(artifact, "parts", [])))

    if not parts:
        parts = [{"kind": "text", "text": "(The agent didn't return a reply.)"}]
    return JSONResponse({"parts": parts})


app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
