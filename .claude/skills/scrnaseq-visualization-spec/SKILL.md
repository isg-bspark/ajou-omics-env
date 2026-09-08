---
name: scrnaseq-visualization-spec
description: 단일세포 RNA-seq 분석의 annotation·DEG·기능 분석(GSEA·pathway) 단계에서 반드시 만들어야 하는 그림의 종류·구성·기준 임베딩을 명시한다. annotation 은 celltypist 로 수행하고, clustering 결과와 celltype 을 같은 임베딩 위에 나란히 놓은 cluster↔celltype 대조 패널과 cluster marker dotplot(marker 를 세포 타입별로 묶어서 그림, 필요하면 curated marker로 축소)을 리포트의 같은 절에 함께 배치해 검증한다. DEG 시각화는 celltype DEG(post-integration UMAP + marker scatter)와 조건 간 DEG(pre-integration UMAP + 유전자 발현량 색) 두 세트로 나누어 서로 다른 임베딩을 쓴다. 모든 조건 관련 그림은 점 하나가 세포 하나인 scatter 이며 volcano·MA plot 은 쓰지 않고, ctrl 과 stim 을 좌우 패널로 쪼개지 않고 한 패널에 함께 그린다. 기능 분석은 pathway 활성 점수를 UMAP scatter와 ctrl/stim 구분 stacked violin으로 보여주고, 모든 그림은 한글 폰트 깨짐(tofu) 없이 렌더링한다. macOS에서 그림 그리는 스크립트를 백그라운드로 돌릴 때 matplotlib 기본(macosx) 백엔드 때문에 에러 없이 멈추는(hang) 문제와 예방법(matplotlib.use("Agg"))도 다룬다. scrnaseq-plan-execute·scrnaseq-stepwise-hitl 실행 중 annotation·DEG·기능분석 단계 코드를 짜기 전에 읽는다. 트리거: "annotation 그림", "DEG 그림", "dotplot", "volcano plot", "scatter plot", "GSEA 그림", "pathway 그림", "stacked violin", "한글 깨짐", "폰트 깨짐", "스크립트가 멈췄다", "백그라운드 hang", "그림 그리다가 멈춤" 단계 진입 시.
---

이 스킬은 8단계 scRNA-seq 파이프라인(`scrnaseq-plan-execute`/`scrnaseq-stepwise-hitl` 공용)에서
**"그림을 그렸다"만으로는 부족한 지점**을 규격화한 것이다. 어떤 임베딩 위에 그릴지, 어떤
그림 형태(scatter vs volcano)를 쓸지가 결과 해석을 바꾸므로, annotation·DEG·기능분석 코드를
짜기 **전에** 이 문서를 읽고 아래 규격을 따른다. `step-validator` 는 이 규격을 기준으로 채점한다.

## 0. 모든 그림 공통 — 한글 폰트 깨짐(tofu) 방지

matplotlib 기본 폰트(DejaVu Sans)에는 한글 글리프가 없다. 그림 제목·축 라벨에 한글이
섞이면 네모(tofu)로 깨진다 — GSEA/pathway 그림처럼 제목에 "~ 경로 활성" 같은 한글 설명을
붙이는 자리에서 특히 자주 터진다. 아래 둘 중 하나를 **반드시** 지킨다.

1. **(권장) 그림 안 텍스트는 영어만 쓴다.** title·axis label·legend·주석 텍스트 전부.
   pathway/gene set 이름(`INTERFERON_ALPHA_RESPONSE` 등)과 유전자 심볼은 원래 영어이므로
   번역하지 않는다. 해석·설명은 그림이 아니라 리포트 본문(한글)에 쓴다 — 그림 캡션에서
   한글로 설명해도 되는 건 리포트 파일 쪽 텍스트이지 matplotlib 렌더링 텍스트가 아니다.
2. **부득이 그림 안에 한글을 넣어야 하면**, 렌더링 전에 이 환경에 실제로 설치된 한글
   폰트를 확인하고(`fc-list :lang=ko` 또는 `matplotlib.font_manager` 로 탐색) 그 폰트
   이름으로 `plt.rcParams['font.family']` 를 지정한다. `plt.rcParams['axes.unicode_minus']
   = False` 도 같이 설정한다(안 하면 마이너스 부호가 깨진다). 어떤 폰트를 썼는지 결정
   로그에 남긴다.

