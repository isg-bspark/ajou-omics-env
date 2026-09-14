---
name: scrnaseq-stepwise-hitl
description: '단일세포 RNA-seq 분석을 한 단계씩 진행하며, 매 단계마다 어떤 알고리즘을 쓸지와 파라미터를 얼마로 둘지를 선택지로 제시하고 사용자가 직접 정하게 하는 human-in-the-loop 방식으로 계획하고 실행한다. 연구 질문만 받아서 Task/Objective/Dataset/Path 를 코드베이스 탐색과 질문으로 채운 뒤, QC 부터 한 단계씩 진행하며 코드를 돌리기 전에 매번 승인을 받는다. scrnaseq-plan-execute 와 짝을 이루는 진행 방식이며, 자율 실행 대신 단계별 개입을 원할 때 쓴다. 트리거: "단계별로 물어보면서 분석해줘", "/scrnaseq-stepwise-hitl".'
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
   `EXISTS <경로> STALE <n>` 이면 **진입하기 전에 멈추고** 세 선택지(`--refresh` 로 갱신 /
   다른 이름으로 새로 / 그대로 진행)를 사용자에게 제시한다 — 그 worktree 가 옛 저장소
   구성으로 만들어져 root 에 옛 파일과 끊어진 링크가 남고 `tools/` 같은 새 경로가 없는
   상태라는 뜻이다. 자세한 표와 선택지 문구, 커밋되지 않은 변경 처리 방식(기본은 무시하고
   계속 진행, `--strict-dirty` 를 붙였을 때만 exit 2 로 멈춰 사용자에게 묻는다)은
   `scrnaseq-plan-execute` 0단계에 있다 — 두 스킬의 세팅 절차는 실험 이름과 `--mode` 만
   다르고 나머지는 동일하다.

   이 스킬은 매 갈림길에서 사용자에게 묻는 방식이지만, **worktree 세팅은 갈림길이 아니다.**
   위 절차는 묻지 않고 그대로 실행한다 (`STALE` 은 예외다 — 기존 실험을 어떻게 할지는
   사용자가 정한다). 다만 사용자가 "worktree 없이 여기서 하자"고 하면 0단계를 건너뛰고
   현재 디렉토리에서 진행한다.

## 0.5 전제 확인

worktree 안으로 들어온 뒤 `.claude/agents/step-validator.md` 가 있는지 확인한다. 없으면
사용자에게 알린다. `.claude/` 는 main 을 가리키는 심볼릭 링크이므로, 없다면 그 파일이
git 에 커밋되지 않았다는 뜻이다.

공유 경로가 끊어져 있지 않은지도 함께 본다 (`find . -maxdepth 2 -type l ! -exec test -e {} \; -print`
가 아무것도 출력하지 않아야 하고, `tools/metrics_template.json` 이 읽혀야 한다).
끊어진 링크가 나오면 0단계의 `--refresh` 선택지를 제시한다 — 링크를 직접 손보지 않는다.

Python 실행 환경은 컨테이너에 이미 설치된 것을 그대로 쓴다. 실습 환경(Codespace /
devcontainer)에서는 시스템 `python` 에 scanpy·decoupler·celltypist 가 설치되어 있고,
`.venv/` 가 있는 환경(로컬 main 등)에서는 worktree 가 그것을 공유하므로 `.venv/bin/python`
을 쓴다. 분석 코드를 짜기 전에 어느 쪽인지 한 번 확인하고
(`[ -x .venv/bin/python ] && PY=.venv/bin/python || PY=python`), 패키지가 없으면 없다고
알린다 — 새 가상환경을 만들지 않는다. 자세한 이유는 `scrnaseq-plan-execute` 0.5단계에 있다.

단계별 산출물 경로도 `scrnaseq-plan-execute` 의 R8 을 그대로 따른다 — 표·수치는
`results/01_qc/` ~ `results/07_functional/` 바로 아래에, 그림은 그 단계 안의
`figures/` 하위 디렉토리(`results/05_annotation/figures/` 처럼)에 쓴다. 최상위에
`figures/` 를 따로 만들지 않는다. `results/validation/` 과 `results/summary/` 에는
번호를 붙이지 않는다.

## 1. Task / Objective / Dataset / Path 를 채운다

`scrnaseq-plan-execute` 의 1단계와 같은 절차를 따른다 — 연구 질문(Task)은 0단계에서 받았고,
코드베이스를 탐색해 Dataset 을 실측으로 확인하고(짐작 금지), Objective 를 구체화하고,
Path(입력·참조·작업 디렉토리)를 채운 뒤 사용자에게 확인받는다.

## 2. 단계 구조를 이 연구 질문에 맞게 조립한다

