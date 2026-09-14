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
- **첫 두 패널은 기준 패널이다 — 조건(ctrl vs stim) 색 UMAP 과 celltype 색 UMAP.**
  나머지 pathway 패널을 읽는 기준점이 되며, **둘 다 있어야** 한다. 활성 덩어리 하나를
  보고 그것이 조건 때문인지 세포 타입 때문인지 가르려면 두 기준이 모두 필요하기
  때문이다 — 조건 패널만 있으면 "stim 세포가 모인 영역과 겹친다" 까지만 말할 수 있고
  그 활성이 어느 세포 타입에서 올라왔는지는 말할 수 없다. celltype 패널만 있으면 그
  반대다. 두 기준 패널은 pathway 패널과 **같은 figure 안에, 같은 임베딩·같은 축
  범위**로 둔다 — 파일을 따로 빼면 대조가 성립하지 않는다.
- celltype 패널은 `legend_loc="on data"` 로 라벨을 점 위에 얹는다. 패널이 여럿이라
  옆으로 붙는 범례는 그리드 폭을 잡아먹고 패널마다 축 범위를 어긋나게 만든다.
- **나머지 패널은 pathway 하나당 하나씩**, 색이 그 세포의 pathway 활성 점수다. 점 하나가
  세포 하나다.
- **ctrl 과 stim 세포는 모든 패널에 함께 그린다** — `deg.md` 2번의 규칙과 같다. 첫 패널에서
  조건을 색으로 구분하는 것이지, 조건별로 패널을 쪼개는 것이 아니다. 조건 간 활성
  분포를 수치로 비교하는 일은 아래 2번 stacked violin 이 맡는다.
- **색 스케일**: 활성 점수는 0 을 중심으로 음수·양수가 함께 나오므로 발현량용
  순차 컬러맵(`YlOrRd` 등)을 쓰지 않는다. `cmap="RdBu_r"` 처럼 발산형을 쓰고
  `vcenter=0` 으로 0 을 중앙에 고정한다. 그렇게 해야 "활성이 낮다" 와 "활성이 음수다"
  가 구분된다. colorbar 는 pathway 마다 범위가 다르므로 패널별로 따로 둔다.
- `acts` 에 **조건 컬럼과 celltype 컬럼이 둘 다** 넘어왔는지 확인한다(`dc` 결과 객체에
  `obs` 가 안 실려 있으면 `acts.obs[["stim", "celltype"]] = adata.obs[["stim", "celltype"]]`
  로 옮긴다). 없으면 기준 패널을 못 그린다. celltype 은 annotation 단계에서 배정한
  라벨 컬럼을 그대로 쓴다 — 여기서 다시 만들지 않는다.

```python
pathways = ["INTERFERON_ALPHA_RESPONSE", "INTERFERON_GAMMA_RESPONSE", "TNFA_SIGNALING_VIA_NFKB"]
sc.pl.embedding(
    acts, basis="X_umap_pre_integration",
    color=["stim", "celltype", *pathways],   # 기준 패널 둘 + pathway 활성
    cmap="RdBu_r", vcenter=0,                # 발산형 컬러맵은 pathway 패널에만 적용된다
    legend_loc="on data",
    ncols=3, wspace=0.3, show=False,
)
```

- 파일명 예: `results/07_functional/figures/pathway_umap_panel.png`.

## 2. Ctrl vs Stim 구분 stacked violin plot

**목적**: 고른 pathway 활성 점수의 분포를 celltype 별로, 그리고 그 안에서 ctrl/stim 을
나눠 비교한다 — 1번 UMAP 패널은 공간 패턴을, stacked violin 은 celltype × 조건별 분포
차이를 정량적으로 보여준다.

`sc.pl.stacked_violin` 은 `groupby` 를 하나만 받으므로 celltype 과 조건을 한 축에 같이
놓을 수 없다. **조건이 정확히 둘(ctrl/stim)이면 방법 B 를 쓴다** — 같은 x 위치에서
바이올린을 좌우로 갈라 그리므로 ctrl/stim 이 말 그대로 나란히 붙는다. `stacked_violin`
자체를 써야 하는 사정이 있을 때만 방법 A 로 간다.

어느 쪽이든 **같은 celltype 안에서 ctrl/stim 이 나란히 비교 가능**해야 한다 — celltype
만으로 묶고 조건을 안 나누면 이 그림의 목적을 못 채운다.

#### 방법 B (기본) — pathway 별 subplot + `seaborn.violinplot` split

패널 하나가 pathway 하나, x 축이 celltype, 바이올린 하나가 좌(ctrl)/우(stim)로 갈린다.

```python
long = (acts.to_df()
        .assign(celltype=acts.obs["celltype"].values, stim=acts.obs["stim"].values)
        .melt(id_vars=["celltype", "stim"], var_name="pathway", value_name="score"))

fig, axes = plt.subplots(len(pathways), 1, sharex=True,
                         figsize=(1.1 * long["celltype"].nunique() + 3, 3 * len(pathways)))
for ax, pw in zip(axes, pathways):
    sns.violinplot(data=long[long["pathway"] == pw], x="celltype", y="score",
                   hue="stim", split=True,          # 아래 주의 1
                   density_norm="width",            # 아래 주의 2
                   inner="quart", ax=ax, legend=(ax is axes[0]))
    ax.axhline(0, color="grey", lw=.8, ls="--")     # 활성 0 기준선
    ax.set_title(pw, fontsize=9); ax.set_xlabel("")
axes[-1].tick_params(axis="x", rotation=45)
for lab in axes[-1].get_xticklabels():
    lab.set_ha("right")
fig.tight_layout()
```

