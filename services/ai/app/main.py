"""FastAPI app entry point for the AI service.

Single user-triggered path: the API service POSTs a sensor reading to
``/ai/explain``; the AI service renders the template, calls Claude (or
the offline stub), persists prompt + response rows, and returns the text.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.claude import make_runner
from app.config import load
from app.db import make_engine, make_sessionmaker
from app.persistence import PromptRecord, ResponseRecord, new_id, save
from app.template import TemplateError, load_template, render

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("iot.ai")


TEMPLATES_DIR = Path(__file__).parent / "prompts"
TEMPLATE_ID = "explain-sensor-v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load()
    app.state.settings = settings

    # Load template at boot — malformed = service refuses to start.
    template = load_template(TEMPLATES_DIR / f"{TEMPLATE_ID}.md")
    app.state.template = template
    logger.info("loaded template %s for audience %s", template.id, template.audience)

    # Database (shared SQLite file with API service).
    engine = make_engine(settings)
    SessionLocal = make_sessionmaker(engine)
    app.state.engine = engine
    app.state.SessionLocal = SessionLocal

    # Claude client (or offline stub).
    app.state.runner = make_runner(settings)
    if not settings.has_api_key:
        logger.warning(
            "ANTHROPIC_API_KEY not set — using offline stub. "
            "Real explanations require a key in .env"
        )
    else:
        logger.info("Anthropic ready (%s)", settings.anthropic_model)

    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(title="Pi IoT Platform AI Service", version="0.6.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ai/info")
async def info() -> dict:
    """Used by the API to surface model info / fallback state in the UI."""
    settings = app.state.settings
    return {
        "provider": "claude" if settings.has_api_key else "echo",
        "model": settings.anthropic_model if settings.has_api_key else "echo-stub",
        "fallback": not settings.has_api_key,
    }


# ---------------------------------------------------------------------------
# /ai/explain
# ---------------------------------------------------------------------------


class ExplainReading(BaseModel):
    source: str = Field(..., description="Device or sensor identifier")
    metric: str
    value: float
    unit: str


class ExplainRequest(BaseModel):
    sensor_id: str
    reading: ExplainReading


class ExplainResponse(BaseModel):
    text: str
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int
    status: str
    prompt_id: str
    response_id: str


@app.post("/ai/explain", response_model=ExplainResponse)
async def explain(req: ExplainRequest) -> ExplainResponse:
    template = app.state.template
    runner = app.state.runner
    SessionLocal = app.state.SessionLocal

    context = {
        "source": req.reading.source,
        "metric": req.reading.metric,
        "value": req.reading.value,
        "unit": req.reading.unit,
    }
    try:
        system_text, user_text = render(template, context)
    except TemplateError as e:
        logger.error("template render failed for %s: %s", req.sensor_id, e)
        raise HTTPException(status_code=500, detail="template render failed") from e

    completion = await runner(system_text, user_text)

    prompt_id = new_id()
    response_id = new_id()
    await save(
        SessionLocal,
        PromptRecord(
            id=prompt_id,
            template_id=template.id,
            context=context,
            rendered_text=user_text,
        ),
        ResponseRecord(
            id=response_id,
            prompt_id=prompt_id,
            provider=completion.provider,
            model=completion.model,
            text=completion.text,
            input_tokens=completion.input_tokens,
            output_tokens=completion.output_tokens,
            latency_ms=completion.latency_ms,
            status=completion.status,
            error=completion.error,
        ),
    )

    return ExplainResponse(
        text=completion.text,
        provider=completion.provider,
        model=completion.model,
        input_tokens=completion.input_tokens,
        output_tokens=completion.output_tokens,
        latency_ms=completion.latency_ms,
        status=completion.status,
        prompt_id=prompt_id,
        response_id=response_id,
    )
