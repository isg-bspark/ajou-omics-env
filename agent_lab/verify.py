#!/usr/bin/env python3
"""환경 점검 — 2일차 1교시(agent_lab · PART 3) 실습 전에 한 번 돌립니다.

    python3 agent_lab/verify.py

앞의 ✓ 항목이 준비되면 시작합니다. 뒤의 노란 · 는 있어도 됩니다.
"""
import os
import shutil
import subprocess
import sys
import urllib.request

OK   = "  \033[32m✓\033[0m"
NO   = "  \033[31m✗\033[0m"
WARN = "  \033[33m·\033[0m"
fails: list[str] = []
warns: list[str] = []


def check(name, ok, detail="", fix="", warn_only=False):
    print(f"{OK if ok else (WARN if warn_only else NO)} {name}"
          f"{('  — ' + detail) if detail else ''}")
    if not ok:
        (warns if warn_only else fails).append(f"{name}\n      → {fix}")
    return ok


def reachable(url, timeout=8):
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except urllib.error.HTTPError:
        return True
    except Exception:
        return False


def gh_version():
    exe = shutil.which("gh")
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=8).stdout
        import re
        m = re.search(r"gh version (\d+)\.(\d+)", out)
        return (int(m.group(1)), int(m.group(2))) if m else None
    except Exception:
        return None


def main() -> int:
    print("\n환경 점검 — 2일차 1교시 (agent_lab · PART 3)\n")

    v = sys.version_info
    check("Python 3.11 이상", v >= (3, 11), f"{v.major}.{v.minor}.{v.micro}",
          "Python 3.11 이상이 필요합니다")

    try:
        import importlib.metadata as md
        check("mcp 패키지 (내 서버 lab-mcp)", True, f"v{md.version('mcp')}")
    except Exception:
        check("mcp 패키지 (내 서버 lab-mcp)", False, "없음", 'pip install "mcp[cli]"')

    try:
        import importlib.metadata as md
        check("scanpy (① QC)", True, f"v{md.version('scanpy')}")
    except Exception:
        check("scanpy (① QC)", False, "없음",
              "이미지 리빌드가 필요합니다 (.devcontainer/requirements.txt)")

    biomcp = shutil.which("biomcp")
    check("biomcp 명령 (② 마커 근거)", biomcp is not None, biomcp or "PATH 에 없음",
          "이미지 리빌드가 필요합니다 (.devcontainer/tools.txt 의 biomcp-python)", warn_only=True)

    claude = shutil.which("claude")
    check("claude 명령", claude is not None, claude or "PATH 에 없음",
          "post-create.sh 가 설치합니다. 새 터미널을 열어보세요")

    gv = gh_version()
    gh_ok = gv is not None and gv >= (2, 90)
    check("gh 2.90+ (① gh skill install)", gh_ok, (f"v{gv[0]}.{gv[1]}" if gv else "없음"),
          "gh 2.90+ 가 있으면 gh skill 을 씁니다. 없으면 part3_setup.sh --with-skill 로도 됩니다",
          warn_only=True)

    check("바깥 인터넷 (②③ · OLS)", reachable("https://www.ebi.ac.uk/ols4/api/mcp"), "",
          "네트워크 정책일 수 있습니다. ③의 CL ID 는 손으로 채워도 됩니다", warn_only=True)

    data = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "pbmc3k_mini.h5ad")
    check("data/pbmc3k_mini.h5ad", os.path.exists(data),
          f"{os.path.getsize(data)//1024} KB" if os.path.exists(data) else "없음",
          "git pull 로 받아오세요")

    env_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    logged_in = os.path.exists(os.path.expanduser("~/.claude.json"))
    check("Claude Code 인증", bool(env_key or logged_in),
          "환경변수 있음" if env_key else "설정 파일 있음" if logged_in else "아직 없음",
          "claude 를 실행하고 안내를 따르세요", warn_only=True)

    print()
    for w in warns:
        print("  ·", w)
    if warns:
        print()
    if fails:
        print(f"\033[31m{len(fails)}개가 준비되지 않았습니다.\033[0m\n")
        for f in fails:
            print("  •", f)
        print()
        return 1
    print("\033[32m준비 완료.  README_agentlab.md 의 ① 로 가세요.\033[0m\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
