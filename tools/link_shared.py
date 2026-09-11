#!/usr/bin/env python3
"""공유 경로를 worktree 에서 main 쪽 심볼릭 링크로 바꾼다.

세 가지 모드가 있다.
  1) 인자 없이   — 공유 경로를 skip-worktree 로 표시 (checkout-index 전)
  2) --link 로   — 실제 심볼릭 링크 생성 (checkout-index 후)
  3) --unlink 로 — 링크를 걷어내고 tracked 내용으로 되돌린다 (skip-worktree 해제)

--unlink 는 이미 만들어 둔 worktree 를 main 최신 커밋으로 갱신하기 전에 쓴다.
skip-worktree 로 표시된 채 심볼릭 링크가 놓여 있으면 merge 가 "local changes"
때문에 거부되기 때문이다. 공유 경로는 실험이 읽기만 하는 파일이므로 링크를
지우고 tracked 내용으로 되돌려도 잃을 것이 없다. merge 뒤에 1)·2) 를 다시
호출하면 새 공유 목록 기준으로 링크가 다시 걸린다.

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


def skipped(worktree):
    """skip-worktree 로 표시된 tracked 파일 전부.

    공유 목록이 바뀐 뒤에는 지금 목록에 없는 옛 경로(예: 루트의 core_markers.xlsx)도
    표시된 채 남아 있다. 그것까지 걷어내야 merge 가 통과한다.
    """
    out = subprocess.run(["git", "-C", worktree, "ls-files", "-v", "-z"],
                         capture_output=True, text=True, check=True).stdout
    return [e[2:] for e in out.split("\0") if e[:2] == "S "]


def main(argv):
    mode = "skip"
    if argv and argv[0] in ("--link", "--unlink"):
        mode, argv = argv[0][2:], argv[1:]
    root, worktree, shared = argv[0], argv[1], argv[2:]

    files = tracked(worktree, shared)
    if not files and mode != "unlink":
        return

    if mode == "skip":
        subprocess.run(["git", "-C", worktree, "update-index", "--skip-worktree", *files],
                       check=True)
        return

    if mode == "unlink":
        # 지금 공유 목록 + 옛 목록에서 남은 skip-worktree 표시 전부
        files = sorted(set(files) | set(skipped(worktree)))
        if not files:
            return
        subprocess.run(["git", "-C", worktree, "update-index", "--no-skip-worktree", *files],
                       check=True)
        for f in files:
            dst = os.path.join(worktree, f)
            if os.path.islink(dst):
                os.remove(dst)
        # 링크를 지운 자리를 tracked 내용으로 채운다 — 이제 worktree 가 깨끗해져 merge 가 된다
        subprocess.run(["git", "-C", worktree, "checkout", "--", *files], check=True)
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
