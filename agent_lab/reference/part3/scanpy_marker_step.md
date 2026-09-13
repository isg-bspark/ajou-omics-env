## 우리 랩 워크플로우: Annotate 뒤 Marker 검증

`cell_type` 라벨이 있는 QC 통과 데이터(`out/qc.h5ad`)의 라벨을 검증할 때는 아래 순서로 하고,
마지막에 **HTML 보고서**로 정리한다. 데이터베이스 결과만 믿지 않는다. 우리 랩 패널의 발현(1)과
데이터베이스 대조(2)를 함께 보고 판정한다. (이 스킬은 라벨 검증만 한다. 클러스터링·어노테이션은 범위 밖.)

1. 패널 발현 확인 + 상위 마커 계산 (우리 스크립트):
   `python scripts/check_markers.py out/qc.h5ad --groupby cell_type --signatures assets/gene_signatures.json --top 8 --expect NK_lab="NK cells" CD8_T_lab="CD8 T cells"`
   출력의 판정(확인 / 약함 → 재검토 / 불일치)과 라벨별 상위 마커 8개를 그대로 쓴다.
2. 데이터베이스 대조: 라벨별 상위 마커 8개를 BioMCP `enrichr_analyzer(genes=[...], database="celltypes")` 에 넣어 상위 3개 세포유형을 받는다.
3. 문헌 근거: 패널 대표 마커 1개(NK cells → NKG7, CD8 T cells → CD8A)를 **우리 서버** lab-mcp 의 `marker_evidence(gene=마커, cell_type=세포유형 영문명)` 으로 조회해 PMID 1건을 받는다. (BioMCP 를 우리 기준으로 감싼 도구)
4. 표준 명명: OLS `searchClasses(query=<Cell Ontology 정식 명칭>, ontologyId="cl")` 로 CL ID 를 받는다. 질의는 정식 명칭으로 한다 (NK cells → "natural killer cell", CD8 T cells → "CD8-positive, alpha-beta T cell").
5. 표 구성: `라벨 | 세포 수 | 패널 발현% (해당 라벨 / 다른 라벨 최대) | 판정 | DB 상위 유형 | CL ID | 대표 마커 · PMID`. 못 찾은 칸은 비워 두고 지어내지 않는다. 판정이 "재검토"면 이유(예: CD8A 검출 46%)를 덧붙인다.
6. 보고서: 위 표를 **자체완결 HTML 보고서**로 만들어 `out/label_report.html` 에 저장하고, **artifact 로 발행**한다. 판정 배지(확인/재검토), CL ID, PMID 링크(https://pubmed.ncbi.nlm.nih.gov/<PMID>/)를 넣는다. 외부 스크립트·CSS 없이 한 파일로 완결한다.
