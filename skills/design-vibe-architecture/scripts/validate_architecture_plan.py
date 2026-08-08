#!/usr/bin/env python3
"""Validate the structure of a design-vibe-architecture Markdown plan."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    message: str


SECTION_ALIASES = {
    "executive-summary": ("executive summary", "项目摘要"),
    "scope-assumptions": ("scope and assumptions", "范围与假设"),
    "quality-targets": ("quality targets", "质量目标"),
    "recommended-architecture": ("recommended architecture", "推荐架构"),
    "data-design": ("data design", "数据设计"),
    "api-critical-flow": ("api and critical flow", "api 与关键流程", "api与关键流程"),
    "identity-security": ("identity, security, and privacy", "身份、安全与隐私"),
    "llm-boundary": ("llm boundary", "llm 边界", "llm边界"),
    "production-evolution": ("production and evolution", "生产与演进"),
    "implementation-plan": ("implementation plan", "实施计划"),
    "architecture-decisions": ("architecture decisions", "架构决策"),
    "risks-triggers": ("risks and review triggers", "风险与复审条件"),
    "coding-agent-brief": ("coding-agent brief", "coding agent brief", "编码代理任务书"),
}


def headings(markdown: str) -> list[str]:
    return [match.group(1).strip().lower() for match in re.finditer(r"^#{2,6}\s+(.+?)\s*$", markdown, re.MULTILINE)]


def mermaid_blocks(markdown: str) -> list[str]:
    return re.findall(r"```mermaid\s*\n([\s\S]*?)```", markdown, re.IGNORECASE)


def has_alias(values: list[str], aliases: tuple[str, ...]) -> bool:
    return any(alias in heading for alias in aliases for heading in values)


def validate(markdown: str) -> list[Finding]:
    findings: list[Finding] = []
    found_headings = headings(markdown)
    word_count = len(markdown.split())

    if word_count < 250 and len(markdown) < 1200:
        findings.append(Finding("warning", "plan-too-short", "The plan may be too short to make its decisions auditable."))
    if word_count > 4500 or len(markdown) > 30000:
        findings.append(Finding("warning", "plan-too-long", "The plan is unusually long; use compact mode unless the risk or user request justifies extended detail."))

    for section, aliases in SECTION_ALIASES.items():
        if not has_alias(found_headings, aliases):
            findings.append(Finding("error", f"missing-{section}", f"Missing required section: {aliases[0]}."))

    blocks = mermaid_blocks(markdown)
    if not blocks:
        findings.append(Finding("error", "missing-mermaid", "No Mermaid diagrams found."))
    else:
        lowered = [block.lstrip().lower() for block in blocks]
        if not any(block.startswith(("flowchart", "graph")) for block in lowered):
            findings.append(Finding("error", "missing-system-diagram", "Add a Mermaid flowchart for the system architecture."))
        if not any(block.startswith("sequencediagram") for block in lowered):
            findings.append(Finding("error", "missing-sequence-diagram", "Add a Mermaid sequenceDiagram for the critical flow."))
        has_er = any(block.startswith("erdiagram") for block in lowered)
        er_omitted = bool(re.search(r"er diagram omitted\s*:|er\s*图[^\n]{0,16}(省略|不适用)", markdown, re.IGNORECASE))
        if not has_er and not er_omitted:
            findings.append(Finding("error", "missing-data-diagram", "Add an erDiagram or an explicit 'ER diagram omitted:' explanation."))
        for index, block in enumerate(blocks, start=1):
            if not block.strip():
                findings.append(Finding("error", "empty-mermaid", f"Mermaid block {index} is empty."))
            if re.search(r"\b(TODO|TBD)\b", block, re.IGNORECASE):
                findings.append(Finding("error", "diagram-placeholder", f"Mermaid block {index} still contains TODO/TBD."))

    if re.search(r"\b(TODO|TBD|FIXME)\b|\[insert .+?\]", markdown, re.IGNORECASE):
        findings.append(Finding("error", "unresolved-placeholder", "Resolve TODO, TBD, FIXME, or insert placeholders before delivery."))

    if "| component |" not in markdown.lower() and "| 组件 |" not in markdown:
        findings.append(Finding("warning", "missing-component-table", "Add a component responsibility table."))

    if not re.search(r"revisit trigger|复审条件|重审条件|重新评估", markdown, re.IGNORECASE):
        findings.append(Finding("warning", "missing-revisit-language", "State when consequential decisions should be revisited."))

    if not re.search(r"rollback|roll back|回滚|回退", markdown, re.IGNORECASE):
        findings.append(Finding("warning", "missing-rollback", "Describe rollback or mitigation for release increments."))

    if not re.search(r"authorization|object-level|授权|对象级权限", markdown, re.IGNORECASE):
        findings.append(Finding("warning", "missing-authorization", "Explicitly address authorization or explain why it is not applicable."))

    return findings


def sample_plan() -> str:
    section_lines = [f"## {index}. {aliases[0].title()}" for index, aliases in enumerate(SECTION_ALIASES.values(), start=1)]
    return "\n\n".join(
        ["# Project Architecture Plan", *section_lines]
        + [
            "| Component | Responsibility | Trust boundary | Data owned | Failure behavior | Scaling trigger |\n|---|---|---|---|---|---|\n| API | Rules and authorization | Trusted | Records | Safe errors | Measured load |",
            "Revisit trigger: measured evidence. Rollback: disable the feature flag. Object-level authorization is enforced.",
            "```mermaid\nflowchart LR\n  user[\"User\"] --> api[\"API\"]\n```",
            "```mermaid\nerDiagram\n  USER ||--o{ ITEM : owns\n```",
            "```mermaid\nsequenceDiagram\n  actor User\n  User->>API: Request\n  API-->>User: Response\n```",
        ]
    )


def self_test() -> int:
    with tempfile.TemporaryDirectory() as directory:
        valid_path = Path(directory) / "valid.md"
        valid_path.write_text(sample_plan(), encoding="utf-8")
        valid_findings = validate(valid_path.read_text(encoding="utf-8"))
        valid_errors = [item for item in valid_findings if item.level == "error"]
        assert not valid_errors, valid_errors

        invalid_findings = validate("# Tiny plan\n\nTODO")
        assert any(item.code == "missing-mermaid" for item in invalid_findings)
        assert any(item.code == "unresolved-placeholder" for item in invalid_findings)

    print("validate_architecture_plan.py self-test: passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", nargs="?", type=Path, help="Markdown architecture plan to validate")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable findings")
    parser.add_argument("--self-test", action="store_true", help="Run the built-in validator tests")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.plan is None:
        parser.error("plan is required unless --self-test is used")
    if not args.plan.is_file():
        print(f"error: plan not found: {args.plan}", file=sys.stderr)
        return 2

    results = validate(args.plan.read_text(encoding="utf-8"))
    errors = [item for item in results if item.level == "error"]

    if args.json:
        print(json.dumps({"valid": not errors, "findings": [asdict(item) for item in results]}, ensure_ascii=False, indent=2))
    elif results:
        for item in results:
            print(f"{item.level.upper()} [{item.code}] {item.message}")
        print(f"\n{len(errors)} error(s), {len(results) - len(errors)} warning(s)")
    else:
        print("Architecture plan validation passed with no findings.")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
