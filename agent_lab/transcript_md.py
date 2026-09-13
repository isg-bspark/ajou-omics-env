#!/usr/bin/env python3
"""Claude Code 세션 기록(JSONL)을 읽기 쉬운 Markdown 으로 바꿉니다 (강사용 · 리허설 분석).

    python3 agent_lab/transcript_md.py ~/.claude/projects/<프로젝트>/<세션>.jsonl > run.md
    python3 agent_lab/transcript_md.py --latest > run.md          # 현재 폴더 프로젝트의 최신 세션

사용자 프롬프트 · Claude 텍스트 · 도구 호출(이름 + 입력) · 도구 결과(앞부분) · 시각을 순서대로 적습니다.
JSONL 형식은 Claude Code 내부 형식이라 버전마다 바뀔 수 있어, 모르는 항목은 건너뜁니다.
"""
import argparse, json, os, re, sys, glob, unicodedata
from datetime import datetime

MAX_RESULT = 1500   # 도구 결과는 이 길이까지만
MAX_INPUT = 800


def project_dir_for_cwd():
    cwd = unicodedata.normalize("NFC", os.getcwd())          # macOS 는 경로를 NFD 로 돌려줘 한글이 쪼개짐
    slug = re.sub(r"[^A-Za-z0-9]", "-", cwd)
    d = os.path.expanduser(f"~/.claude/projects/{slug}")
    if os.path.isdir(d):
        return d
    # 못 찾으면 마지막 폴더 이름으로 끝나는 프로젝트 중 최근 것
    tail = re.sub(r"[^A-Za-z0-9]", "-", os.path.basename(cwd))
    cands = [x for x in glob.glob(os.path.expanduser("~/.claude/projects/*")) if x.endswith(tail)]
    return max(cands, key=os.path.getmtime) if cands else d


def latest_jsonl():
    files = glob.glob(os.path.join(project_dir_for_cwd(), "*.jsonl"))
    if not files:
        sys.exit(f"세션 파일이 없습니다: {project_dir_for_cwd()}")
    return max(files, key=os.path.getmtime)


def ts(entry):
    t = entry.get("timestamp")
    if not t:
        return ""
    try:
        return datetime.fromisoformat(t.replace("Z", "+00:00")).astimezone().strftime("%H:%M:%S")
    except Exception:
        return str(t)[:19]


def clip(s, n):
    s = s if isinstance(s, str) else json.dumps(s, ensure_ascii=False, indent=1)
    return s if len(s) <= n else s[:n] + f"\n… ({len(s) - n}자 생략)"


def result_text(block):
    c = block.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")
    return json.dumps(c, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?")
    ap.add_argument("--latest", action="store_true")
    ap.add_argument("--full", action="store_true", help="도구 결과를 자르지 않음")
    a = ap.parse_args()
    path = latest_jsonl() if (a.latest or not a.path) else a.path
    max_result = 10**9 if a.full else MAX_RESULT

    print(f"# 세션 기록\n\n`{path}`\n")
    n_tools = 0
    tool_names = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                e = json.loads(line)
            except Exception:
                continue
            kind = e.get("type")
            msg = e.get("message") or {}
            content = msg.get("content")
            if kind == "user":
                if isinstance(content, str):
                    print(f"\n---\n## 👤 사용자  `{ts(e)}`\n\n{content.strip()}\n")
                elif isinstance(content, list):
                    for b in content:
                        if not isinstance(b, dict):
                            continue
                        if b.get("type") == "text":
                            print(f"\n---\n## 👤 사용자  `{ts(e)}`\n\n{b.get('text','').strip()}\n")
                        elif b.get("type") == "tool_result":
                            err = " ⚠ error" if b.get("is_error") else ""
                            print(f"\n**↳ 도구 결과{err}** `{ts(e)}`\n\n```\n{clip(result_text(b), max_result)}\n```\n")
            elif kind == "assistant" and isinstance(content, list):
                for b in content:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "text" and b.get("text", "").strip():
                        print(f"\n### 🤖 Claude  `{ts(e)}`\n\n{b['text'].strip()}\n")
                    elif b.get("type") == "tool_use":
                        n_tools += 1
                        name = b.get("name", "?")
                        tool_names[name] = tool_names.get(name, 0) + 1
                        print(f"\n**🔧 도구 호출 #{n_tools}: `{name}`** `{ts(e)}`\n\n```json\n{clip(b.get('input', {}), MAX_INPUT)}\n```\n")
    print("\n---\n## 요약\n")
    print(f"- 도구 호출 {n_tools}회")
    for k, v in sorted(tool_names.items(), key=lambda kv: -kv[1]):
        print(f"  - `{k}` × {v}")


if __name__ == "__main__":
    main()
