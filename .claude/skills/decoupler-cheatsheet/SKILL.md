---
name: decoupler-cheatsheet
description: decoupler 2.x (기능 분석 — GSEA·pathway·전사인자 활성 추정) API 참조와 이 환경에서 자주 틀리는 지점 요약. decoupler 코드를 짜기 전, 또는 1.x/2.x 함수 이름이 헷갈릴 때, 또는 pseudobulk·조건 대비 기능 분석을 설계할 때 이 스킬을 먼저 읽는다. 트리거: "decoupler", "GSEA", "pathway 분석", "전사인자 활성", "기능 분석".
---

# decoupler 2.x · 기능 분석 API 요약

> 이 환경이 쓰는 버전은 **decoupler 2.2** 다.
> `decoupler 1.x` 와 함수 이름이 **전부 다르다.** LLM 이 학습한 코드 대부분은 1.x 이므로,
> 아래 표의 왼쪽 형태가 나오면 잘못된 것이다.

## ⚠ 1.x → 2.x 대응표

| decoupler 1.x (❌ 안 됨) | decoupler 2.x (✅) |
|---|---|
| `dc.run_aucell(mat, net)` | `dc.mt.aucell(data, net)` |
| `dc.run_ulm(mat, net)` | `dc.mt.ulm(data, net)` |
| `dc.run_gsea(mat, net)` | `dc.mt.gsea(data, net)` |
| `dc.run_ora(mat, net)` / `dc.get_ora_df(...)` | `dc.mt.ora(data, net)` |
| `dc.get_progeny(top=500)` | `dc.op.progeny(top=500)` |
| `dc.get_collectri()` | `dc.op.collectri()` |
| `dc.get_resource("MSigDB")` | `dc.op.resource("MSigDB")` |
| `dc.read_gmt(path)` | `dc.pp.read_gmt(path)` |
| `dc.get_pseudobulk(...)` | `dc.pp.pseudobulk(...)` |
| `dc.filter_by_expr(...)` | `dc.pp.filter_by_expr(...)` |
| `dc.get_acts(adata, "ulm_estimate")` | `dc.pp.get_obsm(adata, "score_ulm")` |
| `dc.plot_barplot(...)` | `dc.pl.barplot(...)` |
| `dc.rank_sources_groups(...)` | `dc.tl.rankby_group(...)` |
| `net` 컬럼 `source/target/weight` | 같음 (그대로) |
| 결과가 `adata.obsm["ulm_estimate"]` | `adata.obsm["score_ulm"]` · `adata.obsm["padj_ulm"]` |

```python
import decoupler as dc
print(dc.__version__)      # 2.2.x 여야 한다
dc.mt.show()               # 쓸 수 있는 방법 목록
```

---

## 1. 세 가지 입력

기능 분석은 항상 이 셋으로 구성된다. 코드를 짜기 전에 이 셋이 무엇인지 먼저 적는다.

| | 무엇 | |
|---|---|---|
| **readout** | 분자 수준 측정값 — 발현 행렬 또는 유전자별 통계량 | 세포×유전자 log-normalized, 또는 pseudobulk DE 의 Wald stat 한 줄 |
| **prior knowledge** | 유전자 집합(gene set) 또는 발자국(footprint) | Hallmark · Reactome · PROGENy · CollecTRI 등 |
| **method** | 농축 점수를 계산하는 통계 방법 | AUCell · GSEA · ULM · ORA |

셋 중 하나만 바꿔도 결과가 바뀐다. 셋을 다 기록하지 않은 기능 분석 결과는 재현할 수 없다.

---

## 2. 어디에 점수를 매기는가 — 이 선택이 결과를 가른다

| | readout | 쓰는 방법 | 답하는 질문 |
|---|---|---|---|
| **세포 수준** | `adata` (세포 × 유전자, log-normalized) | `aucell`(gene set) · `ulm`(footprint) | 이 세포는 **지금** 어떤 상태인가 |
| **조건 대비** | DataFrame 한 줄 (대비 × 유전자, DE 통계량) | `gsea` · `ulm` · `ora` | 조건 A 가 조건 B 대비 **무엇을 켰나** |

**둘은 다른 질문에 답한다.** 세포 수준 점수를 조건별로 평균 내는 것은 조건 대비가 아니다
(세포를 독립 표본으로 취급하게 되어 pseudoreplication 이 그대로 남는다).
조건을 비교하려면 **pseudobulk → DE → 통계량을 readout 으로** 넘긴다.

---

