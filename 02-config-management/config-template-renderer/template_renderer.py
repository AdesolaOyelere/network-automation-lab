"""Strict, dependency-free rendering of network configuration templates."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

TAG_RE = re.compile(r"{{\s*([#/!]?)\s*([\w.-]+)?\s*}}")


class TemplateError(ValueError):
    """Raised when template syntax or input data is invalid."""


@dataclass(frozen=True)
class TextNode:
    value: str


@dataclass(frozen=True)
class VariableNode:
    name: str


@dataclass(frozen=True)
class SectionNode:
    name: str
    children: tuple[Node, ...]


Node = TextNode | VariableNode | SectionNode


def _parse(template: str) -> tuple[Node, ...]:
    """Parse variables and repeatable sections into a small syntax tree."""
    matches = list(TAG_RE.finditer(template))

    def parse_nodes(position: int, closing: str | None = None) -> tuple[list[Node], int, int]:
        nodes: list[Node] = []
        cursor = matches[position - 1].end() if position else 0
        while position < len(matches):
            match = matches[position]
            if match.start() > cursor:
                nodes.append(TextNode(template[cursor : match.start()]))
            marker, name = match.group(1), match.group(2)
            if not name:
                raise TemplateError("template tag is missing a name")
            if marker == "/":
                if closing != name:
                    raise TemplateError(f"unexpected closing section: {name}")
                return nodes, position + 1, match.end()
            if marker == "#":
                children, position, cursor = parse_nodes(position + 1, name)
                nodes.append(SectionNode(name, tuple(children)))
                continue
            if marker != "!":
                nodes.append(VariableNode(name))
            position += 1
            cursor = match.end()
        if closing:
            raise TemplateError(f"unclosed section: {closing}")
        if cursor < len(template):
            nodes.append(TextNode(template[cursor:]))
        return nodes, position, len(template)

    nodes, _, _ = parse_nodes(0)
    return tuple(nodes)


def _resolve(name: str, contexts: tuple[dict[str, Any], ...]) -> Any:
    """Resolve a dotted name from the innermost context, then its parents."""
    parts = name.split(".")
    for context in reversed(contexts):
        if parts[0] not in context:
            continue
        value: Any = context[parts[0]]
        for part in parts[1:]:
            if not isinstance(value, dict) or part not in value:
                raise TemplateError(f"missing template value: {name}")
            value = value[part]
        return value
    raise TemplateError(f"missing template value: {name}")


def render_template(template: str, data: dict[str, Any]) -> str:
    """Render a template, failing on missing values or invalid section data."""
    if not isinstance(data, dict):
        raise TemplateError("template data must be an object")

    def render(nodes: tuple[Node, ...], contexts: tuple[dict[str, Any], ...]) -> str:
        output: list[str] = []
        for node in nodes:
            if isinstance(node, TextNode):
                output.append(node.value)
            elif isinstance(node, VariableNode):
                value = _resolve(node.name, contexts)
                if isinstance(value, (dict, list)):
                    raise TemplateError(f"template value must be scalar: {node.name}")
                output.append(str(value))
            else:
                items = _resolve(node.name, contexts)
                if not isinstance(items, list):
                    raise TemplateError(f"section value must be a list: {node.name}")
                for item in items:
                    if not isinstance(item, dict):
                        raise TemplateError(f"section items must be objects: {node.name}")
                    output.append(render(node.children, contexts + (item,)))
        return "".join(output)

    return render(_parse(template), (data,))