어느 쪽을 택했든 **저장하기 전에 실제로 그림을 확인해서** 네모 깨짐이 없는지 본다.
확인 없이 "폰트 설정했으니 괜찮겠지"로 넘기지 않는다.

## 0.5 모든 그림 공통 — macOS에서 백그라운드 실행 시 무한 대기(hang) 방지

이 파이프라인의 그림 그리는 스크립트(annotation·DEG·기능분석 전부)는 실행 시간이 길어
`nohup ... &` 나 `run_in_background`로 뒤로 돌려 실행하는 일이 많다. **macOS에서
matplotlib 기본 백엔드가 `macosx`(네이티브 GUI)일 때, 터미널과 분리된 백그라운드
프로세스 안에서 그림을 그리거나 그 뒤에 별다른 이유 없이 스크립트가 멈춘다** — 에러
없이 CPU 사용률이 0%로 떨어진 채 영원히 끝나지 않는다. 특히 `sc.pl.dotplot`,
`sc.pl.umap`, `plt.savefig` 처럼 그림을 저장하는 호출 **직후**에 멈추는 패턴으로
나타나므로, 코드가 잘못됐다고 오인해 애먼 곳을 고치기 쉽다.

- **증상으로 알아채는 법**: 로그에 에러 없이 마지막 `print`/`WARNING: saving figure to
  file ...` 뒤로 출력이 멈췄고, `ps -o pid,%cpu,time -p <PID>` 를 몇 초 간격으로
  반복해도 `TIME` 값이 전혀 늘지 않으면(CPU 0%) 이 문제다. 실제로 계산 중이라면
  CPU%가 0이 아니거나 TIME이 계속 증가한다.
- **예방(권장, 매번 이렇게 시작한다)**: scRNA-seq 그림을 그리는 모든 스크립트 맨 위,
  `import scanpy` 보다 먼저 아래 두 줄을 넣는다. `matplotlib.use()`는 반드시 다른
  matplotlib 관련 import(scanpy 포함, scanpy가 내부에서 matplotlib을 import한다)보다
  **먼저** 호출해야 적용된다.

  ```python
  import matplotlib
  matplotlib.use("Agg")
  import scanpy as sc
  ```

  또는 스크립트를 실행하는 셸에서 환경변수로 지정해도 된다: `MPLBACKEND=Agg
  .venv/bin/python script.py`. 둘 중 하나만 있으면 충분하고, 스크립트 안에 넣는 쪽이
  실행 방법(포그라운드/백그라운드, 어떤 셸)에 관계없이 항상 적용되므로 더 안전하다.
- **이미 멈춘 경우 복구**: `ps aux | grep <script.py>`로 PID를 찾고, `ps -o
  pid,%cpu,time -p <PID>`를 두세 번 간격을 두고 찍어 TIME이 안 늘어나는 것을 확인한
  뒤 `kill -9 <PID>`로 종료한다. 그 다음 위 예방 조치를 스크립트에 추가하고 **처음부터
  다시 실행**한다 — 중간부터 이어가지 않는다(그림을 그리기 전 단계까지는 이미 끝났을
  수 있지만, 안전하게 전체를 재실행하는 편이 무엇이 저장됐는지 추적하기 쉽다).
- 이 문제는 Linux 컨테이너나 CI처럼 애초에 GUI 백엔드가 없는 환경에서는 발생하지
  않는다 — 로컬 macOS 환경에서 실험할 때만 해당한다는 것을 기억한다.

## 1. Annotation — celltypist 로 수행한다

marker positive/negative 점수 최댓값 할당 방식 대신 **celltypist** 로 세포 타입을 예측한다.

- 조직에 맞는 pretrained 모델을 고른다 (PBMC 면 `Immune_All_Low.pkl` 또는
  `Immune_All_High.pkl` 계열). 모델이 로컬에 없으면 `celltypist.models.download_models()`
  로 받고, **모델 이름과 버전을 결정 로그와 `annotation_summary.json` 에 기록한다** —
  기록이 없으면 재현 불가능하다.
- `celltypist.annotate(adata, model=..., majority_voting=True)` 로 세포 단위 예측 후
  cluster 단위로 다수결(majority voting) 라벨을 cluster 에 배정한다. 세포 단위 예측을
  그대로 쓰지 않는다 — 같은 클러스터 안에서 라벨이 흔들리면 그 자체가 클러스터링/해상도
  문제일 수 있으므로 별도로 기록한다.
