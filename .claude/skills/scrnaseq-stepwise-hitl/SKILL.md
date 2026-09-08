---
name: scrnaseq-stepwise-hitl
description: 단일세포 RNA-seq 분석을 한 단계씩 진행하며 판단이 갈리는 지점마다 멈춰 사용자에게 선택지를 제시하는 human-in-the-loop 방식으로 계획하고 실행한다. 연구 질문만 받아서 Task/Objective/Dataset/Path 를 코드베이스 탐색과 질문으로 채운 뒤, QC 부터 한 단계씩 진행하며 매 갈림길에서 승인을 받는다. scrnaseq-plan-execute 와 짝을 이루는 진행 방식이며, 자율 실행 대신 단계별 개입을 원할 때 쓴다. 트리거: "단계별로 물어보면서 분석해줘", "/scrnaseq-stepwise-hitl".
---

이 스킬은 `scrnaseq-plan-execute` 와 **같은 형식**(Task/Objective/Dataset/Path, 8단계 구조,
step-validator 검증)을 쓰지만 **진행 방식이 다르다.** 전체 계획을 한 번에 승인받지 않고,
**한 단계씩 진행하며 매 갈림길에서 멈춰 사용자에게 묻는다.**

두 스킬이 같은 실험을 다른 진행 방식으로 도는 짝이라면(예: 같은 데이터·같은 질문을
worktree 두 개로 나눠 실행), Task/Objective/Dataset/Path 를 두 세션에서 동일하게 맞춘다 —
달라지는 것은 이 스킬의 진행 방식뿐이어야 한다.

## 0. 작업 트리 준비

이 스킬도 자기 실험용 git worktree 를 **스스로 만들고 그 안으로 들어간다.** 사용자가
`tools/setup.sh` 를 미리 실행해 두었을 필요가 없다. 순서는 이렇다.

```
연구 질문(Task) 확보 → worktree 생성·진입 → Dataset·Objective·Path → QC 부터 한 단계씩
```

1. **연구 질문을 확보한다.** 대화에 이미 나왔으면 그대로 쓰고, 없으면 먼저 묻는다.
2. **세팅 스크립트를 실행한다.** 실험 이름은 이 스킬 이름을 따라 `stepwise-hitl` 을
   기본값으로 쓰고, 사용자가 다른 이름을 줬으면 그 이름을 쓴다.

   ```bash
   ROOT="$(git worktree list --porcelain | sed -n '1s/^worktree //p')"
   bash "$ROOT/.claude/scripts/worktree_init.sh" stepwise-hitl \
        --mode stepwise-hitl --goal "<1에서 확보한 연구 질문>"
   ```
3. **마지막 줄의 상태에 따라 분기한다** — `WORKTREE`/`EXISTS` 면 `EnterWorktree` 도구를
   `path: <경로>` 로 호출해 진입하고, `ALREADY_IN_WORKTREE` 면 그대로 1단계로 간다.
   자세한 표와 커밋되지 않은 변경 처리 방식(기본은 무시하고 계속 진행, `--strict-dirty`
   를 붙였을 때만 exit 2 로 멈춰 사용자에게 묻는다)은 `scrnaseq-plan-execute` 0단계에
   있다 — 두 스킬의 세팅 절차는 실험 이름과 `--mode` 만 다르고 나머지는 동일하다.

   이 스킬은 매 갈림길에서 사용자에게 묻는 방식이지만, **worktree 세팅은 갈림길이 아니다.**
   위 절차는 묻지 않고 그대로 실행한다. 다만 사용자가 "worktree 없이 여기서 하자"고 하면
   0단계를 건너뛰고 현재 디렉토리에서 진행한다.

## 0.5 전제 확인

worktree 안으로 들어온 뒤 `.claude/agents/step-validator.md` 가 있는지 확인한다. 없으면
사용자에게 알린다. `.claude/` 는 main 을 가리키는 심볼릭 링크이므로, 없다면 그 파일이
git 에 커밋되지 않았다는 뜻이다.

Python 실행 환경도 `.venv/` 로 main 과 공유된다. 분석 코드를 짜기 전에 `.venv/bin/python`
에 scanpy·decoupler·celltypist 같은 패키지가 있는지 확인하고 그 인터프리터로 실행한다 —
없다고 새 가상환경을 만들지 않는다. 자세한 이유는 `scrnaseq-plan-execute` 0.5단계에 있다.