## 3. 입력 형태에 따라 반환값이 달라진다

`dc.mt.*` 는 모두 같은 규칙을 쓴다.

```python
# (a) AnnData 를 주면 → 제자리(in-place). 반환값 None
dc.mt.ulm(data=adata, net=progeny, tmin=5)
adata.obsm["score_ulm"]     # DataFrame (세포 × source)
adata.obsm["padj_ulm"]      # DataFrame (세포 × source)

# (b) DataFrame 을 주면 → (score, padj) 튜플
score, padj = dc.mt.gsea(data=stat_df, net=hallmark, tmin=15)
```

`aucell` 은 p 값이 없다 — `score_aucell` 만 생기고 `padj_aucell` 은 없다.

`obsm` 에 든 점수를 scanpy 로 그리려면 AnnData 로 꺼낸다.

```python
acts = dc.pp.get_obsm(adata=adata, key="score_ulm")   # 새 AnnData (세포 × source)
acts.obs = adata.obs                                   # 필요하면 메타데이터를 옮긴다
sc.pl.umap(acts, color=["JAK-STAT", "TNFa"], cmap="RdBu_r", vcenter=0)
```

---

## 4. 공통 인자

`dc.mt.*` 전부에 있다.

| 인자 | 기본값 | 뜻 |
|---|---|---|
| `data` | — | AnnData 또는 DataFrame (관측 × 유전자) |
| `net` | — | `source` · `target` (· `weight`) 컬럼의 long-format DataFrame |
| `tmin` | `5` | **데이터에 실제로 있는 유전자가 이보다 적은 집합은 버린다.** 아래 주의 |
| `layer` | `None` | 쓸 layer. `None` 이면 `.X` |
| `raw` | `False` | `adata.raw` 를 쓸지 |
| `verbose` | `False` | 진행 로그 |

> **`tmin` 을 그냥 두지 않는다.** 권고는 **10~15개 미만 집합을 버리는 것**이다.
> 작은 집합은 분산이 커서 검정 통계량이 불안정해진다.
> gene set 에는 `tmin=15`, footprint 에는 기본값(5) 그대로 두는 것이 보통이다.
> **CollecTRI 는 1,185개 TF 중 716개의 target 이 15개 미만**(중앙값 9)이라
> `tmin=15` 를 걸면 TF 의 60%가 사라진다 — footprint 는 애초에 target 수가 적게 설계돼 있다.
> (PROGENy 는 `top=500` 이라 202~500개로 영향이 없다.)
>
> 상한(예: 500개 초과 제외)은 `tmin` 이 해주지 않는다. `net` 을 직접 걸러야 한다.

```python
size = net.groupby("source").size()
keep = size[(size >= 15) & (size <= 500)].index
net = net[net["source"].isin(keep)]
```

## 5. 방법별 추가 인자

| 방법 | 유형 | 가중치 | p값 | 고유 인자 |
|---|---|---|---|---|
| `dc.mt.aucell` | competitive · 순위 기반 | ✗ | ✗ | `n_up` (상위 몇 개까지 볼지, 기본 = 유전자의 5%) |
| `dc.mt.gsea` | competitive · 순위 기반 | ✗ | ✓ | `times=1000` (permutation 횟수) · `seed=42` |
| `dc.mt.ora` | competitive · 과대표현 | ✗ | ✓ | `n_up`(상위 집합 크기) · `n_bg=20000`(배경) |
| `dc.mt.ulm` | competitive · 선형모델 | ✓ | ✓ | — |
| `dc.mt.mlm` | competitive · 다중선형 | ✓ | ✓ | — |
| `dc.mt.viper` | competitive | ✓ | ✓ | — |
| `dc.mt.gsva` · `zscore` · `waggr` · `udt` · `mdt` | — | 다양 | 다양 | `dc.mt.show()` 참고 |

`seed` 를 고정하지 않으면 `gsea` 결과가 실행할 때마다 조금씩 달라진다. **반드시 고정한다.**

---

## 6. prior knowledge 가져오기

```python
hallmark  = dc.op.hallmark(organism="human")                  # gene set  (source, target)
progeny   = dc.op.progeny(organism="human", top=500)          # footprint (source, target, weight)
collectri = dc.op.collectri(organism="human")                 # footprint (source, target, weight)
reactome  = dc.pp.read_gmt("data/genesets/reactome.gmt")      # gene set  (GMT 파일에서)
dc.op.show_resources()                                        # omnipath 에서 받을 수 있는 목록
```