- `data/core_markers.xlsx` 같은 참조 마커 파일이 있으면 celltypist 라벨과 **대조 검증**에
  쓴다(2번 dotplot 이 이 역할을 한다). celltypist 예측을 이 파일로 덮어쓰지 않는다 —
  불일치가 있으면 근거와 함께 기록하고 어느 쪽을 채택했는지 남긴다.
- celltypist 모델이 이 조직/종에 없거나 부적절하면(예: 비인간 종, 흔치 않은 조직)
  그 사실을 기록하고 marker 기반 방식으로 돌아갈 수 있다 — 단, **왜 celltypist 를 못
  쓰는지**를 결정 로그에 남긴 경우에만 허용한다.

## 2. Annotation 이후 — cluster↔celltype 대조 패널 + cluster marker dotplot (둘 다 필수)

annotation 단계의 그림은 **두 가지를 함께** 만든다. 하나는 "어느 클러스터가 어느 이름을
받았는가"(2-0), 다른 하나는 "그 이름이 marker 로 뒷받침되는가"(2-1~2-3)다. 둘 중 하나만
있으면 라벨을 검증할 수 없다 — dotplot 만 있으면 클러스터 번호와 세포 타입의 대응이
안 보이고, 대조 패널만 있으면 그 대응이 근거 있는지 알 수 없다.

### 2-0. Cluster↔celltype 대조 패널 (필수)

**목적**: clustering 이 만든 클러스터와 annotation 이 붙인 세포 타입을 **나란히 놓고**
어느 클러스터가 어느 타입이 됐는지, 한 타입이 여러 클러스터로 쪼개졌거나 여러 타입이
한 클러스터에 뭉쳐 있지 않은지 눈으로 확인한다.

- **왼쪽 패널**: clustering 결과(`leiden` 등) 색. 클러스터 번호를 그림 위에 얹으면
  (`legend_loc="on data"`) 오른쪽과 대조하기 쉽다. 제목에 어떤 resolution 인지 적는다.
- **오른쪽 패널**: annotation 결과(`celltype` / `celltype_broad`) 색.
- **양쪽 모두 같은 임베딩**을 쓴다 — clustering 을 수행한 그 임베딩, 즉
  **post-integration** UMAP 이다. 좌우가 서로 다른 좌표계면 대조 자체가 불가능하다.
- 한 figure 안에 `plt.subplots(1, 2, ...)` 로 나란히 배치한다.
- 파일명 예: `figures/annotation/cluster_vs_celltype_panel.png`.

```python
fig, axes = plt.subplots(1, 2, figsize=(15, 6))
sc.pl.umap(adata, color="leiden", ax=axes[0], show=False, legend_loc="on data",
           title=f"Leiden clusters (resolution {res})")
sc.pl.umap(adata, color="celltype_broad", ax=axes[1], show=False,
           title="Cell types (celltypist)")
```

> **리포트 배치**: 이 대조 패널은 **dotplot 과 같은 절(annotation 절)에 함께** 놓는다.
> 대조 패널로 "클러스터 3 → NK cells" 를 확인하고 바로 아래 dotplot 에서 "클러스터 3 에
> GNLY·KLRD1 이 켜져 있다" 를 확인하는 흐름이 되어야 한다. 둘을 다른 절로 떼어 놓으면
> 독자가 라벨의 근거를 따라갈 수 없다.

### 2-1. Cluster marker dotplot (필수)

annotation 이 끝나면 cluster 별로 marker 발현이 실제로 분리되는지 **dotplot 으로 확인한다.**

1. **1차 dotplot**: 이 조직에서 흔히 쓰는 전체 marker 세트(`data/core_markers.xlsx` 가 있으면
   그 유전자들, 없으면 celltypist 모델의 대표 마커)로 `sc.pl.dotplot(groupby="leiden", ...)`
   를 그린다.

   **marker 를 세포 타입별로 묶어서 넘긴다.** `var_names` 에 유전자 이름을 평평한
   리스트로 주면(특히 `sorted(...)` 로 정렬하면) 알파벳 순으로 늘어서서, 어느 marker
   묶음이 어느 타입을 가리키는지가 그림에서 사라진다. dotplot 을 보는 이유가 바로 그
   대응을 확인하는 것이므로, **`{세포타입: [marker...]}` 딕셔너리로 넘겨** 타입별
   구획(bracket)이 그려지게 한다.

   ```python
   marker_groups = {ct: [g for g in genes if g in adata.var_names]
                    for ct, genes in marker_dict.items()}
   marker_groups = {ct: gs for ct, gs in marker_groups.items() if gs}
   sc.pl.dotplot(adata, var_names=marker_groups, groupby="leiden", ...)
   ```

   같은 유전자가 여러 타입의 marker 로 중복 등장하는 것은 그대로 둔다 — 그 중복 자체가
   "이 marker 는 단독으로는 타입을 못 가른다"는 정보다.
