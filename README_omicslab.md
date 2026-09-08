# 2일차 2교시 — IFN-beta 자극에 대한 면역세포 반응 분석

> **연구 질문** — IFN-beta 자극을 받은 말초혈액 면역세포(PBMC)는 세포 타입별로 어떻게 다르게 반응하는가?

1교시에서 만든 구조(MCP · SKILL) 위에서, 이번에는 **실제 single-cell RNA-seq 데이터로
분석 판단**을 합니다. 스킬을 받아 튜닝해 쓰고, 같은 질문을 서로 다른 진행 방식으로
동시에 돌려 비교합니다.

전체 실습 환경 안내는 [README.md](README.md) 를, 1교시는 [README_agentlab.md](README_agentlab.md) 를 보세요.

## 시작 전 점검

```bash
python3 tools/verify.py    # 패키지 · gene set 캐시 · 입력 데이터 점검
```

## 데이터

| 항목      | 내용                                                                                                                         |
| --------- | ---------------------------------------------------------------------------------------------------------------------------- |
| 출처      | [GSE96583](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE96583) — Kang et al., _Nat Biotechnol_ 2018 (demuxlet 논문) |
| 사용 범위 | batch2 — 대조군(GSM2560248) / IFN-beta 자극군(GSM2560249)                                                                    |
| 설계      | 루푸스 환자 8명의 PBMC, 조건당 8명 pooling 후 demuxlet 으로 공여자 판별                                                      |
| 파일      | `data/processed/gse96583_ifnb.h5ad` (11,998 세포 × 14,391 유전자, 18 MB)                                                     |

`.X` 에는 **정규화하지 않은 raw count** 가 들어 있습니다. QC · 정규화 · HVG 선별 · 통합 ·
클러스터링 · 차등발현은 실습에서 직접 수행할 부분이라 일부러 처리하지 않았습니다.

**미리 처리해 둔 것**

- demuxlet 이 doublet(3,169) / ambiguous(1,217) 로 판정한 세포 **제거 완료**
- 세포 타입이 할당되지 않은 세포 제거
- (조건 × 세포타입) 층화 다운샘플로 약 12,000 세포까지 축소 — 무료 Codespace 사양에서도 원활히 동작
- 3개 미만의 세포에서만 검출되는 유전자 제거

**일부러 넣지 않은 것**

- **세포 타입 주석** — 원 논문 저자들이 붙여 둔 세포 타입 라벨은 결과 파일에서 제외했습니다.
  클러스터링과 마커 유전자로 직접 주석을 붙이는 것이 실습의 핵심 과정이기 때문입니다.
  (층화 다운샘플 단계에서 세포 타입 구성 비율을 맞추는 데에만 내부적으로 사용했습니다)
- 정규화, HVG 선별, 배치 통합, 차원축소, 클러스터링 결과

**`obs` 컬럼**

| 컬럼                      | 설명                                     |
| ------------------------- | ---------------------------------------- |
| `stim`                    | `ctrl` (대조군) / `stim` (IFN-beta 자극) |
| `donor`                   | 공여자 ID (demuxlet 판별 결과)           |
| `total_counts`, `n_genes` | 기본 QC 지표                             |

> 참고 — 이 데이터는 유전자 목록에 미토콘드리아 유전자(`MT-`) 13개가 있지만 count 가 전부 0 입니다
> (원 저자가 미토콘드리아 리드를 제외함). 따라서 미토콘드리아 비율 기반 QC 는 적용할 수 없고,
> `total_counts` 와 `n_genes` 로 QC 를 진행합니다.

| 파일                                                  | 내용                                                                       |
| ----------------------------------------------------- | -------------------------------------------------------------------------- |
| `GSM2560248_2.1.mtx.gz`, `GSM2560248_barcodes.tsv.gz` | 대조군 count matrix / 바코드                                               |
| `GSM2560249_2.2.mtx.gz`, `GSM2560249_barcodes.tsv.gz` | IFN-beta 자극군 count matrix / 바코드                                      |
| `GSE96583_batch2.genes.tsv.gz`                        | 유전자 목록 (Ensembl ID + symbol)                                          |
| `GSE96583_batch2.total.tsne.df.tsv.gz`                | 세포 주석 (공여자, 조건, demuxlet singlet/doublet 판정, 원 저자 세포 타입) |

> 이 주석 파일에는 원 저자의 세포 타입 라벨이 그대로 들어 있습니다 (GEO 원본이라 손대지 않았습니다).
> 실습 중 정답을 미리 보지 않으려면 열어보지 마세요.

## 분석 범위 — 기능 분석까지 갑니다

