#!/usr/bin/env bash
# 병렬 실험용 git worktree 를 하나 만든다.
#
# 이 스크립트가 worktree 세팅의 유일한 출처다.
#   · scrnaseq-plan-execute · scrnaseq-stepwise-hitl 스킬이 세션 시작 시 직접 호출한다
#   · tools/setup.sh 는 이름 목록을 받아 이 스크립트를 반복 호출하는 얇은 래퍼다
#
#   bash .claude/scripts/worktree_init.sh <이름> [옵션]
#
# 옵션
#   --mode <이름>     진행 방식 블록을 고른다 (기본: <이름> 과 같다)
#   --goal "..."      EXPERIMENT.md 의 목표 줄
#   --strict-dirty    커밋되지 않은 변경이 있으면 멈추고 사용자에게 묻는다 (기본은 무시하고 진행)
#   --refresh         이미 있는 worktree 를 현재 branch 최신 커밋으로 갱신한다
#                     (공유 링크 재구성 + merge). 사용자가 명시적으로 고른 뒤에만 쓴다.
#
# 커밋되지 않은 변경은 기본적으로 무시하고 마지막 커밋을 출발점으로 진행한다 —
# worktree 세팅 자체는 판단이 갈리는 지점이 아니므로 매번 사용자에게 묻지 않는다.
# 무엇을 무시했는지는 화면에 그대로 남긴다. 정말 멈춰서 확인받고 싶을 때만 --strict-dirty 를 쓴다.
#
# 마지막 줄로 상태를 하나 출력한다. 호출자는 그 줄만 보고 분기하면 된다.
#   ALREADY_IN_WORKTREE <절대경로>   이미 실험 worktree 안이다 — 세팅할 것이 없다
#   EXISTS <절대경로>                그 이름의 worktree 가 이미 있고 최신이다
#   EXISTS <절대경로> STALE <n>      그 이름의 worktree 가 이미 있지만 현재 branch 보다
#                                    n 커밋 뒤에 있다 — 공유 경로 구성(SHARED)이 그 사이에
#                                    바뀌었으면 root 에 옛 파일·끊어진 링크가 남는다.
#                                    호출자는 사용자에게 물어 --refresh 로 다시 부르거나,
#                                    다른 이름으로 새로 만들거나, 그대로 진행한다.
#   WORKTREE <절대경로>              새로 만들었다
# --strict-dirty 를 쓴 상태에서 커밋되지 않은 변경을 만나면 exit 2 로 끝난다.
set -euo pipefail

# 이 저장소의 실습 데이터셋 기본 목표. --goal 로 덮어쓴다.
DEFAULT_GOAL="IFN-beta 자극에 대한 PBMC 세포 타입별 반응 차이를 규명한다"

# main 과 공유할 것 — 실험이 만들지 않고 읽기만 하는 공용 입력·도구.
# 이 경로들은 복사하지 않고 main 을 가리키는 심볼릭 링크로 건다.
# data/processed/ 는 분석 중간 데이터가 쌓이는 곳이라 공유하지 않는다 (실험마다 따로).
# .claude/ 는 검증 에이전트·스킬이다. 실험마다 다르면 검증 기준이 달라져 비교가 깨지므로 공유한다.
#   이 스크립트 자신도 .claude/ 안에 있으므로 함께 공유된다.
# data/genesets/ 는 기능 분석의 prior knowledge 캐시다. 실험마다 다른 gene set 을 받으면
#   "gene set 을 바꿨더니 결과가 달라졌다" 를 말할 수 없으므로 공유한다.
#   ★ git 에 커밋되어 있어야 링크가 걸린다 (tools/link_shared.py 가 git ls-files 를 쓴다).
# .venv 는 이 목록과 별개다 — .gitignore 대상이라 git ls-files 에 안 잡히므로
#   tools/link_shared.py 를 못 쓴다. 아래 worktree 생성 이후 별도 블록에서 심볼릭 링크로 건다.
SHARED=(data/raw data/genesets data/core_markers.xlsx agent_lab .devcontainer .claude tools)

# --- 인자 ------------------------------------------------------------------

NAME=""
MODE=""
GOAL=""
IGNORE_DIRTY=1
REFRESH=0
while [ $# -gt 0 ]; do
  case "$1" in
    --mode)         MODE="${2:?--mode 뒤에 이름이 필요합니다}"; shift 2 ;;
    --goal)         GOAL="${2:?--goal 뒤에 문장이 필요합니다}"; shift 2 ;;
    --ignore-dirty) IGNORE_DIRTY=1; shift ;;   # 기본값과 같다 — 하위 호환용으로 남겨 둔다
    --strict-dirty) IGNORE_DIRTY=0; shift ;;
    --refresh)      REFRESH=1; shift ;;
    -*)             echo "모르는 옵션입니다: $1" >&2; exit 1 ;;
    *)
      if [ -n "$NAME" ]; then
        echo "실험 이름은 하나만 받습니다 (여러 개는 tools/setup.sh 를 쓰세요): $1" >&2
        exit 1
      fi
      NAME="$1"; shift ;;
  esac