2. **한눈에 클러스터 구분이 안 되면** (예: 대부분의 클러스터에서 여러 마커가 비슷한
   크기·색으로 찍혀 있어 어느 마커가 어느 클러스터를 가르는지 바로 안 보이는 경우)
   — **2차 축소 dotplot**을 추가로 그린다. celltypist 로 배정된 celltype 과 도메인
   지식을 바탕으로, **타입마다 가장 특이적인 marker 1~3개만** 추려서 다시 그린다.
   이때도 **타입별로 묶은 딕셔너리로 넘긴다**(1번과 같은 이유).
   두 그림 모두 저장하고, 축소가 필요했는지/왜 필요했는지 결정 로그에 남긴다.
3. 축소 여부와 무관하게 최종적으로 **클러스터마다 최소 1개 이상의 뚜렷한 marker**가
   dotplot 상에서 식별돼야 한다. 안 되면 근거 약한 클러스터로 표시하고 annotation 요약에
   남긴다(기존 `unassigned-weak` 관행 유지).

파일명 예: `figures/annotation/dotplot_core_markers.png`(1차),
`figures/annotation/dotplot_curated_markers.png`(2차, 필요시).

### 2-3. 결정 로그에 남길 것

대조 패널에서 읽히는 것 중 **클러스터와 세포 타입이 1:1 이 아닌 지점**을 기록한다 —
한 타입이 여러 클러스터로 갈렸다면 왜 합치지 않았는지, 한 클러스터가 근거 약해
`Ambiguous`/`unassigned` 로 남았다면 그 판단 근거를 남긴다.

## 3. DEG 시각화 — 두 개의 병렬 패널 세트

DEG 는 목적이 다른 두 가지가 있고, **각각 다른 임베딩 위에서 그려야 한다.** 하나로
뭉뚱그리면 조건 신호가 배치 보정으로 지워지거나, 반대로 세포 타입 구조가 조건 차이에
휩쓸려 보이지 않는다.

### 3-1. Celltype DEG 패널 — "세포 타입이 잘 갈라졌는가"

**목적**: annotation 이 만든 세포 타입 구조 자체를 보여주고, 그 구조를 만든 marker 유전자를
같이 보여준다.

- **왼쪽 패널**: UMAP. `stim`(관심 조건)을 포함해 batch 보정(Harmony 등)된 임베딩
  위에서 계산한 clustering 결과를 그린다 — 즉 3단계 배치 통합 이후의 `post-integration`
  UMAP (`umap_post_integration.png` 계열). 색은 celltype.
- **오른쪽 패널**: celltype 별 marker 유전자(cluster marker, one-vs-rest DEG)를
  **scatter plot** 으로 그린다. **volcano 가 아니다** — 유의성 강조가 아니라 발현
  수준 자체를 보여주는 게 목적이다. 기본 형태: x축 = 클러스터 내 발현 세포 비율
  (`pct_expressed_in_group`), y축 = 클러스터 내 평균발현(`mean_expr_in_group`), 점 색 =
  클러스터/celltype, 상위 marker 유전자 이름을 라벨로 표시. (대안으로 x=log2FC,
  y=클러스터 내 평균발현 을 써도 되지만 -log10(padj) 를 축으로 쓰는 볼케이노 형태는
  안 된다.)
- 왼쪽·오른쪽을 **한 figure 안에 나란히**(`plt.subplots(1, 2, ...)`) 배치한다.
- 파일명 예: `figures/annotation/celltype_deg_panel.png`.

### 3-2. 조건(ctrl vs stim) DEG 패널 — "조건 반응이 뚜렷한가"

**목적**: 배치 보정을 걸지 않은 원본 표현형 위에서 조건이 만드는 이동을 보여주고,
그 이동을 만든 유전자의 발현을 **세포 단위로** 보여준다.