`scrnaseq-plan-execute` 의 2단계와 같은 원칙으로 QC → 정규화/HVG → 배치 통합 →
clustering → annotation → 조건 간 차등발현 → 조건 간 기능 분석 → REPORT 구조를 조립하되,
조건 변수·마커·양성 대조는 이 Dataset 에 맞게 다시 채운다.

**분석 코드를 짜기 전에 그 단계를 다루는 스킬을 먼저 읽는다**(`scrnaseq-plan-execute` 의
R5 와 같다) — QC · 정규화/HVG · 차원축소 · clustering · 차등발현 같은 표준 scRNA-seq
작업은 `scanpy` 스킬이 있으면 **반드시 그 스킬을 읽고** 거기 적힌 함수·인자·순서를
따르고, 기능 분석 단계가 필요하면 `decoupler-cheatsheet` 스킬을 읽는다. 기억에 의존해
API 를 짐작하지 않는다. 스킬끼리 충돌하면 이 프로젝트 전용 스킬
(`scrnaseq-visualization-spec` 등)이 범용 스킬(`scanpy`)보다 우선하며, 어느 쪽을
따랐는지 결정 로그에 남긴다.

annotation 은 marker 점수 최댓값 할당이 아니라 **celltypist** 로 수행한다.

그림은 `scrnaseq-visualization-spec` 스킬이 정한다. **주요 단계의 분석이 끝날 때마다
그림 코드를 짜기 전에 이 스킬을 `Skill` 도구로 호출한다** — 언제 어떻게 호출하는지는
아래 3-5 에 적었다. 이 단계는 진행 방식(단계별 개입)과 무관하게 스킬들을 동일하게 지킨다.

REPORT 단계도 마찬가지로 `scrnaseq-plan-execute` 의 `references/report.md` 규격을 그대로
따른다 — `results/summary/report.html` 에 쓰고, `python tools/build_report.py` 로 그림을
본문에 박은 `report_standalone.html` 을 함께 만든 뒤, **우클릭 → Show Preview 로 연다**는
안내를 경로와 함께 준다. Codespace 웹 편집기는 `.html` 을 소스 코드로만 보여주므로 경로만
알려주면 학생은 리포트를 못 본다.

## 3. 진행 방식 — 여기가 plan-execute 와 다른 지점

- **계획을 한 번에 세우지 않는다.** QC 부터 시작해서 한 단계씩 간다.
- **모든 단계에서 알고리즘과 파라미터를 사용자가 고른다.** Claude 가 기본값으로 돌려
  놓고 사후 통보하지 않는다. 어느 단계든 코드를 돌리기 **전에** 아래 형식으로 선택지를
  제시하고 **멈춘다.**
- 사용자가 고른 선택은 `EXPERIMENT.md` 결정 로그에 `decided_by: human` 으로 남긴다.
  사용자가 "알아서 해" 라고 맡긴 것만 `claude` 로 남긴다.
- 수치를 지어내지 않는다. 없으면 없다고 적는다.
- 사용자가 원하면, 다음 단계로 넘어가기 전에 `step-validator` 서브에이전트로 방금 끝낸
  단계를 채점하고 결과를 보여준 뒤 그 점수를 보고 선택하게 한다. 채점을 돌렸으면 결과를
  **받은 그 자리에서** `results/validation/<번호>_<단계>.md` 에 저장한다 — 사용자에게
  보여주는 것으로 끝내면 대화가 압축될 때 사라진다. 요약하지 말고 받은 표 그대로 넣는다.

### 3-1. 매 단계에서 묻는 형식

단계를 시작할 때 **한 번**, 그 단계의 알고리즘과 파라미터를 묶어서 제시한다. 파라미터
하나마다 따로 묻지 않는다 — 그러면 질문이 수십 개가 되어 진행이 막힌다.

1. **직전 단계 결과 요약** — 무엇을 했고 어떤 수치가 나왔는지. 이번 선택의 근거가 되는
   수치(분포·경계값)를 먼저 보여준다.
2. **알고리즘 선택지** — 2~3개. 각각 이 데이터에서 무엇이 달라지는지 한 줄로.
3. **파라미터 표** — 항목 · 권장값 · 그 값을 권하는 근거 · 바꿨을 때의 영향.
4. **권장안 하나를 명시**하고 멈춘다. 사용자가 표 전체를 승인하거나, 특정 값만 바꾸거나,
   "알아서 해" 라고 맡길 수 있게 한다.

권장값은 **이 데이터에서 실제로 측정한 수치**에서 끌어온다. 교과서 기본값을 그대로 옮겨
적고 근거 칸을 "관례" 로 채우지 않는다 — 근거를 못 대는 값은 권장하지 않고 그 사실을
말한다.

### 3-2. 이 환경에서 실제로 고를 수 있는 것