`dc.op.*` 는 **omnipathdb.org 에 네트워크 요청을 보낸다.** 오프라인이거나 느리면
미리 받아 둔 캐시를 쓴다.

캐시는 저장소의 `data/genesets/` 에 이미 들어 있다. 무엇이 있는지는 이렇게 본다.

```bash
python3 tools/verify.py         # 무엇이 캐시돼 있는지 확인
```

```python
import pandas as pd
hallmark = pd.read_csv("data/genesets/hallmark.csv")          # source, target
progeny  = pd.read_csv("data/genesets/progeny.csv")           # source, target, weight
```

| 자원 | 유형 | 무엇 | 크기 |
|---|---|---|---|
| **Hallmark** (MSigDB H) | gene set | 잘 정의된 50개 생물학적 상태 | 집합 50개 · 중복 적음 |
| **Reactome** (MSigDB C2:CP) | gene set | 큐레이션된 경로 구성원 | 집합 1,600+ · **중복 심함** |
| **GO BP** (MSigDB C5) | gene set | 생물학적 과정 | 집합 7,000+ · 중복 매우 심함 |
| **PROGENy** | footprint | 신호경로 14개의 **하류 반응 유전자** + 부호 가중치 | 경로 14개 |
| **CollecTRI** | footprint | 전사인자 → 표적 유전자 + 활성/억제 부호 | TF 1,100+ |
| **CytoSig** | footprint | 사이토카인 자극 시그니처 | — |

> **`dc.op.hallmark()` 은 `HALLMARK_` 접두어를 떼고 돌려준다.**
> source 이름은 `INTERFERON_ALPHA_RESPONSE` 이지 `HALLMARK_INTERFERON_ALPHA_RESPONSE` 가
> 아니다. GMT 파일에서 읽은 이름과 섞어 쓰면 조용히 빈 결과가 나온다.
> 무엇이 들었는지는 항상 먼저 확인한다.
>
> ```python
> print(hallmark["source"].nunique(), "개 집합")
> print(sorted(hallmark["source"].unique())[:5])
> ```
>
> Hallmark 50개 집합의 크기는 **32~200개**(중앙값 199)다 — `tmin=15` 로는 하나도 안 잘린다.
> 반면 Reactome 은 2,105개 중 **710개**가 15개 미만이라 3분의 1이 잘린다.
> 잘린 개수를 항상 확인한다.

Reactome 을 omnipath 에서 받으려면 `resource("MSigDB")` 를 걸러야 한다.
`dc.op.resource` 는 `source`/`target` 이 아니라 **wide 형식**(`genesymbol` · `collection` · `geneset`)을
돌려주므로 직접 이름을 바꿔야 한다.

```python
msigdb  = dc.op.resource("MSigDB")
reactome = (msigdb[msigdb["collection"] == "reactome_pathways"]
            .rename(columns={"geneset": "source", "genesymbol": "target"})
            [["source", "target"]]
            .drop_duplicates())
```

**gene set 은 "이 경로의 구성원"** 이고, **footprint 는 "이 경로가 켜지면 변하는 유전자"** 다.
전사체 데이터에는 footprint 가 더 직접적으로 대응한다 — 경로 단백질의 mRNA 가
그 경로의 활성을 반영한다는 보장이 없기 때문이다.

---

## 7. pseudobulk → DE → 조건 대비 농축