**subplot 을 나누는 기준은 celltype 이 아니라 pathway 다.** celltype 별로 패널을 나눠
놓고 그 안에서 다시 `x="celltype"` 으로 묶으면 패널마다 x축 카테고리가 하나뿐이라
바이올린 한 쌍만 덩그러니 남는다 — 여러 celltype 을 쌓아 비교한다는 이 그림의 목적이
사라진다.

- `inner="quart"` 로 사분위선을 넣는다. 좌우 반쪽의 중앙값 선이 어긋난 정도가 곧
  조건 효과이므로, 이 선이 없으면 눈대중으로만 읽게 된다.
- 범례는 첫 패널에만 둔다(`legend=(ax is axes[0])`). 패널마다 범례가 붙으면 그림 폭이
  패널마다 달라져 x축이 어긋난다.

#### 방법 A — 합친 그룹 컬럼 + `sc.pl.stacked_violin`

`stacked_violin` 을 쓸 때는 **`swap_axes=True` 를 반드시 켜서 그룹을 x 축에 놓고, 너비를
그룹 수에 비례시킨다.**

```python
acts.obs["celltype_stim"] = (acts.obs["celltype"].astype(str) + "_"
                             + acts.obs["stim"].astype(str)).astype("category")
n_groups = acts.obs["celltype_stim"].nunique()
sc.pl.stacked_violin(
    acts, pathways, groupby="celltype_stim",
    swap_axes=True,                                      # 행=pathway, 열=celltype×조건
    density_norm="width",                                # 아래 주의 2
    figsize=(max(10, 0.75 * n_groups), 2.2 * len(pathways) + 1.5),   # 아래 주의 3
    show=False,
)
```

카테고리는 알파벳순으로 정렬되므로 `<celltype>_ctrl` 과 `<celltype>_stim` 이 저절로
이웃한다 — 같은 celltype 의 두 조건이 항상 붙어 나온다. 다만 **붙어 있을 뿐 갈라져 있지는
않으므로**, 두 바이올린이 같은 celltype 쌍인지는 축 라벨을 읽어야 안다. 조건이 둘뿐이면
방법 B 가 낫다.

- 파일명 예: `results/07_functional/figures/pathway_stacked_violin.png`.

#### 이 그림이 이상해 보일 때 — 원인 넷

1. **좌우가 안 갈리고 celltype 당 바이올린이 두 개로 떨어져 있다 → `split`.**
   `split=True` 는 `hue` 카테고리가 정확히 둘일 때만 동작한다. 조건이 셋 이상이면
   `split=False` 로 두고 나란히 배치하거나, 비교할 조건 쌍을 골라 subset 한다.
2. **그룹 크기가 안 보인다 → `density_norm`.** `density_norm="width"` 는 모든 바이올린을
   같은 최대 폭으로 정규화하므로 **모양은 비교되지만 세포 수는 안 보인다** — 세포 5개짜리
   조합이 2000개짜리와 똑같이 크게 보인다. 분포 모양을 비교하는 것이 이 그림의 목적이므로
   `width` 를 기본으로 두되, **그룹별 세포 수를 같은 단계의 표로 반드시 남긴다**
   (`results/07_functional/celltype_stim_counts.csv` 류). 세포 수 자체를 그림에서 보여야
   한다면 `density_norm="count"` 로 바꾼다 — 대신 작은 그룹은 실선처럼 얇아진다.
3. **바이올린이 납작한 선처럼 눌려 있다 → 방향과 `figsize` 가 어긋났다.**
   `sc.pl.stacked_violin` 의 기본 방향은 **그룹이 행(y축)** 이다. 이때 그룹 수에 맞춰
   늘려야 하는 것은 너비가 아니라 **높이**인데, 너비만 키우고 높이를 고정하면
   (`figsize=(0.55 * n_groups, 6)` 류) 18개 그룹이 6인치 안에 눌려 바이올린이 전부
   납작해진다. 위 방법 A 코드처럼 `swap_axes=True` 로 그룹을 x 축에 놓고 **너비**를
   그룹 수에 비례시키거나, 기본 방향을 유지할 거라면 **높이**를 비례시킨다.
4. **`KeyError: not in index` 로 죽는다 → 쓰이지 않는 카테고리.** `groupby`/`hue` 컬럼에
   실제로 등장하지 않는 카테고리가 남아 있으면 빈 칸을 그리는 게 아니라 에러로 멈춘다.
   AnnData 를 subset 하면 대개 자동 정리되지만, `obs` 컬럼을 직접 손댔다면
   `.cat.remove_unused_categories()` 를 한 번 부른다.

그린 뒤에는 **반드시 그림을 열어서** 바이올린이 실제로 폭을 가지고 있는지, 같은 celltype
의 ctrl/stim 이 좌우로 갈려(방법 B) 또는 이웃해(방법 A) 비교되는지 확인한다.

## 3. 결정 로그에 남길 것

고른 pathway 목록(왜 이 pathway 들을 골랐는지), UMAP 패널에 쓴
임베딩이 pre-integration 인 이유, 기준 패널(조건·celltype)에 쓴 컬럼 이름, stacked violin 에서 celltype×조건을 어떻게 묶었는지(방법 A/B 중
무엇을 썼는지, `density_norm` 값과 그룹별 세포 수를 어디에 남겼는지)를 한 줄로 남긴다. `SKILL.md` 0번의 폰트 규칙을 지켰는지(그림 텍스트를 영어로 뒀는지, 아니면 어떤
한글 폰트를 지정했는지)도 함께 남긴다.
