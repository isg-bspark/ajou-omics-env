# DEG 시각화 — 두 개의 병렬 패널 세트

> 공통 규칙(그림 안 한글 폰트, 저장 위치, 백그라운드 실행 시 Agg 백엔드)은 `SKILL.md` 의 0번에 있다. 이 파일은 그 위에 얹히는 이 단계의 규격이다.

DEG 는 목적이 다른 두 가지가 있고, **각각 다른 임베딩 위에서 그려야 한다.** 하나로
뭉뚱그리면 조건 신호가 배치 보정으로 지워지거나, 반대로 세포 타입 구조가 조건 차이에
휩쓸려 보이지 않는다.

## 1. Celltype DEG 패널 — "세포 타입이 잘 갈라졌는가"

**목적**: annotation 이 만든 세포 타입 구조 자체를 보여주고, 그 구조를 만든 marker 유전자를
같이 보여준다.

- **왼쪽 패널**: UMAP. `stim`(관심 조건)을 포함해 batch 보정(Harmony 등)된 임베딩
  위에서 계산한 clustering 결과를 그린다 — 즉 3단계 배치 통합 이후의 `post-integration`
  UMAP (`umap_post_integration.png` 계열). 색은 celltype.
- **오른쪽 패널**: **같은 post-integration UMAP 위에** celltype 별 marker 유전자
  (cluster marker, one-vs-rest DEG) 상위 유전자의 **발현량을 색으로** 얹는다
  (`sc.pl.embedding(..., color="<gene>", cmap="YlOrRd")`). 여기서 말하는
  **scatter plot 은 "점 하나 = 세포 하나, 색 = 그 세포의 발현량" 인 UMAP 발현 그림**이지,
  유전자를 점으로 찍는 요약 산점도가 아니다.
- **volcano · MA plot 류(유전자 하나가 점 하나)는 쓰지 않는다.** 유전자 수준 통계는
  표(CSV)로 남기고, 그림은 그 marker 가 **어느 세포에서** 켜져 있는지를 보여주는 데 쓴다.
  x축=pct_expressed, y축=평균발현 같은 **유전자 요약 산점도도 이 패널에서는 쓰지 않는다.**
- 왼쪽·오른쪽을 **한 figure 안에 나란히**(`plt.subplots(1, 2, ...)`) 배치한다.
- 상위 marker 가 여러 개면 **유전자마다 UMAP 하나씩** 그리드로 배치한다
  (`results/05_annotation/figures/celltype_marker_umap_topgenes.png` 계열).
- 파일명 예: `results/05_annotation/figures/celltype_deg_panel.png`.

## 2. 조건(ctrl vs stim) DEG 패널 — "조건 반응이 뚜렷한가"

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
  (`results/06_deg/figures/condition_deg_umap_topgenes.png` 계열).
- 파일명 예: `results/06_deg/figures/condition_deg_panel.png` (조건 색 UMAP + 대표 유전자 발현 UMAP),
  `results/06_deg/figures/condition_deg_umap_topgenes.png` (상위 유전자별 그리드).

> **ctrl 과 stim 을 좌우 패널로 쪼개지 않는다.** 두 조건의 세포를 **한 패널 안에 모두**
> 그린다. pre-integration 임베딩은 이미 조건에 따라 세포를 공간적으로 갈라 놓으므로,
> 한 패널에 다 그리면 조건 차이가 그림 안에서 바로 읽힌다 — 굳이 `ctrl` 패널과 `stim`
> 패널로 나누면 같은 색 스케일을 눈으로 옮겨 가며 비교해야 해서 오히려 대비가 약해진다.
> 이 규칙은 `functional.md` 의 pathway 활성 UMAP 패널에도 똑같이 적용된다 — 거기서도 조건은 패널을
> 쪼개는 기준이 아니라 **한 패널 안의 색**이다.

## 3. 결정 로그에 남길 것

두 패널 세트가 **서로 다른 임베딩을 의도적으로 쓴다는 사실**을 결정 로그에 한 줄로
남긴다 — 이후 검증자나 리뷰어가 "왜 UMAP이 두 종류냐"고 묻지 않도록.
