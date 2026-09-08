#!/usr/bin/env bash
# 병렬 실험 worktree 와 branch 를 정리한다.
#
#   bash tools/cleanup.sh          # 무엇이 지워지는지 보여주기만 한다
#   bash tools/cleanup.sh --yes    # 실제로 지운다
#
# 주의 — worktree 를 지우면 그 안의 results/ figures/ 도 함께 사라집니다.
#        남기고 싶은 것은 먼저 worktree 밖으로 복사하세요.
set -euo pipefail

# 항상 main 작업 트리를 기준으로 동작한다.
# 이 스크립트 자체는 worktree 에 링크되지 않지만, 실행 위치가 worktree 안일 수 있으므로
# worktree 안에서 실행했을 때 자기 자신을 루트로 착각한다.
ROOT="$(git worktree list --porcelain 2>/dev/null | sed -n '1s/^worktree //p')"
if [ -z "$ROOT" ] || [ ! -d "$ROOT/.git" ]; then
  echo "✗ git 저장소 안에서 실행하세요." >&2
  exit 1
fi
HERE="$(pwd)"
cd "$ROOT"
if [ "$HERE" != "$ROOT" ] && [ "${HERE#$ROOT/worktrees/}" != "$HERE" ]; then
  echo "· 실험 worktree 안에서 실행했습니다 — main($ROOT) 기준으로 동작합니다"
fi

YES=0
[ "${1:-}" = "--yes" ] && YES=1

if [ ! -d worktrees ]; then
  echo "worktrees/ 가 없습니다. 정리할 것이 없습니다."
  exit 0
fi

TARGETS=()
for wt in worktrees/*/; do
  if [ -d "$wt" ]; then TARGETS+=("${wt%/}"); fi
done

if [ "${#TARGETS[@]}" -eq 0 ]; then
  echo "worktrees/ 가 비어 있습니다."
  exit 0
fi

count_files() {
  find "$1/results" "$1/figures" -type f 2>/dev/null | wc -l | tr -d ' '
}

echo "지워질 것:"
for t in "${TARGETS[@]}"; do
  n=$(basename "$t")
  files=$(count_files "$t" || true)
  echo "    $t  (산출물 ${files:-0} 개)  + branch exp/$n"
done
if [ "$YES" -eq 0 ]; then
  echo
  echo "실제로 지우려면:  bash tools/cleanup.sh --yes"
  exit 0
fi

echo
for t in "${TARGETS[@]}"; do
  n=$(basename "$t")
  git worktree remove --force "$t" && echo "✓ worktree 제거 $t"
  git branch -D "exp/$n" >/dev/null 2>&1 && echo "✓ branch 삭제 exp/$n" || true
done
git worktree prune
rmdir worktrees 2>/dev/null || true
echo
git worktree list
