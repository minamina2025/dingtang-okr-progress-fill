#!/usr/bin/env python3
"""Utilities for evidence-backed Dingteam OKR progress filling.

The script is intentionally conservative: it prepares and validates paste-ready
progress plans, but it does not write to Dingteam. Writeback should use a
separate, verified UI/API path after the user approves the exact plan.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SENSITIVE_PATTERNS = [
    (re.compile(r"(?i)(薪资|薪酬|salary|compensation)[：: ]*[\d,.]+[kKwW万千元/年薪月薪 -]*"), r"\1：[已脱敏]"),
    (re.compile(r"(?i)(绩效分|绩效得分|performance score|score)[：: ]*[\d.]+"), r"\1：[已脱敏]"),
    (re.compile(r"1[3-9]\d{9}"), "[手机号已脱敏]"),
    (re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"), "[邮箱已脱敏]"),
    (re.compile(r"\b\d{15,18}[0-9Xx]\b"), "[证件号已脱敏]"),
]

LOCAL_PATH_RE = re.compile(r"(^|\s)(/Users/|/tmp/|/private/tmp/|outputs/|file://)", re.IGNORECASE)
RAW_URL_RE = re.compile(r"https?://[^\s)）>]+", re.IGNORECASE)
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def sanitize_text(text: Any) -> str:
    value = "" if text is None else str(text)
    for pattern, replacement in SENSITIVE_PATTERNS:
        value = pattern.sub(replacement, value)
    return value.strip()


def sanitize_obj(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, list):
        return [sanitize_obj(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_obj(val) for key, val in value.items()}
    return value


def normalize_quarter(value: str) -> str:
    s = re.sub(r"\s+", "", str(value or "").lower())
    s = s.replace("年", "").replace("第", "")
    s = re.sub(r"(一季度|1季度|q1|第一季度)", "q1", s)
    s = re.sub(r"(二季度|2季度|q2|第二季度)", "q2", s)
    s = re.sub(r"(三季度|3季度|q3|第三季度)", "q3", s)
    s = re.sub(r"(四季度|4季度|q4|第四季度)", "q4", s)
    return s.replace("季", "")


def previous_quarter(period: str) -> str:
    key = normalize_quarter(period)
    match = re.fullmatch(r"(\d{4})q([1-4])", key)
    if not match:
        raise ValueError(f"unsupported quarter label: {period}")
    year = int(match.group(1))
    quarter = int(match.group(2))
    if quarter == 1:
        return f"{year - 1}q4"
    return f"{year}q{quarter - 1}"


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "是", "在招", "招聘中"}


def _looks_like_local_path(value: Any) -> bool:
    return bool(LOCAL_PATH_RE.search(str(value or "")))


def _looks_like_raw_url(value: Any) -> bool:
    return bool(RAW_URL_RE.search(str(value or "")))


def _display_text(evidence: dict[str, Any]) -> str:
    return str(evidence.get("display") or evidence.get("label") or evidence.get("title") or "").strip()


def _image_embed_planned_or_verified(evidence: dict[str, Any]) -> bool:
    return any(
        [
            _truthy(evidence.get("embed")),
            _truthy(evidence.get("embedded")),
            _truthy(evidence.get("pasteIntoDingteam")),
            _truthy(evidence.get("uploaded")),
            _truthy(evidence.get("dingteamEmbedded")),
            bool(evidence.get("attachmentId")),
            bool(evidence.get("dingteamImageUrl")),
        ]
    )


def _presentation_verified(evidence: dict[str, Any]) -> bool:
    return any(
        [
            _truthy(evidence.get("postWriteVerified")),
            _truthy(evidence.get("verifiedInDingteam")),
            _truthy(evidence.get("dingteamLinkVerified")),
            _truthy(evidence.get("dingteamImageVisible")),
            str(evidence.get("presentationStatus") or "").strip().lower() == "verified",
        ]
    )


def compute_recruiting_ratio(records: list[dict[str, Any]], period: str) -> dict[str, Any]:
    """Compute the Q recruiting OKR ratio from HC/position-slot records.

    Expected fields per record:
      - title/jobTitle/name: human-readable role
      - slotId/hcSlotId/jobId: stable id when available
      - priority: optional P0/P1
      - keyRole: optional bool/name for key-role subsets
      - currentQuarterRecruiting / recruiting / status: denominator signal
      - offerQuarter / onboardQuarter: quarter label for exclusion/numerator

    Job-level aggregates are allowed, but rows without enough slot-level fields
    are reported as gaps instead of forced into the ratio.
    """
    current = normalize_quarter(period)
    previous = previous_quarter(period)
    numerator: list[dict[str, Any]] = []
    denominator: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    gaps: list[str] = []

    for idx, raw in enumerate(records):
        row = dict(raw)
        title = row.get("title") or row.get("jobTitle") or row.get("name") or f"row-{idx + 1}"
        slot_id = row.get("slotId") or row.get("hcSlotId") or row.get("jobId") or ""
        offer_q = normalize_quarter(row.get("offerQuarter") or row.get("offer_q") or "")
        onboard_q = normalize_quarter(row.get("onboardQuarter") or row.get("onboard_q") or "")
        status = str(row.get("status") or "")
        recruiting = (
            _truthy(row.get("currentQuarterRecruiting"))
            or _truthy(row.get("recruiting"))
            or any(word in status for word in ["招聘中", "待入职", "面试", "offer", "在招"])
        )

        if not slot_id and not (offer_q or onboard_q or status or row.get("currentQuarterRecruiting") is not None):
            gaps.append(f"{title}: 缺少 HC/岗位槽位状态，不能纳入本季度口径计算")
            continue

        normalized = {
            "slotId": slot_id,
            "title": title,
            "priority": row.get("priority", ""),
            "keyRole": row.get("keyRole", ""),
            "status": status,
            "offerQuarter": offer_q,
            "onboardQuarter": onboard_q,
        }

        if offer_q == previous or onboard_q == previous:
            excluded.append({**normalized, "reason": "上季度已 offer/入职"})
            continue
        if recruiting or onboard_q == current:
            denominator.append(normalized)
        if onboard_q == current:
            numerator.append(normalized)

    rate = None if not denominator else round(len(numerator) / len(denominator) * 100, 2)
    return {
        "period": current,
        "previousPeriod": previous,
        "numerator": len(numerator),
        "denominator": len(denominator),
        "rate": rate,
        "status": "ok" if denominator else "insufficient_denominator",
        "includedNumerator": numerator,
        "includedDenominator": denominator,
        "excludedPreviousQuarter": excluded,
        "gaps": gaps,
    }


def _okr_kr_ids(okr: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    processed = okr.get("processed") if isinstance(okr.get("processed"), dict) else okr
    for objective in processed.get("objectives", []) if isinstance(processed, dict) else []:
        for kr in objective.get("keyResults", []) if isinstance(objective, dict) else []:
            kr_id = kr.get("keyResultId") or kr.get("krId") or kr.get("id")
            if kr_id:
                ids.add(str(kr_id))
    for row in processed.get("okrRows", []) if isinstance(processed, dict) else []:
        if row.get("level") == "KR" and row.get("krId"):
            ids.add(str(row["krId"]))
    return ids


def validate_plan(plan: dict[str, Any], okr: dict[str, Any] | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    valid_ids = _okr_kr_ids(okr) if okr else set()

    updates = plan.get("updates")
    if not isinstance(updates, list) or not updates:
        errors.append("plan.updates must be a non-empty list")
        updates = []

    seen: set[str] = set()
    for idx, item in enumerate(updates, 1):
        if not isinstance(item, dict):
            errors.append(f"updates[{idx}] must be an object")
            continue
        kr_id = str(item.get("krId") or "")
        if not kr_id:
            errors.append(f"updates[{idx}] missing krId")
        elif kr_id in seen:
            errors.append(f"duplicate krId: {kr_id}")
        seen.add(kr_id)
        if valid_ids and kr_id and kr_id not in valid_ids:
            errors.append(f"krId not found in live OKR: {kr_id}")

        progress = item.get("progress")
        if not isinstance(progress, (int, float)) or isinstance(progress, bool):
            errors.append(f"{kr_id or 'updates[' + str(idx) + ']'} progress must be numeric")
        elif progress < 0 or progress > 100:
            errors.append(f"{kr_id} progress must be between 0 and 100")

        note = sanitize_text(item.get("note"))
        if not note:
            errors.append(f"{kr_id or 'updates[' + str(idx) + ']'} missing note")
        elif note != str(item.get("note", "")).strip():
            warnings.append(f"{kr_id or 'updates[' + str(idx) + ']'} note contains text that will be redacted")

        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            warnings.append(f"{kr_id or 'updates[' + str(idx) + ']'} has no evidence list")
        for ev_idx, evidence_item in enumerate(evidence or [], 1):
            if not isinstance(evidence_item, dict):
                warnings.append(f"{kr_id} evidence[{ev_idx}] is not an object")
                continue
            if not evidence_item.get("summary") and not evidence_item.get("url") and not evidence_item.get("path"):
                warnings.append(f"{kr_id} evidence[{ev_idx}] lacks summary/url/path")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def validate_presentation(plan: dict[str, Any]) -> dict[str, Any]:
    """Check manager-visible evidence presentation.

    Local paths are fine in audit JSON, but the Dingteam-visible evidence should
    be represented as inline images or readable rich links. This validator flags
    plans that still rely on local-only paths or raw URLs without labels.
    """
    errors: list[str] = []
    warnings: list[str] = []
    updates = plan.get("updates") if isinstance(plan, dict) else None
    if not isinstance(updates, list):
        errors.append("plan.updates must be a list")
        updates = []

    for idx, item in enumerate(updates, 1):
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or item.get("krId") or f"updates[{idx}]")
        visible_text = "\n".join(
            str(item.get(key) or "") for key in ("note", "risk", "nextStep")
        )
        if LOCAL_PATH_RE.search(visible_text):
            errors.append(f"{label} visible text contains a local path; paste/upload the image or use a named rich link")
        if RAW_URL_RE.search(visible_text):
            warnings.append(f"{label} visible text contains a raw URL; prefer a named rich link")

        for ev_idx, evidence in enumerate(item.get("evidence") or [], 1):
            if not isinstance(evidence, dict):
                continue
            display = _display_text(evidence)
            path = str(evidence.get("path") or "")
            url = str(evidence.get("url") or "")
            if display and (_looks_like_local_path(display) or _looks_like_raw_url(display)):
                errors.append(f"{label} evidence[{ev_idx}] display/label/title must be a readable title, not a path or URL")
            if path and LOCAL_PATH_RE.search(path):
                suffix = Path(path.split("?", 1)[0].split("#", 1)[0]).suffix.lower()
                if suffix and suffix not in IMAGE_EXTENSIONS:
                    warnings.append(f"{label} evidence[{ev_idx}] local path does not look like a supported image file")
                if not _image_embed_planned_or_verified(evidence):
                    errors.append(
                        f"{label} evidence[{ev_idx}] uses local path without embed/pasteIntoDingteam/uploaded evidence"
                    )
                if not display:
                    errors.append(f"{label} evidence[{ev_idx}] local image evidence needs display/label/title")
                elif _image_embed_planned_or_verified(evidence) and not _presentation_verified(evidence):
                    warnings.append(
                        f"{label} evidence[{ev_idx}] image is only planned for paste/upload; verify it renders after writeback"
                    )
            if url:
                if not display:
                    errors.append(f"{label} evidence[{ev_idx}] url needs display/label/title for named rich link")
                elif not _presentation_verified(evidence):
                    warnings.append(f"{label} evidence[{ev_idx}] link title is planned; verify href after writeback")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def _render_evidence_pointer(evidence: dict[str, Any]) -> str:
    display = _display_text(evidence)
    summary = evidence.get("summary") or evidence.get("type") or "证据"
    path = str(evidence.get("path") or "")
    url = str(evidence.get("url") or "")
    if path and _looks_like_local_path(path):
        if display and _image_embed_planned_or_verified(evidence):
            return f"- {summary}: {display}（写回时内嵌图片）"
        return f"- {summary}: 待补内嵌截图"
    if url:
        if display:
            return f"- {summary}: [{display}]({url})"
        return f"- {summary}: 待补可读链接"
    pointer = evidence.get("source") or display or "待补链接/截图"
    if _looks_like_local_path(pointer) or _looks_like_raw_url(pointer):
        return f"- {summary}: 待补可读链接/截图"
    return f"- {summary}: {pointer}"


def render_markdown(plan: dict[str, Any], okr: dict[str, Any] | None = None) -> str:
    sanitized = sanitize_obj(plan)
    lines = [
        f"# {sanitized.get('title') or 'OKR Progress Draft'}",
        "",
        f"- 周期: {sanitized.get('period') or '未注明'}",
        f"- 目标用户: {sanitized.get('targetUser') or '当前用户'}",
        f"- 生成时间: {sanitized.get('generatedAt') or '未注明'}",
        "",
    ]
    validation = validate_plan(sanitized, okr)
    lines.extend(["## 校验", ""])
    lines.append(f"- 状态: {'通过' if validation['ok'] else '未通过'}")
    for err in validation["errors"]:
        lines.append(f"- 错误: {err}")
    for warn in validation["warnings"]:
        lines.append(f"- 提醒: {warn}")
    lines.append("")

    lines.extend(["## KR 更新草稿", ""])
    for idx, item in enumerate(sanitized.get("updates", []), 1):
        lines.append(f"### {idx}. {item.get('label') or item.get('krTitle') or item.get('krId')}")
        lines.append("")
        lines.append(f"- krId: `{item.get('krId', '')}`")
        lines.append(f"- 建议进度: {item.get('progress', '')}%")
        lines.append("")
        lines.append("进展说明草稿:")
        lines.append("")
        lines.append(str(item.get("note", "")).strip())
        lines.append("")
        lines.append("证据链接/截图:")
        evidence = item.get("evidence") or []
        if evidence:
            for ev in evidence:
                lines.append(_render_evidence_pointer(ev))
        else:
            lines.append("- 待补链接/截图")
        risk = item.get("risk")
        next_step = item.get("nextStep")
        confidence = item.get("confidence")
        if risk:
            lines.append(f"- 未完成/风险: {risk}")
        if next_step:
            lines.append(f"- 下阶段计划: {next_step}")
        if confidence:
            lines.append(f"- 置信度: {confidence}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def cmd_sanitize(args: argparse.Namespace) -> int:
    text = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
    print(sanitize_text(text))
    return 0


def cmd_recruiting_ratio(args: argparse.Namespace) -> int:
    data = load_json(args.input)
    records = data.get("records", data) if isinstance(data, dict) else data
    if not isinstance(records, list):
        raise SystemExit("input must be a list or an object with records")
    print(dump_json(compute_recruiting_ratio(records, args.period)))
    return 0


def cmd_validate_plan(args: argparse.Namespace) -> int:
    plan = load_json(args.plan)
    okr = load_json(args.okr) if args.okr else None
    result = validate_plan(plan, okr)
    print(dump_json(result))
    return 0 if result["ok"] else 1


def cmd_validate_presentation(args: argparse.Namespace) -> int:
    plan = load_json(args.plan)
    result = validate_presentation(plan)
    print(dump_json(result))
    return 0 if result["ok"] else 1


def cmd_render_markdown(args: argparse.Namespace) -> int:
    plan = load_json(args.plan)
    okr = load_json(args.okr) if args.okr else None
    markdown = render_markdown(plan, okr)
    if args.output:
        Path(args.output).write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sanitize = sub.add_parser("sanitize-text", help="redact sensitive visible text")
    sanitize.add_argument("--input", help="input text path; stdin when omitted")
    sanitize.set_defaults(func=cmd_sanitize)

    ratio = sub.add_parser("recruiting-ratio", help="compute quarter hiring ratio")
    ratio.add_argument("--input", required=True, help="JSON records path")
    ratio.add_argument("--period", required=True, help="quarter label, e.g. 2026年3季度")
    ratio.set_defaults(func=cmd_recruiting_ratio)

    validate = sub.add_parser("validate-plan", help="validate a writeback plan")
    validate.add_argument("--plan", required=True, help="progress plan JSON")
    validate.add_argument("--okr", help="live OKR JSON for krId matching")
    validate.set_defaults(func=cmd_validate_plan)

    presentation = sub.add_parser("validate-presentation", help="validate manager-visible evidence presentation")
    presentation.add_argument("--plan", required=True, help="progress plan JSON")
    presentation.set_defaults(func=cmd_validate_presentation)

    render = sub.add_parser("render-markdown", help="render plan as review Markdown")
    render.add_argument("--plan", required=True, help="progress plan JSON")
    render.add_argument("--okr", help="live OKR JSON for krId matching")
    render.add_argument("--output", help="output Markdown path")
    render.set_defaults(func=cmd_render_markdown)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