**설치되어 있지 않은 선택지를 제시하지 않는다.** 아래는 실측한 목록이다(scanpy 1.11.5,
decoupler 2.2.0, celltypist 1.7.1). 제시 전에 달라졌을 수 있으니 한 번 확인한다.

| 단계 | 알고리즘 선택지 | 사용자가 정할 파라미터 |
|---|---|---|
| QC | 고정 컷오프 · 분위수 기반 · MAD 기반 / `sc.pp.scrublet` 로 doublet 제거할지 | `min_genes` · `max_genes` · `pct_counts_mt` 상한 · `min_cells` · doublet 임계 |
| 정규화 · HVG | `normalize_total`+`log1p` · `pearson_residuals` / HVG flavor `seurat` · `seurat_v3` · `cell_ranger` | `target_sum` · `n_top_genes` 또는 분산 컷오프 · `batch_key` 로 HVG 를 배치별로 뽑을지 · scale 및 `max_value` |
| 배치 통합 | 보정 안 함 · `sc.pp.combat` · `sc.external.pp.harmony_integrate` | `batch_key` · `n_pcs` · `n_neighbors` · harmony 수렴 관련 인자 |
| Clustering | `sc.tl.leiden` · `sc.tl.louvain` | 후보 `resolution` 목록 · `flavor`/`n_iterations` · 최종 채택값 |
| Annotation | celltypist pretrained 모델 (복수 후보) · 필요하면 서브클러스터링 | 모델명 · `majority_voting` 여부 · 참조 marker 파일로 검증할 범위 |
| 차등발현 | `sc.tl.rank_genes_groups` (`wilcoxon`·`t-test`·`logreg`) · pseudobulk + `pydeseq2` | `padj` · `log2FC` 컷오프 · up/down 방향 정의 · pseudobulk 집계 단위 |
| 기능 분석 | `dc.mt.ulm` · `mlm` · `ora` · `gsea` · `gsva` · `aucell` · `consensus` | gene set 출처(`data/genesets/`) · 최소 집합 크기 · 상위 pathway 개수 |
| REPORT | — | 어떤 그림·표를 실을지, 절 구성 |

`bbknn` 과 `scanorama` 는 `sc.external.pp` 에 함수는 있지만 **패키지가 설치되어 있지
않아 호출하면 실패한다.** 선택지로 제시하지 않는다. 사용자가 굳이 원하면 설치가 필요하다고
알리고, 설치 없이 쓸 수 있는 것은 `combat` 과 `harmony` 두 가지라고 말한다.

### 3-3. 단계마다 반드시 짚어야 하는 갈림길

위 표는 매 단계의 공통 항목이고, 아래 넷은 **결과를 가장 크게 가르는 지점**이라
사용자가 "알아서 해" 라고 맡겨도 **무엇을 골랐는지 반드시 보고한다.**

- **배치 통합** — 조건 변수를 통계 검정의 `batch_key` 로 보정할 것인가, 아니면
  clustering/annotation 목적의 시각화용 임베딩에만 보정을 걸고 통계 입력은 원본으로
  남길 것인가. 조건 자체를 보정하면 찾으려는 신호가 지워질 수 있다.
  보정한 뒤에는 `batch_key` 가 실제로 겹쳤는지와 세포 타입 구조가 살아남았는지를
  `scrnaseq-visualization-spec` 의 `references/integration.md` 규격대로 그림과 표로 확인하고, **보정 전 임베딩을
  따로 보관한다** — 뒤의 조건 DEG·pathway 그림이 그것을 쓴다.
- **Clustering resolution** — 하나만 고정으로 쓰지 않는다. 최소 3~4개 후보(예:
  0.3/0.5/0.8/1.0)로 Leiden 을 각각 돌리고, `data/core_markers.xlsx` 같은 참조 marker
  파일이 있으면 그 positive/negative marker 로 resolution 마다 cluster marker dotplot 을
  그린다(dotplot 형식은 `scrnaseq-visualization-spec` 의 `references/annotation.md` 2번을
  따른다). 그 dotplot 들을
  비교해서 "각 resolution 이 주요 세포 타입을 얼마나 깨끗하게 분리하는지, 해상도를
  올렸을 때 새로 갈리는 것이 의미 있는 하위 타입인지 아니면 이미 분리된 타입의 불필요한
  재분할인지"를 근거로 권장값을 제시하고 선택받는다. 어느 세포 타입이 모든 후보
  resolution 에서 계속 한 클러스터로 뭉쳐 있었는지도 함께 보여준다 — 있다면 annotation
  단계에서 celltypist·서브클러스터링으로 별도 처리가 필요하다는 뜻이므로 결정 로그에
  남긴다.
- **Annotation** — celltypist 모델 선택(조직에 맞는 pretrained 모델이 여러 개거나
  불확실할 때)과, 1차 dotplot 만으로 cluster 구분이 충분한지 아니면 2차 축소 dotplot 이
  필요한지.
