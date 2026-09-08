#!/usr/bin/env bash
# 병렬 실험용 git worktree 를 여러 개 한 번에 만든다.
#
# ★ 보통은 이 스크립트를 직접 실행할 필요가 없습니다.
#   저장소 루트에서 claude 를 띄우고 /scrnaseq-plan-execute 또는
#   /scrnaseq-stepwise-hitl 을 부르면 스킬이 자기 worktree 를 알아서 만들고
#   그 안으로 들어갑니다.
#
#   이 스크립트는 "임의의 아이디어 이름으로 N 개를 미리 깔아 두고 싶을 때" 씁니다.
#
#   bash tools/setup.sh                 # 기본 실험 두 개 (plan-execute · stepwise-hitl)
#   bash tools/setup.sh harmony scvi    # 임의의 아이디어 이름으로 N 개
#
# 옵션
#   --strict-dirty   커밋되지 않은 변경이 있으면 멈추고 확인받는다 (기본은 무시하고 진행)
#
# 실제 세팅(공유 경로 심볼릭 링크 · .venv 공유 · CLAUDE.md · EXPERIMENT.md)은
# .claude/scripts/worktree_init.sh 가 한다. 공유 경로 목록도 거기에 있다.
set -euo pipefail

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

INIT="$ROOT/.claude/scripts/worktree_init.sh"
if [ ! -f "$INIT" ]; then
  echo "✗ $INIT 가 없습니다." >&2
  exit 1
fi

PASS=()
NAMES=()
for arg in "$@"; do
  case "$arg" in
    --strict-dirty|--ignore-dirty) PASS+=("$arg") ;;
    -*) echo "모르는 옵션입니다: $arg" >&2; exit 1 ;;
    *)  NAMES+=("$arg") ;;
  esac
done
if [ ${#NAMES[@]} -eq 0 ]; then
  NAMES=(plan-execute stepwise-hitl)
fi

for NAME in "${NAMES[@]}"; do
  # worktree_init.sh 가 멈추면(커밋 안 된 변경 등) 그 안내를 그대로 보여주고 함께 멈춘다.
  if ! OUT="$(bash "$INIT" "$NAME" ${PASS[@]+"${PASS[@]}"} 2>&1)"; then
    printf '%s\n' "$OUT" >&2
    exit 1
  fi
  # 상태 줄(EXISTS/WORKTREE/...)은 스킬용 신호이므로 사람에게는 보여주지 않는다.
  printf '%s\n' "$OUT" | grep -Ev '^(ALREADY_IN_WORKTREE|EXISTS|WORKTREE) ' || true
done

echo
git worktree list
echo
echo "다음 — 실험마다 VS Code 터미널을 하나씩 열고 그 안에서 claude 를 띄웁니다."
for NAME in "${NAMES[@]}"; do
  echo "    cd $ROOT/worktrees/$NAME && claude"
done
echo
echo "각 worktree 에서 claude 를 띄운 뒤 /scrnaseq-plan-execute 또는 /scrnaseq-stepwise-hitl 을 쓰세요."
echo "진행 상황 확인:  bash tools/status.sh"
