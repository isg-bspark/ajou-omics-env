#!/usr/bin/env python3
"""
환경 점검 — 실습 전에 한 번 돌리세요.

    python3 agent_lab/verify.py

'환경' 만 봅니다. .mcp.json 은 실습에서 직접 채우므로 검사하지 않습니다.
"""
import os
import re
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
        return True          # 응답이 왔으면 망은 열린 것
    except Exception:
        return False


def gh_version():
    """(major, minor) 또는 None."""
    exe = shutil.which("gh")
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=8).stdout
        m = re.search(r"gh version (\d+)\.(\d+)", out)
        return (int(m.group(1)), int(m.group(2))) if m else None
    except Exception:
        return None


def main() -> int:
    print("\n환경 점검\n")

    v = sys.version_info
    check("Python 3.10 이상", v >= (3, 10), f"{v.major}.{v.minor}.{v.micro}",
          "Python 3.10 이상이 필요합니다 (mcp 패키지 요구사항)")

    try:
        import importlib.metadata as md
        check("mcp 패키지", True, f"v{md.version('mcp')}")
    except Exception:
        check("mcp 패키지", False, "없음", 'python3 -m pip install "mcp[cli]"')

    claude = shutil.which("claude")
    check("claude 명령", claude is not None, claude or "PATH 에 없음",
          "curl -fsSL https://claude.ai/install.sh | bash  후 새 터미널")

    # ── 실습 4단계(스킬 설치) 용 — gh 2.90+ 또는 node(npx) 중 하나면 됩니다 ──
    gv = gh_version()
    gh_ok = gv is not None and gv >= (2, 90)
    check("gh 2.90+  (실습 4 · 스킬)", gh_ok,
          (f"v{gv[0]}.{gv[1]}" if gv else "없음"),
          "gh 2.90+ 가 있으면 gh skill 을 씁니다. 없으면 아래 node(npx) 로도 됩니다",
          warn_only=True)

    node = shutil.which("node")
    check("node / npx  (실습 4 대체 경로)", node is not None, node or "없음",
          "gh 2.90+ 가 없을 때 'npx skills add …' 로 설치합니다",
          warn_only=True)

    if not gh_ok and node is None:
        warns.append("실습 4단계 준비\n      → gh 2.90+ 또는 node 중 하나는 있어야 스킬을 설치합니다")

    check("바깥 인터넷 (실습 3 · OLS)",
          reachable("https://www.ebi.ac.uk/ols4/api/mcp"), "",
          "네트워크 정책일 수 있습니다. 실습 3의 원격 부분은 건너뛰어도 됩니다",
          warn_only=True)

    env_key = os.environ.get("ANTHROPIC_API_KEY")
    logged_in = os.path.exists(os.path.expanduser("~/.claude.json"))
    check("Claude Code 인증", bool(env_key or logged_in),
          "ANTHROPIC_API_KEY 있음" if env_key
          else "설정 파일 있음 — 첫 실행 때 확인됩니다" if logged_in
          else "아직 없음 — claude 를 실행하면 안내가 나옵니다",
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
    print("\033[32m준비 완료.  README_agentlab.md 의 1단계로 가세요.\033[0m\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
