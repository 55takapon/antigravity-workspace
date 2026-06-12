#!/usr/bin/env python3
"""description 改善候補を生成する。"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)
FRONTMATTER_PATTERN = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
DESCRIPTION_PATTERN = re.compile(r"^description:\s*>-\n((?:\s{2}.+\n?)*)", re.MULTILINE)


def configure_logging() -> None:
    """標準出力向けロガー設定。"""
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)


def load_json(path: Path) -> dict[str, Any]:
    """JSON ファイルを辞書として読む。"""
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON の最上位が辞書ではありません: {path}")
    return data


def read_skill(skill_path: Path) -> tuple[str, str]:
    """SKILL.md 全文と description を返す。"""
    skill_md = skill_path / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    frontmatter_match = FRONTMATTER_PATTERN.match(text)
    if not frontmatter_match:
        raise ValueError("SKILL.md に frontmatter がありません")

    description_match = DESCRIPTION_PATTERN.search(frontmatter_match.group(0))
    if not description_match:
        raise ValueError("description が見つかりません")

    description = " ".join(line.strip() for line in description_match.group(1).splitlines())
    return text, description.strip()


def build_query_examples(queries: list[dict[str, Any]], should_trigger: bool) -> list[str]:
    """トリガー例または除外例を取り出す。"""
    results = []
    for item in queries:
        if bool(item.get("should_trigger")) is not should_trigger:
            continue
        text = str(item.get("text", "")).strip()
        if text:
            results.append(text)
    return results


def unique_examples(examples: list[str], current_description: str, limit: int) -> list[str]:
    """description にまだ入っていない例を上限付きで抽出する。"""
    results = []
    for example in examples:
        if example in current_description or example in results:
            continue
        results.append(example)
        if len(results) >= limit:
            break
    return results


def build_candidate(description: str, trigger_examples: list[str], exclude_examples: list[str]) -> str:
    """改善候補の description を組み立てる。"""
    candidate = description
    if trigger_examples:
        candidate += " 「" + "」「".join(trigger_examples) + "」等の指示でも必ず使用する。"
    if exclude_examples:
        candidate += " 「" + "」「".join(exclude_examples) + "」等の通常会話では使用しない。"
    return candidate.strip()


def write_report(path: Path, payload: dict[str, Any]) -> None:
    """JSON レポートを書き出す。"""
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def maybe_write_skill(skill_path: Path, original_text: str, old_description: str, new_description: str) -> None:
    """description を実際に書き換える。"""
    skill_md = skill_path / "SKILL.md"
    replacement = f"description: >-\n  {new_description}\n"
    updated = re.sub(
        r"description:\s*>-\n(?:\s{2}.+\n?)+",
        replacement,
        original_text,
        count=1,
    )
    skill_md.write_text(updated, encoding="utf-8")
    LOGGER.info("description を更新しました: %s", skill_md)
    LOGGER.info("変更前: %s", old_description)
    LOGGER.info("変更後: %s", new_description)


def main() -> int:
    """CLI エントリポイント。"""
    configure_logging()
    parser = argparse.ArgumentParser(description="Generate description improvements for skill-update")
    parser.add_argument("--skill", required=True, help="対象スキルディレクトリ")
    parser.add_argument("--queries", required=True, help="trigger/non-trigger クエリ JSON")
    parser.add_argument("--output", help="改善レポートの出力先")
    parser.add_argument("--write", action="store_true", help="SKILL.md の description を更新する")
    parser.add_argument("--max-triggers", type=int, default=4, help="追加する trigger 例の上限")
    parser.add_argument("--max-excludes", type=int, default=2, help="追加する除外例の上限")
    args = parser.parse_args()

    skill_path = Path(args.skill).resolve()
    queries_path = Path(args.queries).resolve()
    output_path = Path(args.output).resolve() if args.output else queries_path.with_name("description-review.json")

    try:
        original_text, current_description = read_skill(skill_path)
        query_payload = load_json(queries_path)
        queries = query_payload.get("queries", [])
        if not isinstance(queries, list):
            raise ValueError("queries は配列である必要があります")

        trigger_examples = unique_examples(
            build_query_examples(queries, should_trigger=True),
            current_description,
            args.max_triggers,
        )
        exclude_examples = unique_examples(
            build_query_examples(queries, should_trigger=False),
            current_description,
            args.max_excludes,
        )
        candidate = build_candidate(current_description, trigger_examples, exclude_examples)
        report = {
            "current_description": current_description,
            "candidate_description": candidate,
            "trigger_examples_added": trigger_examples,
            "exclude_examples_added": exclude_examples,
            "character_count": len(candidate),
        }
        write_report(output_path, report)
        if args.write and candidate != current_description:
            maybe_write_skill(skill_path, original_text, current_description, candidate)
    except (FileNotFoundError, OSError, ValueError) as exc:
        LOGGER.error("エラー: %s", exc)
        return 1

    LOGGER.info("description 改善レポートを出力しました: %s", output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