```python
# 7-1. 세포 타입 안에서 (생물학적 반복 × 조건) 으로 합친다. 입력은 raw count 여야 한다.
pdata = dc.pp.pseudobulk(
    adata[adata.obs["cell_type"] == "CD14+ Monocytes"],
    sample_col="donor",          # 생물학적 반복 (도너 · 환자 등)
    groups_col="stim",           # 조건
    layer="counts",              # ★ raw count. log-normalized 를 넣으면 안 된다
    mode="sum",
)
# pdata.obs 에 psbulk_cells · psbulk_counts 가 생긴다
#   ※ decoupler 문서에는 psbulk_n_cells 로 적혀 있지만 실제 컬럼명은 psbulk_cells 다 (2.2.0 실측)
# pdata.layers["psbulk_props"] 에 유전자별 비영(非零) 세포 비율이 들어간다

# 7-2. 표본·유전자 거르기
dc.pp.filter_samples(pdata, min_cells=10, min_counts=1000)
dc.pl.filter_by_expr(pdata, group="stim")            # 임계값을 눈으로 정하는 보조 그림
genes = dc.pp.filter_by_expr(pdata, group="stim", min_count=10,
                             min_total_count=15, inplace=False)
pdata = pdata[:, genes].copy()

# 7-3. pydeseq2 로 DE. 여기서 나오는 통계량이 다음 단계의 readout 이다
#      아래는 pydeseq2 0.5.x 기준이다 (0.4 는 design 대신 design_factors 를 쓴다)
from pydeseq2.dds import DeseqDataSet
from pydeseq2.ds import DeseqStats

counts = pd.DataFrame(pdata.X, index=pdata.obs_names, columns=pdata.var_names).astype(int)
dds = DeseqDataSet(counts=counts, metadata=pdata.obs, design="~stim")
dds.deseq2()
res = DeseqStats(dds, contrast=["stim", "stim", "ctrl"])
res.summary()
df = res.results_df          # baseMean · log2FoldChange · lfcSE · stat · pvalue · padj

# 7-4. Wald 통계량 한 줄을 (대비 × 유전자) DataFrame 으로.
#      NaN 이 섞이면 농축이 조용히 틀어지므로 먼저 떨군다
stat_df = df[["stat"]].dropna().T.rename(index={"stat": "stim.vs.ctrl"})

# 7-5. 농축
score, padj = dc.mt.gsea(data=stat_df, net=hallmark, tmin=15, times=1000, seed=42)
score, padj = dc.mt.ulm(data=stat_df, net=progeny)          # footprint 는 ulm
```

**7-1 의 `layer="counts"` 가 가장 흔한 실수 지점이다.** `pseudobulk` 는 count 를 더하는
것이 기본 동작이고, pydeseq2 도 count 를 요구한다. log-normalized 값을 더하면 둘 다 틀린다.

---

## 8. 세포 수준 점수

> ⚠ **codespace/컨테이너처럼 메모리가 좁은 환경에서는 `adata.copy()` 로 시작하지 않는다.**
> 이 환경은 컨테이너 전체 메모리가 ~7.8GB인데 VSCode/Claude 관련 프로세스가 이미 5GB+ 를
> 쓰고 있어 실제 여유는 **~2GB 안팎**이다. 전체 AnnData(layers·obsp neighbor graph·여러
> UMAP embedding 포함)를 `adata.copy()` 로 통째로 복제한 뒤 `dc.mt.ulm`/`dc.mt.aucell` 을
> 돌리면 두 메모리 요구가 겹쳐 커널이 프로세스를 **조용히 SIGKILL** 한다 — 에러도
> 트레이스백도 없이 그냥 사라진다 (컨테이너엔 dmesg 권한도 없어 OOM 로그도 못 본다).
>
> 돌리기 전에 두 단계로 줄인다.
> 1. `adata.copy()` 대신, 필요한 `obs` 컬럼 몇 개 + `.X` (+ 필요하면 UMAP 좌표)만 골라
>    **새 AnnData**를 만든다. layers·obsp·불필요한 obsm 은 애초에 들고 오지 않는다.
> 2. 실제로 쓸 gene set/footprint(`net`)에 들어있는 유전자만 남기도록 `.X` 를 서브셋한다.
>    Hallmark 4개 + PROGENy 14개처럼 일부만 쓴다면 전체 유전자(1만+개) 중 `net["target"]`
>    에 있는 것만 남겨도 충분하다 — 이 축소만으로 유전자 수가 수천 개 단위로 줄어든다.
>
> ```python
> genes_needed = sorted(set(net["target"]) & set(adata.var_names))
> small = ad.AnnData(
>     X=adata[:, genes_needed].X,
>     obs=adata.obs[["cell_type", "stim", "donor"]].copy(),
>     var=adata.var.loc[genes_needed].copy(),
>     obsm={"X_umap": adata.obsm["X_umap"]},
> )
> ```

```python
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)

dc.mt.aucell(data=adata, net=hallmark, tmin=15)     # gene set  → obsm["score_aucell"]
dc.mt.ulm(data=adata, net=progeny)                  # footprint → obsm["score_ulm"], obsm["padj_ulm"]

acts = dc.pp.get_obsm(adata, key="score_ulm")
acts.obs = adata.obs
sc.pl.umap(acts, color="JAK-STAT", cmap="RdBu_r", vcenter=0)
sc.pl.violin(acts, keys="JAK-STAT", groupby="cell_type", rotation=90)

# 어느 세포 타입에서 어떤 source 가 특징적인가
markers = dc.tl.rankby_group(adata=acts, groupby="cell_type",
                             reference="rest", method="t-test_overestim_var")
```