## 1. Task / Objective / Dataset / Path 를 채운다

`scrnaseq-plan-execute` 의 1단계와 같은 절차를 따른다 — 연구 질문(Task)은 0단계에서 받았고,
코드베이스를 탐색해 Dataset 을 실측으로 확인하고(짐작 금지), Objective 를 구체화하고,
Path(입력·참조·작업 디렉토리)를 채운 뒤 사용자에게 확인받는다.

## 2. 단계 구조를 이 연구 질문에 맞게 조립한다

`scrnaseq-plan-execute` 의 2단계와 같은 원칙으로 QC → 정규화/HVG → 배치 통합 →
clustering → annotation → 조건 간 차등발현 → 조건 간 기능 분석 → REPORT 구조를 조립하되,
조건 변수·마커·양성 대조는 이 Dataset 에 맞게 다시 채운다. 기능 분석 단계가 필요하면
`decoupler-cheatsheet` 스킬을 먼저 읽는다.

annotation 은 marker 점수 최댓값 할당이 아니라 **celltypist** 로 수행하고, annotation·
DEG·기능분석 단계의 그림은 `scrnaseq-visualization-spec` 스킬을 코드를 짜기 전에 읽고
그 규격(cluster marker dotplot, celltype DEG 패널과 조건 DEG 패널을 서로 다른 임베딩
위에 그리는 것, 기능 분석의 pathway 활성 scatter·ctrl/stim 구분 stacked violin, 한글
폰트 깨짐 방지)을 따른다. 이 단계는 진행 방식(단계별 개입)과 무관하게 두 스킬 모두
동일하게 지킨다.

## 3. 진행 방식 — 여기가 plan-execute 와 다른 지점

- **계획을 한 번에 세우지 않는다.** QC 부터 시작해서 한 단계씩 간다.
- 각 단계를 끝낼 때마다 (1) 무엇을 했고 어떤 수치가 나왔는지, (2) 이 단계에서 판단이
  갈리는 지점과 선택지 2~3개를 근거와 함께 제시하고 **멈춘다.** 사용자가 고르기 전에
  스스로 정하고 다음 단계로 넘어가지 않는다.
- 사용자가 고른 선택은 `EXPERIMENT.md` 결정 로그에 `decided_by: human` 으로 남긴다.
  사용자가 "알아서 해" 라고 맡긴 것만 `claude` 로 남긴다.
- 수치를 지어내지 않는다. 없으면 없다고 적는다.
- 사용자가 원하면, 다음 단계로 넘어가기 전에 `step-validator` 서브에이전트로 방금 끝낸
  단계를 채점하고 결과를 보여준 뒤 그 점수를 보고 선택하게 한다. 채점을 돌렸으면 결과를
  **받은 그 자리에서** `results/validation/<번호>_<단계>.md` 에 저장한다 — 사용자에게
  보여주는 것으로 끝내면 대화가 압축될 때 사라진다. 요약하지 말고 받은 표 그대로 넣는다.

배치 통합 단계에서는 다음을 반드시 사용자에게 되묻는다 — **조건 변수를 통계 검정의
batch_key 로 보정할 것인가, 아니면 clustering/annotation 목적의 시각화용 임베딩에만
보정을 걸고 통계 입력은 원본으로 남길 것인가.** 이 선택이 결과를 가장 크게 가른다.

annotation 단계에서는 celltypist 모델 선택(조직에 맞는 pretrained 모델이 여러 개거나
불확실할 때)과, 1차 dotplot 만으로 cluster 구분이 충분한지 아니면 2차 축소 dotplot이
필요한지를 판단이 갈리는 지점으로 사용자에게 제시한다.

## 4. 끝났을 때

`results/summary/metrics.json` 과 `EXPERIMENT.md` 결정 로그를 채운다. 사용자가 고른 것과
Claude 가 고른 것을 `decided_by` 로 구분해서 보여준다. 채점을 돌린 단계는 validation 결과를
함께 정리한다.

정리하기 전에 `ls results/validation/` 로 **채점을 돌린 단계 수만큼 `.md` 가 실제로
있는지** 확인한다. 모자라면 대화에 남아 있는 채점을 지금 옮겨 적고, 이미 사라졌으면 그
단계를 다시 채점한다 — 기억으로 점수를 지어내지 않는다.
