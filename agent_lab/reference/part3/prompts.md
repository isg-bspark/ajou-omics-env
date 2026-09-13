# 2일차 1교시 실습 프롬프트 모음 (복사용) · 기준값을 프롬프트에 쓰지 않는다

## ① SKILL 변형 · 파라미터
data/pbmc3k_mini.h5ad 를 scanpy 스킬로 QC 해줘
(SKILL.md 수정 뒤, 같은 문장 그대로 다시)

## ② MCP 변형 · 범위
NK 세포 마커로 NKG7 을 쓰려고 해. 우리 랩 기준으로 NKG7 이 세포독성 마커라는 근거 논문을 PMID 와 함께 찾아줘
(변형 전: BioMCP article_searcher · 변형 후: lab-mcp marker_evidence 가 불려야 함. 안 불리면 "우리 서버(lab-mcp)의 marker_evidence 로 다시")

## ③ SKILL 변형 · 워크플로우
'CD8-positive exhausted alpha-beta T cell' 의 Cell Ontology ID 를 OLS 로 찾아줘
out/qc.h5ad 의 NK cells 와 CD8 T cells 라벨이 맞는지 scanpy 스킬로 검증해서 표로 정리해줘
(변형 전 1회 · 변형(cp · merge · SKILL.md 단계 추가) 뒤 같은 문장 1회 → 마지막에 HTML 보고서 artifact 발행)
