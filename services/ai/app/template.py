"""Prompt template loader + renderer.

Templates are markdown files with a small YAML-ish front-matter and two
sections, ``## system`` and ``## user``, both of which are rendered with
Jinja2 against a context dict.

The front-matter parser is hand-written to avoid pulling in PyYAML — we
only need to read three keys (``id``, ``audience``, ``required``) and the
``required`` value is a JSON array.

A malformed template raises :class:`TemplateError` at boot, never at
request time.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, StrictUndefined, TemplateError as JinjaTemplateError


class TemplateError(ValueError):
    """The template file is malformed or invalid."""


@dataclass(frozen=True)
class PromptTemplate:
    id: str
    audience: str
    required: tuple[str, ...]
    system: str  # Jinja2 source for the system block
    user: str    # Jinja2 source for the user block


_FRONT_MATTER = re.compile(
    r"\A---\s*\n(?P<front>.*?)\n---\s*\n(?P<body>.*)\Z", re.DOTALL
)
_SECTION = re.compile(r"^##\s+(\w+)\s*\n", re.MULTILINE)


def _parse_front_matter(text: str) -> dict[str, Any]:
    """Trivial 'key: value' parser. Values are JSON-decoded if they look
    like a JSON value, otherwise treated as bare strings."""
    out: dict[str, Any] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise TemplateError(f"front-matter line missing colon: {line!r}")
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if not value:
            raise TemplateError(f"front-matter key {key!r} is empty")
        try:
            out[key] = json.loads(value)
        except json.JSONDecodeError:
            out[key] = value
    return out


def _split_sections(body: str) -> dict[str, str]:
    """Split ``## name`` headed sections into a {name: body} dict."""
    parts: dict[str, str] = {}
    matches = list(_SECTION.finditer(body))
    if not matches:
        raise TemplateError("template body has no '## section' headings")
    for i, m in enumerate(matches):
        name = m.group(1).lower()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        parts[name] = body[start:end].strip()
    return parts


def load_template(path: str | Path) -> PromptTemplate:
    raw = Path(path).read_text(encoding="utf-8")

    m = _FRONT_MATTER.match(raw)
    if not m:
        raise TemplateError(
            f"{path}: missing '---' front-matter at top of file"
        )

    front = _parse_front_matter(m.group("front"))
    body = m.group("body")

    for key in ("id", "audience", "required"):
        if key not in front:
            raise TemplateError(f"{path}: front-matter missing {key!r}")

    if not isinstance(front["required"], list):
        raise TemplateError(f"{path}: 'required' must be a JSON array")

    sections = _split_sections(body)
    if "system" not in sections or "user" not in sections:
        raise TemplateError(
            f"{path}: must have '## system' and '## user' sections"
        )

    return PromptTemplate(
        id=str(front["id"]),
        audience=str(front["audience"]),
        required=tuple(str(x) for x in front["required"]),
        system=sections["system"],
        user=sections["user"],
    )


_env = Environment(undefined=StrictUndefined, autoescape=False)


def render(template: PromptTemplate, context: dict[str, Any]) -> tuple[str, str]:
    """Returns (system_text, user_text)."""
    missing = [k for k in template.required if k not in context]
    if missing:
        raise TemplateError(
            f"template {template.id!r}: missing context keys {missing}"
        )
    try:
        system = _env.from_string(template.system).render(**context)
        user = _env.from_string(template.user).render(**context)
    except JinjaTemplateError as e:
        raise TemplateError(f"render failed: {e}") from e
    return system, user
