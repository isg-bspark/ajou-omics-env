# Annotation 이후 — cluster↔celltype 대조 패널 + cluster marker dotplot (둘 다 필수)

> 공통 규칙(그림 안 한글 폰트, 저장 위치, 백그라운드 실행 시 Agg 백엔드)은 `SKILL.md` 의 0번에 있다. 이 파일은 그 위에 얹히는 이 단계의 규격이다.

annotation 단계의 그림은 **두 가지를 함께** 만든다. 하나는 "어느 클러스터가 어느 이름을
받았는가"(1번), 다른 하나는 "그 이름이 marker 로 뒷받침되는가"(2번)다. 둘 중 하나만
있으면 라벨을 검증할 수 없다 — dotplot 만 있으면 클러스터 번호와 세포 타입의 대응이
안 보이고, 대조 패널만 있으면 그 대응이 근거 있는지 알 수 없다.

## 1. Cluster↔celltype 대조 패널 (필수)

**목적**: clustering 이 만든 클러스터와 annotation 이 붙인 세포 타입을 **나란히 놓고**
어느 클러스터가 어느 타입이 됐는지, 한 타입이 여러 클러스터로 쪼개졌거나 여러 타입이
한 클러스터에 뭉쳐 있지 않은지 눈으로 확인한다.

- **왼쪽 패널**: clustering 결과(`leiden` 등) 색. 클러스터 번호를 그림 위에 얹으면
  (`legend_loc="on data"`) 오른쪽과 대조하기 쉽다. 제목에 어떤 resolution 인지 적는다.
- **오른쪽 패널**: annotation 결과(`celltype` / `celltype_broad`) 색.
- **양쪽 모두 같은 임베딩**을 쓴다 — clustering 을 수행한 그 임베딩, 즉
  **post-integration** UMAP 이다. 좌우가 서로 다른 좌표계면 대조 자체가 불가능하다.
- 한 figure 안에 `plt.subplots(1, 2, ...)` 로 나란히 배치한다.
- 파일명 예: `results/05_annotation/figures/cluster_vs_celltype_panel.png`.

```python
fig, axes = plt.subplots(1, 2, figsize=(15, 6))
sc.pl.umap(adata, color="leiden", ax=axes[0], show=False, legend_loc="on data",
           title=f"Leiden clusters (resolution {res})")
sc.pl.umap(adata, color="celltype_broad", ax=axes[1], show=False,
           title="Cell types")
```

> **리포트 배치**: 이 대조 패널은 **dotplot 과 같은 절(annotation 절)에 함께** 놓는다.
> 대조 패널로 "클러스터 3 → NK cells" 를 확인하고 바로 아래 dotplot 에서 "클러스터 3 에
> GNLY·KLRD1 이 켜져 있다" 를 확인하는 흐름이 되어야 한다. 둘을 다른 절로 떼어 놓으면
> 독자가 라벨의 근거를 따라갈 수 없다.

## 2. Cluster marker dotplot (필수)

annotation 이 끝나면 cluster 별로 marker 발현이 실제로 분리되는지 **dotplot 으로 확인한다.**