- **차등발현** — 세포 단위 검정(`rank_genes_groups`)으로 갈지 pseudobulk + `pydeseq2` 로
  갈지. 세포 단위는 같은 개체의 세포를 독립 표본으로 취급해 p 값이 과대하게 유의해진다.
  이 한계를 설명하고 고르게 한다.

### 3-4. 되묻지 않는 것

매 갈림길에서 묻는 방식이지만, 아래는 갈림길이 아니므로 묻지 않고 그대로 한다 — 물으면
진행만 느려진다.

- worktree 세팅(0단계, `STALE` 만 예외)
- 산출물 경로 규칙(R8) · 결정 로그 형식 · `metrics.json` 키 이름
- `scrnaseq-visualization-spec` 의 그림 규격 — 어떤 임베딩 위에 무엇을 그릴지는 규격이
  정한다. 사용자가 고르는 것은 **분석 방법**이지 그림 형식이 아니다.
- annotation 을 celltypist 로 한다는 것(모델 선택은 사용자가 한다)

### 3-5. 주요 단계가 끝나면 — 그림은 규격 스킬을 호출해서 그린다

분석 코드가 끝나고 그 단계의 수치가 나온 **직후**, 그림 코드를 한 줄이라도 짜기 전에
`Skill` 도구로 `scrnaseq-visualization-spec` 을 호출하고, **그 단계에 해당하는 참조
파일 하나를 읽는다**(네 개를 다 읽지 않는다 — 다른 단계 규격은 지금 쓰이지 않는다).
기억에 남은 규격으로 그리지 않는다 — 규격은 바뀌고, 이 스킬이 정본이다.

호출하는 자리는 다섯이다.

| 단계 | 호출 시점 | 읽을 파일 | 그 단계에서 나와야 하는 그림 |
|---|---|---|---|
| 배치 통합 | 보정이 끝나고 `neighbors`·UMAP 을 다시 만든 뒤 | `references/integration.md` | 보정 전·후 UMAP 대조 패널(`batch_key` 색) + 과보정 확인 marker 패널 + 겹침 표 |
| Clustering | resolution 후보를 다 돌린 뒤, 비교 dotplot 을 그리기 전 | `references/annotation.md` | resolution 별 cluster marker dotplot |
| Annotation | 라벨 배정이 끝난 뒤 | `references/annotation.md` | cluster↔celltype 대조 패널 + cluster marker dotplot |
| 조건 간 차등발현 | DEG 표가 나온 뒤 | `references/deg.md` | celltype DEG 패널 + 조건 DEG 그림 |
| 기능 분석 | enrichment 표가 나온 뒤 | `references/functional.md` | pathway 활성 UMAP 패널 + ctrl/stim stacked violin |

- **한 번 읽었으니 됐다고 넘기지 않는다.** 다섯 자리에서 각각 호출한다. 단계 사이에 대화가
  압축되면 규격이 컨텍스트에서 사라지기 때문이다.
- 호출은 **묻지 않고 그냥 한다**(3-4 와 같은 이유). 사용자가 고르는 것은 분석 방법이지
  그림 형식이 아니므로, 이 호출로 진행을 멈추지 않는다.
- 그림을 저장한 뒤 그 단계에서 **규격이 요구하는 그림이 다 나왔는지 파일 목록으로
  확인**하고, 빠진 것이 있으면 다음 단계로 넘어가기 전에 채운다. `step-validator` 는
  이 규격으로 채점하므로, 여기서 빠뜨린 그림은 그대로 감점이 된다.
- 규격과 사용자가 고른 분석 방법이 어긋나면(예: 배치 보정을 안 하기로 해서 post-
  integration 임베딩이 없는 경우) 임의로 대체하지 말고, 무엇을 어떻게 바꿔 그렸는지
  결정 로그에 남긴다.

## 4. 끝났을 때

`results/summary/metrics.json` 과 `EXPERIMENT.md` 결정 로그를 채운다. 사용자가 고른 것과
Claude 가 고른 것을 `decided_by` 로 구분해서 보여준다. 채점을 돌린 단계는 validation 결과를
함께 정리한다.

정리하기 전에 `ls results/validation/` 로 **채점을 돌린 단계 수만큼 `.md` 가 실제로
있는지** 확인한다. 모자라면 대화에 남아 있는 채점을 지금 옮겨 적고, 이미 사라졌으면 그
단계를 다시 채점한다 — 기억으로 점수를 지어내지 않는다.

REPORT 까지 갔다면 `ls results/summary/` 로 `report.html` 과 `report_standalone.html` 이
둘 다 있는지 확인하고, 여는 법(우클릭 → Show Preview)을 다시 한 번 안내한다.