이 분석은 QC → 클러스터링 → 주석 → 차등발현에서 끝나지 않고,
**조건 간 기능 분석(경로 · 전사인자 활성)** 까지 갑니다. 내용은
[sc-best-practices 의 Gene set enrichment and pathway analysis](https://www.sc-best-practices.org/conditions/gsea-pathway/)
챕터를 따랐습니다.

|                    |                                                                                                                                                   |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| 무엇을 하나        | 세포 수준 점수(AUCell · ULM) · pseudobulk 조건 대비(GSEA · ULM · ORA)                                                                             |
| 쓰는 자원          | MSigDB Hallmark · Reactome · PROGENy · CollecTRI                                                                                                  |
| 왜 pseudobulk 인가 | 도너가 8명, 조건마다 8명 전부 있습니다. (도너 × 조건)으로 합치면 **8 대 8** 의 진짜 반복이 되고, 세포 단위 검정의 pseudoreplication 이 해소됩니다 |
| 양성 대조          | IFN-beta 를 넣었으니 인터페론 반응이 최상위여야 합니다. **안 나오면 앞 단계가 깨진 것입니다**                                                     |

> **decoupler 는 2.0 에서 API 가 전면 개편되었습니다** (`dc.run_ulm` → `dc.mt.ulm`).
> LLM 이 학습한 코드 대부분은 1.x 라 Claude 가 옛 함수를 쓸 가능성이 높습니다.
> 대응표는 `.claude/skills/decoupler-cheatsheet/SKILL.md` 맨 앞에 있습니다.
> 이미 만들어 둔 Codespace 는 `pip install -U 'decoupler>=2.2,<3' 'pydeseq2>=0.5,<1'` 를 한 번 실행하세요.

## 분석 스킬 — 프롬프트를 복사-붙여넣기 하지 않습니다

분석 자체는 `.claude/skills/` 의 스킬로 시작합니다.

| 스킬                     | 진행 방식                                   |
| ------------------------ | ------------------------------------------- |
| `scrnaseq-plan-execute`  | 계획을 먼저 세우고 승인 후 끝까지 자율 실행 |
| `scrnaseq-stepwise-hitl` | 한 단계씩 가고 갈림길마다 사람에게 물음     |

| 곁들여 쓰는 것                  | 하는 일                               |
| ------------------------------- | ------------------------------------- |
| `decoupler-cheatsheet`          | decoupler 2.x API 대응표              |
| `scrnaseq-visualization-spec`   | 단계별로 반드시 그려야 하는 그림 규격 |
| `.claude/agents/step-validator` | 끝난 단계를 정확성 · 완결성으로 채점  |

## 병렬 실험 — 같은 질문을 서로 다른 진행 방식으로

한 연구 질문을 두고 **서로 다른 진행 방식을 동시에** 돌려 볼 수 있습니다.
터미널 두 개를 열고 각각 **저장소 루트**에서 `claude` 를 띄운 뒤, 한쪽에서
`/scrnaseq-plan-execute` 를, 다른 쪽에서 `/scrnaseq-stepwise-hitl` 을 부릅니다.
실험마다 작업 공간을 따로 만드는 일은 스킬이 알아서 합니다.

```bash
git add -A && git commit -m "병렬 실험 출발점"   # 실험은 마지막 커밋에서 갈라집니다
claude
```

스킬을 부르면 연구 질문을 물어봅니다. 두 터미널에 **같은 데이터, 같은 질문**을 주고
**진행 방식만 다르게** 적습니다.

자율 실행 쪽 (`/scrnaseq-plan-execute`):

> IFN-beta 자극에 대해 다양한 면역세포들이 어떻게 반응하는지를 연구하고 싶어.
> 데이터는 data 디렉토리 안에 있어. 연구 계획을 세우고 그 이후에는 네가 알아서
> 자발적으로 실행하도록해.

단계별 검토 쪽 (`/scrnaseq-stepwise-hitl`):

> IFN-beta 자극에 대해 다양한 면역세포들이 어떻게 반응하는지를 연구하고 싶어.
> 데이터는 data 디렉토리 안에 있어. 연구 계획을 세우고 실행하되 주요 단계가 끝날
> 때마다 나의 검토를 받았으면 해.

두 세션은 서로의 결과를 건드리지 않고 나란히 진행됩니다. 공용 입력 데이터는
그대로 함께 쓰고, 각 실험이 만드는 스크립트 · 중간 데이터 · 결과 · 그림만
실험별로 따로 쌓입니다. 끝난 뒤 두 쪽의 판단이 어디서 갈렸는지 비교해 보세요.

## 참고 문헌

Kang HM, Subramaniam M, Targ S, et al. **Multiplexed droplet single-cell RNA-sequencing using
natural genetic variation.** _Nature Biotechnology_ 36, 89–94 (2018).

Heumos L, Schaar AC, Lance C, et al. **Best practices for single-cell analysis across modalities.**
_Nature Reviews Genetics_ 24, 550–572 (2023). — https://www.sc-best-practices.org/

Badia-i-Mompel P, Vélez Santiago J, Braunger J, et al. **decoupleR: ensemble of computational
methods to infer biological activities from omics data.** _Bioinformatics Advances_ 2, vbac016 (2022).

Holland CH, Tanevski J, Perales-Patón J, et al. **Robustness and applicability of transcription
factor and pathway analysis tools on single-cell RNA-seq data.** _Genome Biology_ 21, 36 (2020).