**이 패널의 모든 그림은 "점 하나 = 세포 하나, 색 = 발현량" 형태의 scatter 다.**
유전자 하나가 점 하나인 그림(volcano · MA plot 류)은 쓰지 않는다 — 유전자 수준 통계는
표(CSV)로 남기고, 그림은 그 변화가 **어느 세포에서** 일어났는지를 보여주는 데 쓴다.

- **왼쪽 패널**: UMAP. **조건 간 배치 보정을 걸지 않은** 임베딩 — 3단계에서 만든
  `pre-integration` UMAP(원본 `X_pca` 기반, `umap_pre_integration.png` 계열)을 그대로
  쓴다. 색은 조건 변수(`stim`/`ctrl`). Harmony 등으로 보정된 임베딩을 쓰면 조건이
  만든 이동 자체가 지워져 이 패널의 목적과 모순된다.
- **오른쪽 패널**: 같은 pre-integration 임베딩 위에 **조건 간 상위 DEG 유전자 하나의
  발현량을 색으로** 얹는다(`sc.pl.embedding(..., color="<gene>", cmap="YlOrRd")`).
  점 하나가 세포 하나이고, 색이 그 세포의 발현량이다.
- 상위 유전자가 여러 개면 **유전자마다 임베딩 하나씩** 그리드로 배치한다
  (`figures/deg/condition_deg_umap_topgenes.png` 계열).
- 파일명 예: `figures/deg/condition_deg_panel.png` (조건 색 UMAP + 대표 유전자 발현 UMAP),
  `figures/deg/condition_deg_umap_topgenes.png` (상위 유전자별 그리드).

> **ctrl 과 stim 을 좌우 패널로 쪼개지 않는다.** 두 조건의 세포를 **한 패널 안에 모두**
> 그린다. pre-integration 임베딩은 이미 조건에 따라 세포를 공간적으로 갈라 놓으므로,
> 한 패널에 다 그리면 조건 차이가 그림 안에서 바로 읽힌다 — 굳이 `ctrl` 패널과 `stim`
> 패널로 나누면 같은 색 스케일을 눈으로 옮겨 가며 비교해야 해서 오히려 대비가 약해진다.
> 이 규칙은 4-1 pathway 활성 scatter 에도 똑같이 적용된다.

### 3-3. 결정 로그에 남길 것

두 패널 세트가 **서로 다른 임베딩을 의도적으로 쓴다는 사실**을 결정 로그에 한 줄로
남긴다 — 이후 검증자나 리뷰어가 "왜 UMAP이 두 종류냐"고 묻지 않도록.

## 4. 기능 분석(GSEA·pathway) 시각화 — pathway 활성을 세포 단위로 보여준다

