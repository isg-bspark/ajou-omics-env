# 기능 분석(GSEA·pathway) 시각화 — pathway 활성을 세포 단위로 보여준다

> 공통 규칙(그림 안 한글 폰트, 저장 위치, 백그라운드 실행 시 Agg 백엔드)은 `SKILL.md` 의 0번에 있다. 이 파일은 그 위에 얹히는 이 단계의 규격이다.

enrichment 표(상위 pathway 순위·점수)만으로는 그 pathway 가 실제로 어느 세포에서 얼마나
발현되는지, 조건에 따라 어떻게 갈리는지 보이지 않는다.
[sc-best-practices의 조건 비교·기능 분석 챕터](https://www.sc-best-practices.org/conditions/gsea-pathway/)
방식을 따라 아래 두 그림을 **enrichment 표에 추가로** 그린다. 대상 pathway 는 상위
결과에서 3~5개를 고른다 — 왜 그 pathway 를 골랐는지는 결정 로그에 남긴다.

## 1. Pathway 활성 UMAP 패널 (pathway 하나당 한 패널 + 조건 색 패널)

**목적**: 고른 pathway 의 세포 단위 활성 점수(`dc.mt.*` 결과의 score matrix, 즉
`adata.obsm["score_..."]` 류)를 UMAP 위에 점 색으로 얹어, 그 활성이 특정 세포 타입/영역에
몰려 있는지 눈으로 확인한다. **pathway 마다 따로 파일을 만들지 않고 한 figure 안에
그리드로 배치한다** — pathway 활성은 서로 비교해서 읽는 값이라, 파일을 오가며 보면
"어느 pathway 가 어느 영역에서 켜지는가" 라는 이 그림의 핵심이 드러나지 않는다.

- **비보정(pre-integration) UMAP**을 쓴다 — `deg.md` 의 조건 DEG 패널과 같은 이유로, 배치
  보정된 임베딩을 쓰면 조건이 만드는 활성 차이가 지워질 수 있다. 모든 패널이 **같은
  임베딩·같은 축 범위**를 써야 패널 간 위치 비교가 성립한다.
- **첫 패널은 조건(ctrl vs stim) 색 UMAP 이다.** 나머지 pathway 패널을 읽는 기준점이
  된다 — 어떤 pathway 활성 영역이 stim 세포가 모인 영역과 겹치는지를 눈으로 바로
  대조할 수 있다. 이 패널이 없으면 활성 덩어리를 보고도 그게 조건 때문인지 세포 타입
  때문인지 구분할 수 없다.
- **나머지 패널은 pathway 하나당 하나씩**, 색이 그 세포의 pathway 활성 점수다. 점 하나가
  세포 하나다.
- **ctrl 과 stim 세포는 모든 패널에 함께 그린다** — `deg.md` 2번의 규칙과 같다. 첫 패널에서
  조건을 색으로 구분하는 것이지, 조건별로 패널을 쪼개는 것이 아니다. 조건 간 활성
  분포를 수치로 비교하는 일은 아래 2번 stacked violin 이 맡는다.
- **색 스케일**: 활성 점수는 0 을 중심으로 음수·양수가 함께 나오므로 발현량용
  순차 컬러맵(`YlOrRd` 등)을 쓰지 않는다. `cmap="RdBu_r"` 처럼 발산형을 쓰고
  `vcenter=0` 으로 0 을 중앙에 고정한다. 그렇게 해야 "활성이 낮다" 와 "활성이 음수다"
  가 구분된다. colorbar 는 pathway 마다 범위가 다르므로 패널별로 따로 둔다.
- `acts` 에 조건 컬럼이 넘어왔는지 확인한다(`dc` 결과 객체에 `obs` 가 안 실려 있으면
  `acts.obs["stim"] = adata.obs["stim"]` 로 옮긴다). 없으면 첫 패널을 못 그린다.

```python
pathways = ["INTERFERON_ALPHA_RESPONSE", "INTERFERON_GAMMA_RESPONSE", "TNFA_SIGNALING_VIA_NFKB"]
sc.pl.embedding(
    acts, basis="X_umap_pre_integration",
    color=["stim", *pathways],          # 첫 패널 = 조건, 나머지 = pathway 활성
    cmap="RdBu_r", vcenter=0,
    ncols=2, wspace=0.3, show=False,
)
```

- 파일명 예: `results/07_functional/figures/pathway_umap_panel.png`.

## 2. Ctrl vs Stim 구분 stacked violin plot

**목적**: 고른 pathway 활성 점수의 분포를 celltype 별로, 그리고 그 안에서 ctrl/stim 을
나눠 비교한다 — 1번 UMAP 패널은 공간 패턴을, stacked violin 은 celltype × 조건별 분포
차이를 정량적으로 보여준다.

`sc.pl.stacked_violin` 은 `groupby` 를 하나만 받으므로 celltype 과 조건을 한 축에 같이
놓을 수 없다. 아래 둘 중 **하나**를 고른다. 어느 쪽이든 **같은 celltype 안에서 ctrl/stim
이 나란히 비교 가능**해야 한다 — celltype 만으로 묶고 조건을 안 나누면 이 그림의 목적을
못 채운다.

#### 방법 A — 합친 그룹 컬럼 + `sc.pl.stacked_violin` (행=pathway, 열=celltype×조건)

```python
acts.obs["celltype_stim"] = (acts.obs["celltype"].astype(str) + "_"
                             + acts.obs["stim"].astype(str)).astype("category")
n_groups = acts.obs["celltype_stim"].nunique()
sc.pl.stacked_violin(
    acts, pathways, groupby="celltype_stim",
    density_norm="count",                        # 아래 주의 1
    figsize=(max(10, 0.55 * n_groups), 6), width=0.9,   # 아래 주의 2
    show=False,
)
```

카테고리는 알파벳순으로 정렬되므로 `<celltype>_ctrl` 과 `<celltype>_stim` 이 저절로
이웃한다 — 같은 celltype 의 두 조건이 항상 붙어 나온다.

#### 방법 B — pathway 별 subplot + `seaborn.violinplot` (패널=pathway, x=celltype, hue=조건)

```python
long = acts.to_df().assign(**acts.obs[["celltype", "stim"]]).melt(
    id_vars=["celltype", "stim"], var_name="pathway", value_name="score")
fig, axes = plt.subplots(len(pathways), 1, figsize=(8, 3 * len(pathways)), sharex=True)
for ax, pw in zip(axes, pathways):
    sns.violinplot(data=long[long["pathway"] == pw], x="celltype", y="score",
                   hue="stim", split=True, ax=ax)
    ax.axhline(0, color="grey", lw=.8, ls="--")   # 활성 0 기준선
```

**subplot 을 나누는 기준은 celltype 이 아니라 pathway 다.** celltype 별로 패널을 나눠
놓고 그 안에서 다시 `x="celltype"` 으로 묶으면 패널마다 x축 카테고리가 하나뿐이라
바이올린 한 쌍만 덩그러니 남는다 — 여러 celltype 을 쌓아 비교한다는 이 그림의 목적이
사라진다. `split=True` 는 조건이 정확히 두 개일 때만 쓴다.

여러 pathway 를 한 그림에 stack 하든(방법 A) pathway 하나당 패널 하나로 나누든(방법 B)
상관없다 — ctrl/stim 구분이 보이면 된다.

- 파일명 예: `results/07_functional/figures/pathway_stacked_violin.png`.

#### 이 그림이 이상해 보일 때 — 원인 넷

1. **바이올린이 세로선처럼 얇다 → `figsize`.** `celltype_stim` 은 보통 12개 이상
   (celltype 6~9개 × 조건 2개)이 되는데, `figsize` 기본값이나 임의로 준 작은 값
   (예: `(6, 8)`)은 이만큼의 카테고리를 욱여넣기엔 좁다. 각 바이올린 폭이 머리카락처럼
   얇아져 모양이 안 보인다 — 값이 잘못된 게 아니라 그릴 자리가 부족한 것이다. 위
   방법 A 코드처럼 그룹 수에 비례해 너비를 잡는다.
2. **그룹 크기가 안 보인다 → `density_norm`.** `sc.pl.stacked_violin` 의 기본값은
   `density_norm="width"` 라 모든 바이올린을 같은 최대 폭으로 정규화한다. 세포 5개짜리
   조합이 2000개짜리와 똑같이 크게 보인다. `density_norm="count"` 로 바꾸거나, 그룹별
   세포 수를 그림이나 표에 같이 남긴다.
3. **위아래가 뒤섞여 보인다 → 0 기준선이 없다.** 활성 점수는 0 을 중심으로 부호가
   갈리는 값인데 stacked violin 은 원래 음수가 없는 발현량용 그림이라 기준선이 없다.
   0 선을 그어야 "활성이 올라갔다"와 "내려갔다"가 구분된다.
4. **`KeyError: not in index` 로 죽는다 → 쓰이지 않는 카테고리.** `groupby` 컬럼에 실제로
   등장하지 않는 카테고리가 남아 있으면 빈 칸을 그리는 게 아니라 에러로 멈춘다. AnnData
   를 subset 하면 대개 자동 정리되지만, `obs` 컬럼을 직접 손댔다면
   `.cat.remove_unused_categories()` 를 한 번 부른다.

그린 뒤에는 **반드시 그림을 열어서** 바이올린이 실제로 폭을 가지고 있는지, 같은 celltype
의 ctrl/stim 이 이웃해 있는지 확인한다.

## 3. 결정 로그에 남길 것

고른 pathway 목록(왜 이 pathway 들을 골랐는지), UMAP 패널에 쓴
임베딩이 pre-integration 인 이유, stacked violin 에서 celltype×조건을 어떻게 묶었는지를
한 줄로 남긴다. `SKILL.md` 0번의 폰트 규칙을 지켰는지(그림 텍스트를 영어로 뒀는지, 아니면 어떤
한글 폰트를 지정했는지)도 함께 남긴다.
