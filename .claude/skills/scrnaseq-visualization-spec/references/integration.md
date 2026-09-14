# 배치 통합 이후 — `batch_key` 기준으로 겹쳐졌는지 확인한다

> 공통 규칙(그림 안 한글 폰트, 저장 위치, 백그라운드 실행 시 Agg 백엔드)은 `SKILL.md` 의 0번에 있다. 이 파일은 그 위에 얹히는 이 단계의 규격이다.

배치 통합은 **보정했다는 사실만으로는 아무것도 말해 주지 않는다.** 두 가지를 동시에
보여야 한다 — (a) `batch_key` 로 나뉘던 덩어리가 보정 후 실제로 **겹쳤는가**,
(b) 겹치는 과정에서 **세포 타입 구조까지 뭉개지지 않았는가**. 둘 중 하나만 보면
과소보정과 과보정을 구분할 수 없다.

여기서 `batch_key` 는 이 단계에서 보정 대상으로 넣은 변수 전부다 — 이 데이터셋처럼
조건(`stim`)을 clustering·annotation 목적으로 보정했다면 그것도 포함하고,
`obs` 에 donor/lane 같은 진짜 배치 변수가 있으면 그것도 각각 본다.

## 1. 보정 전·후 UMAP 대조 패널 (필수)

- **왼쪽**: 보정 전 임베딩(`X_pca` 기반 UMAP), **오른쪽**: 보정 후 임베딩
  (`X_pca_harmony` 등 실제로 `neighbors` 를 만든 그 표현형) 기반 UMAP.
- **양쪽 모두 `batch_key` 값으로 색칠한다.** 이 패널의 질문은 "배치가 겹쳤는가" 하나이므로
  색 기준을 바꾸지 않는다. 세포 타입 색은 아래 2번이 맡는다.
- `batch_key` 가 여럿이면 **변수마다 한 행**으로 쌓는다(2열 × 변수 수). `stim` 은 겹쳤는데
  donor 는 그대로 갈려 있는 상태가 그림 한 장에서 보여야 한다.
- **좌우를 조건별로 쪼개지 않는다.** 왼쪽=보정 전, 오른쪽=보정 후이지 왼쪽=ctrl,
  오른쪽=stim 이 아니다. 모든 패널에 전체 세포를 함께 그린다.
- **점 순서를 섞어서 그린다.** `adata` 순서대로 그리면 나중에 그려진 배치가 위를 덮어
  섞이지 않은 것을 섞인 것처럼(또는 그 반대로) 보이게 만든다. 인덱스를 셔플한 뷰로
  그리거나, 겹침이 보이도록 `alpha` 와 점 크기를 낮춘다.
- 파일명 예: `results/03_integration/figures/batch_mixing_before_after.png`.

```python
rng = np.random.default_rng(0)
view = adata[rng.permutation(adata.n_obs)]          # 그리는 순서를 섞는다
keys = ["stim", "donor"]                             # 이 단계에서 보정 대상으로 넣은 변수
fig, axes = plt.subplots(len(keys), 2, figsize=(13, 5.5 * len(keys)), squeeze=False)
for i, k in enumerate(keys):
    sc.pl.embedding(view, basis="umap_pre", color=k, ax=axes[i][0], show=False,
                    alpha=0.5, size=8, title=f"Before integration — {k}")
    sc.pl.umap(view, color=k, ax=axes[i][1], show=False,
               alpha=0.5, size=8, title=f"After integration — {k}")
```

> 보정 전 UMAP 은 **버리지 말고 남긴다.** `adata.obsm["X_umap_pre"]` 처럼 따로 보관해야
> `deg.md` 의 조건 DEG 그림과 `functional.md` 의 pathway 활성 UMAP 이 쓸 수 있다 — 거기서는 보정 **전**
> 임베딩이 기준이다. 보정 후 UMAP 으로 덮어쓰면 뒤 단계 그림을 다시 그릴 수 없다.

## 2. 과보정 확인 — 같은 임베딩에 세포 타입 구조를 얹는다

`batch_key` 가 완전히 겹쳤다는 것은 **좋은 신호이면서 동시에 위험 신호**다. 세포 타입까지
같이 뭉개면 배치는 완벽하게 섞인다. 그래서 1번과 **같은 보정 후 임베딩** 위에 구조가
남아 있는지 확인한다.

- 아직 annotation 전이므로 **주요 계통 marker 발현**(예: PBMC 면 `CD3D`·`CD14`·`MS4A1`·
  `GNLY`)을 색으로 얹은 패널을 나란히 그린다. 각 marker 가 **한 덩어리에 모여 있어야**
  한다 — 여러 덩어리로 흩어지면 과소보정, 전체에 고르게 번지면 과보정 쪽을 의심한다.
- 이 단계에서 이미 임시 clustering 을 돌렸다면 클러스터 색 패널을 함께 둔다.
- 파일명 예: `results/03_integration/figures/lineage_markers_after_integration.png`.

## 3. 겹침은 그림만으로 판정하지 않는다 — 표를 함께 남긴다

UMAP 에서 "섞여 보인다" 는 판정 근거가 아니다. 아래 중 최소 하나를 **CSV 표**로 남기고
그림과 같은 절에 배치한다.

- **클러스터(또는 임시 클러스터)별 `batch_key` 구성비** — 전체 비율과 얼마나 어긋나는지.
  한 클러스터가 한 배치로만 채워져 있으면 그 클러스터는 아직 안 겹친 것이다.
- **이웃 그래프 기준 섞임 정도** — 각 세포의 `n_neighbors` 이웃 중 다른 배치가 차지하는
  비율의 평균(간이 kBET/LISI 역할). 보정 전·후 값을 같은 표에 나란히 둔다.
- 이 데이터셋처럼 조건을 보정한 경우, **조건 반응 유전자**(IFN 반응이면 `ISG15`·`IFI6`·
  `MX1` 등)의 `stim`/`ctrl` 평균 발현을 보정 전·후로 나란히 적는다. 보정이 조건 신호를
  어디까지 지웠는지가 이 표에서 드러난다.

## 4. 결정 로그에 남길 것

`batch_key` 에 무엇을 넣었고 왜 넣었는지(특히 조건 변수를 넣었다면 clustering·annotation
목적이라는 것), 보정 후 `neighbors` 를 어느 표현형 위에서 만들었는지, 보정 전 임베딩을
어디에 보관했는지(뒤 단계가 쓴다), 3번 표에서 읽은 겹침 정도를 한 줄로 남긴다.