enrichment 표(상위 pathway 순위·점수)만으로는 그 pathway 가 실제로 어느 세포에서 얼마나
발현되는지, 조건에 따라 어떻게 갈리는지 보이지 않는다.
[sc-best-practices의 조건 비교·기능 분석 챕터](https://www.sc-best-practices.org/conditions/gsea-pathway/)
방식을 따라 아래 두 그림을 **enrichment 표에 추가로** 그린다. 대상 pathway 는 상위
결과(양성 대조인 `INTERFERON_ALPHA_RESPONSE` 계열 포함)에서 3~5개를 고른다.

### 4-1. Pathway 활성 scatter plot (embedding plot)

**목적**: 고른 pathway 의 세포 단위 활성 점수(`dc.mt.*` 결과의 score matrix, 즉
`adata.obsm["score_..."]` 류)를 UMAP 위에 점 색으로 얹어, 그 활성이 특정 세포 타입/영역에
몰려 있는지 눈으로 확인한다.

- **비보정(pre-integration) UMAP**을 쓴다 — 3-2 조건 DEG 패널과 같은 이유로, 배치
  보정된 임베딩을 쓰면 조건이 만드는 활성 차이가 지워질 수 있다.
- `sc.pl.embedding(acts, basis="X_umap_pre_integration", color="<pathway>", ...)` 형태로
  pathway 마다 **한 장씩** 그린다. 점 하나가 세포 하나, 색이 그 세포의 pathway 활성이다.
- **ctrl 과 stim 세포를 한 패널에 모두 그린다** — 3-2 의 규칙과 같다. 조건별로 좌우
  패널을 나누지 않는다. 조건 간 활성 분포를 수치로 비교하는 일은 4-2 stacked violin 이
  맡는다(같은 celltype 안에서 ctrl/stim 을 나란히 놓는 것은 거기서 한다).
- 파일명 예: `figures/functional/pathway_scatter_<pathway>.png`.

### 4-2. Ctrl vs Stim 구분 stacked violin plot

**목적**: 고른 pathway 활성 점수의 분포를 celltype 별로, 그리고 그 안에서 ctrl/stim 을
나눠 비교한다 — scatter 는 공간 패턴을, stacked violin 은 celltype × 조건별 분포 차이를
정량적으로 보여준다.

- `sc.pl.stacked_violin` 은 `groupby` 를 하나만 받으므로, celltype 과 조건을 합친 그룹
  컬럼(예: `adata.obs["celltype_stim"] = adata.obs["celltype"].astype(str) + "_" +
  adata.obs["stim"].astype(str)`)을 만들어 그 컬럼으로 그리거나, celltype 별 subplot 을
  만들어 각각 `seaborn.violinplot(..., x="celltype", y="score", hue="stim", split=True)`
  로 그린다. 어느 방식을 쓰든 **같은 celltype 안에서 ctrl/stim 이 나란히 비교 가능**해야
  한다 — celltype 만으로 묶고 조건을 안 나누면 이 그림의 목적을 못 채운다.
- 여러 pathway 를 한 그림에 stack 해도 되고(변수=pathway, groupby=celltype_stim), pathway
  하나당 그림 하나로 나눠도 된다 — 어느 쪽이든 ctrl/stim 구분이 보이면 된다.
- 파일명 예: `figures/functional/pathway_stacked_violin.png`.

### 4-3. 결정 로그에 남길 것

고른 pathway 목록(왜 이 pathway 들을 골랐는지 — 양성 대조 포함 여부), scatter 에 쓴
임베딩이 pre-integration 인 이유, stacked violin 에서 celltype×조건을 어떻게 묶었는지를
한 줄로 남긴다. 0번의 폰트 규칙을 지켰는지(그림 텍스트를 영어로 뒀는지, 아니면 어떤
한글 폰트를 지정했는지)도 함께 남긴다.

## 5. step-validator 채점 포인트 (요약)

- annotation 단계: celltypist 사용 여부·모델명 기록, **cluster↔celltype 대조 패널**(같은
  post-integration 임베딩 위에 clustering 결과와 celltype 을 나란히) 존재, 1차 dotplot
  존재, 필요시 2차 축소 dotplot과 그 판단 근거. **dotplot 의 marker 가 세포 타입별로
  묶여 있는지**(알파벳 순 평평한 리스트면 완결성을 깎는다). 리포트에서 대조 패널과
  dotplot 이 **같은 절에 함께** 배치되어 있는지.
- 조건 간 차등발현 단계: celltype DEG 패널(post-integration UMAP + marker scatter)과
  조건 DEG 그림(pre-integration UMAP + 유전자 발현량 색)이 각각 올바른 임베딩을 쓰는지,
  둘을 뒤바꿔 쓰지 않았는지. **volcano·MA plot 이 있으면 규격 위반**이고, **ctrl 과 stim
  이 좌우 패널로 쪼개져 있어도 규격 위반**이다.
- 기능 분석 단계: pathway 활성 scatter(비보정 UMAP, ctrl+stim 한 패널)와 ctrl/stim 구분
  stacked violin 이 둘 다 있는지, 그림 텍스트에 한글 폰트 깨짐(tofu)이 없는지.
- 리포트 단계: **각 절에 그 절의 그림만 들어갔는지.** 조건 간 차등발현 절에 celltype
  DEG 패널(세포 타입 구조를 보여주는 그림)을 넣는 것은 흔한 혼동이다 — celltype DEG
  패널은 annotation 절에, 조건 DEG 그림은 조건 간 차등발현 절에 둔다.
- 공통: 그림 그리는 스크립트를 백그라운드로 실행했다면 `matplotlib.use("Agg")`(또는
  `MPLBACKEND=Agg`)를 적용했는지 — 안 했다면 macOS에서 조용히 멈췄다가 재실행됐을
  가능성이 있으므로, 로그에 재실행 흔적(같은 산출물을 두 번 만든 기록)이 있는지 본다.
