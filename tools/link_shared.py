#!/usr/bin/env python3
"""공유 경로를 worktree 에서 main 쪽 심볼릭 링크로 바꾼다.

두 번 호출된다.
  1) 인자 없이   — 공유 경로를 skip-worktree 로 표시 (checkout-index 전)
  2) --link 로   — 실제 심볼릭 링크 생성 (checkout-index 후)

파일 단위로 링크를 건다. 디렉토리를 통째로 링크하면 git 이 그 디렉토리를
untracked 로 보고 status 에 남기 때문이다.
"""
import os
import subprocess
import sys


def tracked(worktree, paths):
    # -z: NUL-separated, unquoted paths — without it git quotes/octal-escapes
    # non-ASCII filenames (e.g. 한글) whenever core.quotepath is at its default,
    # which corrupts every path built from the split-by-line output below.
    out = subprocess.run(["git", "-C", worktree, "ls-files", "-z", "--", *paths],
                         capture_output=True, text=True, check=True).stdout
    return [f for f in out.split("\0") if f]


def main(argv):
    link = argv and argv[0] == "--link"
    if link:
        argv = argv[1:]
    root, worktree, shared = argv[0], argv[1], argv[2:]

    files = tracked(worktree, shared)
    if not files:
        return

    if not link:
        subprocess.run(["git", "-C", worktree, "update-index", "--skip-worktree", *files],
                       check=True)
        return

    for f in files:
        dst = os.path.join(worktree, f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        rel = os.path.relpath(os.path.join(root, f), os.path.dirname(dst))
        if os.path.lexists(dst):
            os.remove(dst)
        os.symlink(rel, dst)


if __name__ == "__main__":
    main(sys.argv[1:])
