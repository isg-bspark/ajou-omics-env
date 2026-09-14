#!/usr/bin/env python3
"""리포트 HTML 의 그림을 파일 안으로 집어넣어 단일 파일로 만든다.

Codespace 웹 편집기에서 리포트를 우클릭 → Show Preview 로 볼 때는 상대 경로
그림도 보이지만, 학생이 그 HTML 만 내려받으면 그림이 전부 깨진다. 그림을
data URI 로 본문에 박아 두면 다운로드한 파일 하나로 어디서든 열린다.

사용법:
    python tools/build_report.py results/summary/report.html
    python tools/build_report.py results/summary/report.html -o /tmp/report.html

-o 를 주지 않으면 <이름>_standalone.html 로 옆에 쓴다. 원본은 건드리지 않는다.
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
import re
import sys
from pathlib import Path
from urllib.parse import unquote

# <img src="..."> 와 CSS 의 url(...) 둘 다 잡는다.
IMG_SRC = re.compile(r"""(<img\b[^>]*?\bsrc\s*=\s*)(["'])(.*?)\2""", re.IGNORECASE | re.DOTALL)
CSS_URL = re.compile(r"""(url\()\s*(["']?)(.*?)\2\s*(\))""", re.IGNORECASE)

SKIP_PREFIXES = ("data:", "http://", "https://", "//", "#")


def _to_data_uri(raw: str, base: Path, missing: list[str]) -> str | None:
    """상대 경로 하나를 data URI 로 바꾼다. 못 바꾸면 None 을 돌려준다."""
    if not raw or raw.startswith(SKIP_PREFIXES):
        return None

    path = (base / unquote(raw.split("?", 1)[0].split("#", 1)[0])).resolve()
    if not path.is_file():
        missing.append(raw)
        return None

    mime, _ = mimetypes.guess_type(path.name)
    if mime is None or not (mime.startswith("image/") or mime == "image/svg+xml"):
        mime = "application/octet-stream"

    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def inline_assets(html: str, base: Path) -> tuple[str, int, list[str]]:
    """html 안의 상대 경로 그림을 data URI 로 치환한다."""
    embedded = 0
    missing: list[str] = []

    def repl_img(m: re.Match[str]) -> str:
        nonlocal embedded
        uri = _to_data_uri(m.group(3), base, missing)
        if uri is None:
            return m.group(0)
        embedded += 1
        return f"{m.group(1)}{m.group(2)}{uri}{m.group(2)}"

    def repl_css(m: re.Match[str]) -> str:
        nonlocal embedded
        uri = _to_data_uri(m.group(3), base, missing)
        if uri is None:
            return m.group(0)
        embedded += 1
        return f'{m.group(1)}"{uri}"{m.group(4)}'

    html = IMG_SRC.sub(repl_img, html)
    html = CSS_URL.sub(repl_css, html)
    return html, embedded, missing


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", type=Path, help="리포트 HTML 경로")
    ap.add_argument("-o", "--output", type=Path, default=None, help="출력 경로 (기본: <이름>_standalone.html)")
    args = ap.parse_args()

    src: Path = args.html
    if not src.is_file():
        print(f"ERROR: 파일이 없다 — {src}", file=sys.stderr)
        return 1

    out: Path = args.output or src.with_name(f"{src.stem}_standalone.html")
    if out.resolve() == src.resolve():
        print("ERROR: 출력 경로가 원본과 같다. 원본은 덮어쓰지 않는다.", file=sys.stderr)
        return 1

    html, embedded, missing = inline_assets(src.read_text(encoding="utf-8"), src.parent)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    size_mb = out.stat().st_size / 1024 / 1024
    print(f"그림 {embedded}개를 본문에 넣었다 → {out.resolve()} ({size_mb:.1f} MB)")

    if missing:
        # 조용히 넘어가면 깨진 리포트를 완성본으로 착각하게 된다.
        print(f"WARN: 파일을 못 찾아 그대로 둔 참조 {len(missing)}개 — 이 그림은 깨진다:", file=sys.stderr)
        for ref in missing:
            print(f"  - {ref}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