done

if [ -z "$NAME" ]; then
  echo "✗ 실험 이름이 필요합니다.  예: bash .claude/scripts/worktree_init.sh plan-execute" >&2
  exit 1
fi
case "$NAME" in
  */*|.*) echo "✗ 실험 이름에 / 나 앞머리 . 는 쓸 수 없습니다: $NAME" >&2; exit 1 ;;
esac
[ -z "$MODE" ] && MODE="$NAME"
[ -z "$GOAL" ] && GOAL="$DEFAULT_GOAL"

# --- 어디서 실행했나 -------------------------------------------------------

# 항상 main 작업 트리를 기준으로 동작한다. 실행 위치가 worktree 안일 수 있으므로
# 스크립트 위치가 아니라 git worktree 목록에서 루트를 잡는다.
ROOT="$(git worktree list --porcelain 2>/dev/null | sed -n '1s/^worktree //p')"
if [ -z "$ROOT" ] || [ ! -d "$ROOT/.git" ]; then
  echo "✗ git 저장소 안에서 실행하세요." >&2
  exit 1
fi

# 이미 실험 worktree 안에서 세션을 띄웠다면 세팅할 것이 없다.
HERE="$(pwd -P)"
ROOT_P="$(cd "$ROOT" && pwd -P)"
if [ "$HERE" != "$ROOT_P" ] && [ "${HERE#$ROOT_P/worktrees/}" != "$HERE" ]; then
  echo "· 이미 실험 worktree 안입니다 — 세팅을 건너뜁니다"
  echo "ALREADY_IN_WORKTREE $HERE"
  exit 0
fi

cd "$ROOT"
BRANCH="exp/$NAME"
DIR="worktrees/$NAME"
ABS="$ROOT_P/$DIR"

BASE="$(git rev-parse --abbrev-ref HEAD)"
HEAD_MAIN="$(git rev-parse HEAD)"

# 끊어진 심볼릭 링크를 치운다. 옛 공유 목록으로 만들어진 worktree 에는 main 에서
# 이미 옮겨진 파일(예: 루트의 setup.sh·verify.py)을 가리키는 링크가 남아 있다.
prune_dead_links() {
  local l
  for l in "$1"/* "$1"/.[!.]*; do
    if [ -L "$l" ] && [ ! -e "$l" ]; then
      rm -f "$l"
      echo "· 끊어진 링크 제거: ${l#$ROOT_P/}"
    fi
  done
}

# 이미 만들어 둔 worktree 를 현재 branch 최신 커밋으로 갱신한다.
# 공유 경로는 skip-worktree + 심볼릭 링크 상태라 그대로는 merge 가 거부된다.
# 그래서 링크를 먼저 걷어내고(--unlink) merge 한 뒤 새 공유 목록으로 다시 건다.
refresh_worktree() {
  echo "· 공유 링크를 걷어냅니다"
  python3 "$ROOT/tools/link_shared.py" --unlink "$ROOT" "$ROOT/$DIR" "${SHARED[@]}"
  echo "· $BASE 를 $BRANCH 에 merge 합니다"
  if ! git -C "$DIR" merge --no-edit "$BASE"; then
    echo
    echo "✗ merge 가 끝나지 않았습니다. 충돌을 해결한 뒤 아래를 실행해 공유 링크를 다시 거세요."
    echo "    git -C $DIR commit          # 충돌 해결 후"
    echo "    bash .claude/scripts/worktree_init.sh $NAME --refresh"
    exit 3
  fi
  python3 "$ROOT/tools/link_shared.py" "$ROOT" "$ROOT/$DIR" "${SHARED[@]}"
  python3 "$ROOT/tools/link_shared.py" --link "$ROOT" "$ROOT/$DIR" "${SHARED[@]}"
  prune_dead_links "$ROOT_P/$DIR"
  echo "✓ $DIR 를 $BASE 최신 커밋으로 갱신했습니다"
}

# 이미 있으면 그대로 쓴다. 여기서는 dirty 여부를 따지지 않는다 —
# 만들 때 이미 출발점이 정해졌고, 지금 main 의 커밋되지 않은 변경은 이 worktree 와 무관하다.
# 다만 만든 뒤 main 이 앞서 나갔는지는 본다. 공유 경로 목록(SHARED)이나 디렉토리 구조가
# 그 사이에 바뀌었으면 이 worktree 는 옛 구성 그대로 남아 있기 때문이다.
if [ -e "$DIR" ]; then
  if [ "$REFRESH" -eq 1 ]; then
    echo "· $DIR 이미 있습니다 — 갱신합니다 (--refresh)"
    refresh_worktree
    echo "EXISTS $ABS"
    exit 0
  fi
  echo "· $DIR 이미 있습니다 — 그대로 씁니다"
  if git -C "$DIR" merge-base --is-ancestor "$HEAD_MAIN" HEAD 2>/dev/null; then
    echo "EXISTS $ABS"
    exit 0
  fi
  BEHIND="$(git -C "$DIR" rev-list --count "HEAD..$HEAD_MAIN" 2>/dev/null || echo 0)"
  echo "· 다만 이 worktree 의 branch($BRANCH) 는 $BASE 보다 $BEHIND 커밋 뒤에 있습니다."
  echo "  그 사이에 공유 파일의 위치가 바뀌었다면 이 worktree 의 root 에는 옛 파일과"
  echo "  끊어진 링크가 그대로 남아 있습니다. 갱신하려면:"
  echo "      bash .claude/scripts/worktree_init.sh $NAME --refresh"
  echo "EXISTS $ABS STALE $BEHIND"
  exit 0
fi

# --- 사전 점검 -------------------------------------------------------------

DIRTY="$(git status --porcelain)"
if [ -n "$DIRTY" ] && [ "$IGNORE_DIRTY" -eq 0 ]; then
  echo "✗ 커밋되지 않은 변경이 있습니다. worktree 는 마지막 커밋을 기준으로 만들어지므로"
  echo "  아래 변경들은 실험 worktree 에 들어가지 않습니다."
  echo
  echo "$DIRTY" | sed 's/^/    /'
  echo
  echo "  둘 중 하나를 고르세요."
  echo "    1) 지금 상태를 실험의 출발점으로 삼는다"
  echo "         git add -A && git commit -m '병렬 실험 출발점'"
  echo "    2) 마지막 커밋을 출발점으로 삼고 위 변경은 main 에만 둔다"
  echo "         --strict-dirty 없이 다시 실행한다"
  exit 2
elif [ -n "$DIRTY" ]; then
  echo "· 커밋되지 않은 변경이 있지만 무시하고 마지막 커밋을 출발점으로 삼습니다:"
  echo "$DIRTY" | sed 's/^/    /'
fi

mkdir -p worktrees

# --- 실험별 설명 -----------------------------------------------------------

describe() {
  case "$1" in
    plan-execute)
      echo "전체 계획을 먼저 세우고, 한 번 승인받은 뒤 끝까지 자율 실행한다" ;;
    stepwise-hitl)
      echo "한 단계씩 진행하고, 판단이 갈리는 지점마다 멈춰 사람에게 묻는다" ;;
    *)
      echo "(아이디어 설명을 EXPERIMENT.md 에 직접 적으세요)" ;;
  esac
}

rules_block() {
  case "$1" in
    plan-execute)
      cat <<'BLOCK'
사용자가 목표를 주면 먼저 전체 분석 계획을 세워 제시하고 승인을 받는다. 승인 이후에는 사용자에게 되묻지 않고 계획을 끝까지 실행한다.

실행 중 판단이 갈리는 지점을 만나면 멈추지 말고 스스로 결정한다. 대신 무엇을 골랐고 왜 골랐는지, 그리고 고르지 않은 대안이 무엇이었는지를 EXPERIMENT.md 결정 로그에 남긴다. 이때 decided_by 는 claude 다.

계획을 벗어나야 할 이유가 생기면 실행을 멈추지 말고 벗어난 뒤, 무엇이 왜 달라졌는지를 결정 로그에 기록한다.

모든 단계가 끝나면 results/summary/metrics.json 과 results/summary/report.html 을 완성하고 사용자에게 결과를 보고한다.
BLOCK
      ;;
    stepwise-hitl)
      cat <<'BLOCK'
한 번에 한 단계만 진행한다. 사용자가 다음으로 가자고 하기 전에는 다음 단계로 넘어가지 않는다.

각 단계를 끝낼 때마다 (1) 무엇을 했고 어떤 수치가 나왔는지, (2) 이 단계에서 판단이 갈리는 지점과 선택지 2~3개를 근거와 함께 제시하고 멈춘다. 선택지를 제시한 뒤에는 사용자의 답을 기다린다. 스스로 고르고 진행하지 않는다.

사용자가 고른 선택은 EXPERIMENT.md 결정 로그에 decided_by 를 human 으로 기록한다. 사용자가 "알아서 해"라고 맡긴 경우에만 claude 로 기록한다.

여러 단계를 한 번에 처리해 달라는 요청이 아니라면 단계를 묶어서 진행하지 않는다.
BLOCK
      ;;
    *)
      cat <<'BLOCK'
이 실험의 아이디어와 진행 방식은 EXPERIMENT.md 에 적혀 있다. 세션을 시작할 때 EXPERIMENT.md 를 먼저 읽고 그 방식대로 진행한다.
BLOCK
      ;;
  esac
}

# --- worktree 생성 ---------------------------------------------------------

# 두 세션이 동시에 시작하면 .git/index.lock 에서 부딪힐 수 있다. 잠깐 기다리고 다시 시도한다.
git_retry() {
  local tries=0 out
  while :; do
    if out="$("$@" 2>&1)"; then
      [ -n "$out" ] && printf '%s\n' "$out" >&2
      return 0
    fi
    tries=$((tries + 1))
    if [ "$tries" -ge 3 ] || ! printf '%s' "$out" | grep -qi 'index\.lock\|cannot lock'; then
      printf '%s\n' "$out" >&2
      return 1
    fi
    echo "· git 잠금 충돌 — 잠시 후 다시 시도합니다 ($tries/3)" >&2
    sleep 2
  done
}

if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git_retry git worktree add --no-checkout "$DIR" "$BRANCH"
  NOTE="기존 branch $BRANCH 재사용"
else
  git_retry git worktree add --no-checkout -b "$BRANCH" "$DIR" "$BASE"
  NOTE="branch $BRANCH ← $BASE"
fi

# 공유할 경로는 체크아웃하지 않고 main 을 가리키는 심볼릭 링크로 건다.
#   read-tree        index 만 채운다 (파일은 아직 안 쓴다)
#   skip-worktree    공유 경로를 "작업 트리에서 신경 쓰지 마라" 로 표시
#   checkout-index   나머지만 실제로 꺼낸다
git -C "$DIR" read-tree HEAD
python3 "$ROOT/tools/link_shared.py" "$ROOT" "$ROOT/$DIR" "${SHARED[@]}"
git -C "$DIR" checkout-index -a
python3 "$ROOT/tools/link_shared.py" --link "$ROOT" "$ROOT/$DIR" "${SHARED[@]}"
echo "✓ $DIR   ($NOTE)"

# .venv 는 .gitignore 대상이라 git 이 추적하지 않으므로 SHARED 배열(git 추적 파일 전용
# tools/link_shared.py)로는 못 건다. 실험마다 scanpy·decoupler 등을 새로 설치하지 않도록
# main 의 .venv 를 그대로 심볼릭 링크로 공유한다 — 읽기 전용으로 쓴다.
if [ -d "$ROOT/.venv" ] && [ ! -e "$DIR/.venv" ]; then
  ln -s "../../.venv" "$DIR/.venv"
  echo "✓ .venv → main 공유 (심볼릭 링크)"
fi

# CLAUDE.md — 공통 지침 + 이 실험의 진행 방식
if [ -f CLAUDE.md ]; then
  cp CLAUDE.md "$DIR/CLAUDE.md"
else
  cp CLAUDE.example.md "$DIR/CLAUDE.md"
fi
{
  echo
  echo
  echo "## 이 작업 트리는 실험 \"$NAME\" 이다"
  echo
  echo "branch: $BRANCH"
  echo
  rules_block "$MODE"
} >> "$DIR/CLAUDE.md"

# 1교시에서 채운 .mcp.json 을 그대로 물려준다
[ -f .mcp.json ] && cp .mcp.json "$DIR/.mcp.json"

# EXPERIMENT.md — 실험 카드
cat > "$DIR/EXPERIMENT.md" <<MD
# 실험 — $NAME

| | |
|---|---|
| branch | \`$BRANCH\` |
| 작업 트리 | \`$DIR\` |
| 목표 | $GOAL |
| 진행 방식 | $(describe "$MODE") |

## 아이디어

<!-- 이 실험에서 무엇을 시험해 보려는지 한두 문단으로 적는다. -->

## 결정 로그

판단이 갈린 지점을 만날 때마다 아래 표에 한 줄씩 더한다.
같은 내용을 \`results/summary/metrics.json\` 의 \`decisions\` 에도 남긴다.

| 단계 | 갈린 지점 | 선택 | 근거 | 결정 주체 |
|---|---|---|---|---|
| | | | | |

## 진행 상황

- [ ] QC
- [ ] 정규화 · HVG
- [ ] 배치 통합 · 차원축소
- [ ] Clustering
- [ ] Cell type annotation
- [ ] 조건 간 차등발현
- [ ] 조건 간 기능 분석 (GSEA · pathway)
- [ ] \`results/summary/metrics.json\`
- [ ] \`results/summary/report.html\`
MD

echo "WORKTREE $ABS"