1. **1차 dotplot**: 이 조직에서 흔히 쓰는 전체 marker 세트(`data/core_markers.xlsx` 가 있으면
   그 유전자들, 없으면 이 조직에서 통용되는 대표 마커)로 `sc.pl.dotplot(groupby="leiden", ...)`
   를 그린다.

   **marker 를 세포 타입별로 묶어서 넘긴다.** `var_names` 에 유전자 이름을 평평한
   리스트로 주면(특히 `sorted(...)` 로 정렬하면) 알파벳 순으로 늘어서서, 어느 marker
   묶음이 어느 타입을 가리키는지가 그림에서 사라진다. dotplot 을 보는 이유가 바로 그
   대응을 확인하는 것이므로, **`{세포타입: [marker...]}` 딕셔너리로 넘겨** 타입별
   구획(bracket)이 그려지게 한다.

   **positive marker 만 그리지 않는다 — negative marker 도 같이 그린다.**
   `data/core_markers.xlsx` 는 `Cell type` / `Marker` / `Type`(`Positive`/`Negative`)
   세 열 구조이고, `Type == "Negative"` 행은 "이 타입이라면 **꺼져 있어야 하는**
   유전자"다. 이걸 빼고 그리면 dotplot 이 "켜져 있다"만 보여 주고 **배제 근거**
   (예: CD4 T 라면 `CD8A`·`NKG7`·`LYZ` 가 꺼져 있어야 한다)는 못 보여 준다 — 인접한
   타입끼리 헷갈리는 구간이 바로 이 배제 근거로 갈린다.

   타입마다 **positive 묶음과 negative 묶음을 각각 별도 구획으로** 넘겨, 그림에서
   `CD4 T cells (+)` / `CD4 T cells (-)` 처럼 나란히 읽히게 한다. 한 묶음에 섞으면
   어느 점이 켜져야 맞고 어느 점이 꺼져야 맞는지 구분이 사라진다. 구획 라벨은
   `SKILL.md` 0번 규칙대로 **영어(+ ASCII `(+)`/`(-)`)**로 쓴다.

   ```python
   df = pd.read_excel("data/core_markers.xlsx")          # Cell type / Marker / Type
   marker_groups = {}
   for ct, sub in df.groupby("Cell type", sort=False):
       for sign, label in (("Positive", "+"), ("Negative", "-")):
           genes = [g for g in sub.loc[sub["Type"] == sign, "Marker"]
                    if g in adata.var_names]
           if genes:
               marker_groups[f"{ct} ({label})"] = list(dict.fromkeys(genes))
   sc.pl.dotplot(adata, var_names=marker_groups, groupby="leiden", ...)
   ```

   같은 유전자가 여러 타입의 marker 로 중복 등장하는 것은 그대로 둔다 — 그 중복 자체가
   "이 marker 는 단독으로는 타입을 못 가른다"는 정보다. 한 타입의 positive 가 다른 타입의
   negative 로 다시 나오는 것도 정상이므로 그대로 둔다.

   **읽는 법**: 어떤 클러스터를 `X` 로 부르려면 `X (+)` 구획의 점이 크고 진하면서
   동시에 `X (-)` 구획의 점이 작고 옅어야 한다. 둘 중 하나만 맞으면 근거가 약한
   것이므로 아래 3번(`unassigned-weak`)으로 넘기고 결정 로그에 남긴다.

2. **한눈에 클러스터 구분이 안 되면** (예: 대부분의 클러스터에서 여러 마커가 비슷한
   크기·색으로 찍혀 있어 어느 마커가 어느 클러스터를 가르는지 바로 안 보이는 경우)
   — **2차 축소 dotplot**을 추가로 그린다. 배정된 celltype 과 도메인
   지식을 바탕으로, **타입마다 가장 특이적인 marker 1~3개만** 추려서 다시 그린다.
   이때도 **타입별로 묶은 딕셔너리로 넘기고, positive `(+)` / negative `(-)` 구획을
   둘 다 남긴다**(1번과 같은 이유) — 축소한다고 negative 를 통째로 버리지 않는다.
   타입마다 positive 1~3개 + negative 1~2개 정도가 기준이다.
   두 그림 모두 저장하고, 축소가 필요했는지/왜 필요했는지 결정 로그에 남긴다.
3. 축소 여부와 무관하게 최종적으로 **클러스터마다 최소 1개 이상의 뚜렷한 marker**가
   dotplot 상에서 식별돼야 한다. 안 되면 근거 약한 클러스터로 표시하고 annotation 요약에
   남긴다(기존 `unassigned-weak` 관행 유지).

파일명 예: `results/05_annotation/figures/dotplot_core_markers.png`(1차),
`results/05_annotation/figures/dotplot_curated_markers.png`(2차, 필요시).

## 3. 결정 로그에 남길 것

대조 패널에서 읽히는 것 중 **클러스터와 세포 타입이 1:1 이 아닌 지점**을 기록한다 —
한 타입이 여러 클러스터로 갈렸다면 왜 합치지 않았는지, 한 클러스터가 근거 약해
`Ambiguous`/`unassigned` 로 남았다면 그 판단 근거를 남긴다.
