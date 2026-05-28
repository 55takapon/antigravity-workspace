#!/usr/bin/env python3
"""skill-update 用の静的 review.html を生成する。"""

from __future__ import annotations

import argparse
import html
import json
import logging
import sys
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)


def configure_logging() -> None:
    """標準出力向けロギング設定。"""
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)


def load_json(path: Path) -> dict[str, Any]:
    """JSON ファイルを辞書として読み込む。"""
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON の最上位が辞書ではありません: {path}")
    return data


def read_preview(output_dir: Path) -> str:
    """最初に見つかったテキストファイルの冒頭を返す。"""
    if not output_dir.is_dir():
        return "出力ファイルなし"
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".txt", ".json", ".html"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        return text[:1200]
    return "テキストプレビュー対象なし"


def render_expectations(expectations: list[dict[str, Any]]) -> str:
    """expectations テーブルを HTML 化する。"""
    if not expectations:
        return "<p>判定結果なし</p>"

    rows = []
    for item in expectations:
        status = "pass" if bool(item.get("passed")) else "fail"
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('text', '')))}</td>"
            f"<td>{status}</td>"
            f"<td>{html.escape(str(item.get('evidence', '')))}</td>"
            "</tr>"
        )

    return (
        "<table>"
        "<thead><tr><th>条件</th><th>判定</th><th>根拠</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def render_eval_card(eval_dir: Path, config_name: str) -> str:
    """評価ケースの HTML カードを生成する。"""
    config_dir = eval_dir / config_name
    if not config_dir.is_dir():
        return ""

    metadata = load_json(eval_dir / "eval_metadata.json")
    grading = load_json(config_dir / "grading.json") if (config_dir / "grading.json").is_file() else {}
    expectations = grading.get("expectations", [])
    if not isinstance(expectations, list):
        expectations = []

    preview = read_preview(config_dir / "outputs")
    summary = str(grading.get("summary", "要約なし"))
    return (
        '<section class="card">'
        f"<h3>{html.escape(str(metadata.get('eval_name', eval_dir.name)))} / {html.escape(config_name)}</h3>"
        f"<p><strong>Prompt:</strong> {html.escape(str(metadata.get('prompt', '')))}</p>"
        f"<p><strong>Expected:</strong> {html.escape(str(metadata.get('expected_output', '')))}</p>"
        f"<p><strong>Summary:</strong> {html.escape(summary)}</p>"
        f"{render_expectations(expectations)}"
        f"<pre>{html.escape(preview)}</pre>"
        "</section>"
    )


def render_benchmark(benchmark: dict[str, Any]) -> str:
    """benchmark セクションを HTML 化する。"""
    rows = []
    for config in benchmark.get("configs", []):
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(config.get('label', config.get('name', ''))))}</td>"
            f"<td>{config.get('eval_count', 0)}</td>"
            f"<td>{config.get('pass_rate', 0.0)}</td>"
            f"<td>{config.get('mean_tokens', 0.0)}</td>"
            f"<td>{config.get('mean_duration_seconds', 0.0)}</td>"
            "</tr>"
        )

    comparison_rows = []
    for item in benchmark.get("comparisons", []):
        comparison_rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('name', '')))}</td>"
            f"<td>{item.get('pass_rate_delta', 0.0)}</td>"
            f"<td>{item.get('mean_tokens_delta', 0.0)}</td>"
            f"<td>{item.get('mean_duration_seconds_delta', 0.0)}</td>"
            f"<td>{item.get('regression_detected', False)}</td>"
            "</tr>"
        )

    comparison_html = ""
    if comparison_rows:
        comparison_html = (
            "<h2>差分</h2>"
            "<table><thead><tr><th>比較</th><th>pass率差分</th><th>tokens差分</th>"
            "<th>秒数差分</th><th>回帰</th></tr></thead>"
            f"<tbody>{''.join(comparison_rows)}</tbody></table>"
        )

    return (
        "<h2>Benchmark</h2>"
        "<table><thead><tr><th>設定</th><th>eval数</th><th>pass率</th>"
        "<th>平均tokens</th><th>平均秒数</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        f"{comparison_html}"
    )


def render_page(iteration_dir: Path, benchmark: dict[str, Any]) -> str:
    """HTML 全体を組み立てる。"""
    cards = []
    for eval_dir in sorted(iteration_dir.iterdir()):
        if not eval_dir.is_dir() or not (eval_dir / "eval_metadata.json").is_file():
            continue
        for config_name in ("with_skill", "old_skill", "without_skill"):
            card = render_eval_card(eval_dir, config_name)
            if card:
                cards.append(card)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <title>skill-update review</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", sans-serif;
      margin: 24px auto;
      max-width: 1200px;
      line-height: 1.6;
      color: #1f2937;
      background: #f8fafc;
      padding: 0 16px 40px;
    }}
    h1, h2 {{ color: #0f172a; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 16px;
    }}
    .card {{
      background: white;
      border: 1px solid #dbe4ee;
      border-radius: 14px;
      padding: 16px;
      box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 12px 0 16px;
      background: white;
    }}
    th, td {{
      border: 1px solid #dbe4ee;
      padding: 8px;
      vertical-align: top;
    }}
    th {{
      background: #e0f2fe;
    }}
    pre {{
      white-space: pre-wrap;
      word-break: break-word;
      background: #0f172a;
      color: #e2e8f0;
      border-radius: 10px;
      padding: 12px;
      overflow: auto;
    }}
  </style>
</head>
<body>
  <h1>skill-update review</h1>
  <p><strong>iteration:</strong> {html.escape(str(iteration_dir))}</p>
  {render_benchmark(benchmark)}
  <h2>ケース別レビュー</h2>
  <div class="grid">
    {''.join(cards)}
  </div>
</body>
</html>
"""


def main() -> int:
    """CLI エントリポイント。"""
    configure_logging()
    parser = argparse.ArgumentParser(description="Generate static HTML review for skill-update")
    parser.add_argument("iteration_dir", help="iteration-N のパス")
    parser.add_argument("--benchmark", help="benchmark.json のパス")
    parser.add_argument("--output", help="review.html の出力先")
    args = parser.parse_args()

    iteration_dir = Path(args.iteration_dir).resolve()
    benchmark_path = Path(args.benchmark).resolve() if args.benchmark else iteration_dir / "benchmark.json"
    output_path = Path(args.output).resolve() if args.output else iteration_dir / "review.html"

    try:
        benchmark = load_json(benchmark_path)
        html_text = render_page(iteration_dir, benchmark)
        output_path.write_text(html_text, encoding="utf-8")
    except (FileNotFoundError, OSError, ValueError) as exc:
        LOGGER.error("エラー: %s", exc)
        return 1

    LOGGER.info("review.html を出力しました: %s", output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