> AUCell·z-score 처럼 **순위/분포에 기대는 방법은 정규화 방식에 민감하다.**
> 정규화를 바꿔서 결과가 크게 흔들리면 그 자체가 보고할 관찰이다.

---

## 9. 그림

```python
dc.pl.barplot(data=score, name="stim.vs.ctrl", top=15, vertical=True)
dc.pl.dotplot(df=long_df, x="score", y="source", c="score", s="-log10(padj)", top=20)
dc.pl.volcano(data=res, x="log2FoldChange", y="padj", net=hallmark,
              name="INTERFERON_ALPHA_RESPONSE")
fig, le_genes = dc.pl.leading_edge(df=res, net=hallmark, stat="stat",
                                   name="INTERFERON_ALPHA_RESPONSE")
dc.pl.source_targets(data=res, net=collectri, x="log2FoldChange", y="stat", name="STAT1")
dc.pl.network(net=hallmark, data=score, sources=["INTERFERON_ALPHA_RESPONSE"])
```

`dc.pl.leading_edge` 는 **그림과 함께 leading-edge 유전자 배열을 돌려준다.**
"이 경로가 나온 이유가 무엇인가" 를 유전자 이름으로 답할 수 있는 유일한 지점이니
상위 경로 두세 개에 대해서는 반드시 돌려서 표로 남긴다.

---

## 10. 자주 틀리는 곳

| 증상 | 원인 | 고치는 법 |
|---|---|---|
| `AttributeError: module 'decoupler' has no attribute 'run_ulm'` | 1.x 코드 | 위 1번 표 |
| 결과 집합이 몇 개 안 나온다 | `tmin` 에 걸려 대부분 잘렸다 | `verbose=True` 로 몇 개가 남았는지 확인 |
| `net` 의 source 이름이 데이터 유전자와 안 맞음 | 종(species) 불일치 · Ensembl ID vs symbol | `dc.op.translate(net)` · `adata.var_names` 확인 |
| GSEA 결과가 매번 다르다 | `seed` 미고정 | `seed=42` |
| pseudobulk 후 표본이 2~3개뿐 | 세포가 적은 타입 | `psbulk_cells` 를 보고 저신뢰로 표시하거나 제외 |
| 모든 경로의 padj 가 1.0 | 대비가 한 줄뿐이라 FDR 이 그 줄 안에서만 보정됨 (정상) · 또는 통계량이 전부 0 | `stat_df` 를 직접 출력해 확인 |
| 상위 경로가 서로 거의 같은 유전자 | gene set 중복 | Hallmark 로 바꾸거나, 상위 집합 간 Jaccard 를 표로 남긴다 |
| 배치 효과가 결과에 섞임 | 농축 방법은 배치를 **보정하지 않는다** | 앞 DE 단계에서 처리해야 한다 |

---

## 11. 남길 다섯 줄

1. 기능 분석에는 **readout · prior knowledge · method** 세 입력이 필요하다. 세포 수준에서도, 집단 수준에서도 돌릴 수 있다
2. gene set 은 발현이 단백질 활성을 반영한다고 **가정**한다. footprint 는 부호와 가중치가 붙은 하류 반응을 쓴다
3. **10~15개 미만의 집합은 걸러낸다.** 농축 전에 정규화를 제대로 한다
4. **competitive 검정이 self-contained 보다 낫다** — 유전자 수준 통계량 하나만 쓰므로 표본이 바뀌어도 안정적이다
5. **결과는 통계 방법의 선택보다 gene set 의 선택에 훨씬 민감하다** (Holland et al. 2020)

gene set 을 둘 이상, 통계 방법을 둘 이상 써서 상위 결과의 일치도를 재고, 무엇을 바꿨을 때
더 갈렸는지 적으면 5번 주장을 이 실험 안에서 직접 확인할 수 있다.

---

## 출처

- sc-best-practices, *Gene set enrichment and pathway analysis* — https://www.sc-best-practices.org/conditions/gsea-pathway/
- decoupler 문서 — https://decoupler.readthedocs.io/
- Badia-i-Mompel P, et al. **decoupleR: ensemble of computational methods to infer biological activities from omics data.** *Bioinformatics Advances* 2 (2022)
- Holland CH, et al. **Robustness and applicability of transcription factor and pathway analysis tools on single-cell RNA-seq data.** *Genome Biology* 21, 36 (2020)
- Subramanian A, et al. **Gene set enrichment analysis.** *PNAS* 102, 15545–15550 (2005)
