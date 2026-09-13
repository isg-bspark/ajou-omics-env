# 정답본 — 막혔을 때만 여세요 (2일차 1교시 실습)

실습 안내는 저장소 루트의 [README_agentlab.md](../../README_agentlab.md) 입니다.

| 경로 | 언제 |
|---|---|
| `part3/lab_mcp.py` | ②에서 `agent_lab/lab_mcp.py` 가 안 뜰 때. 통째로 복사: `cp agent_lab/reference/part3/lab_mcp.py agent_lab/lab_mcp.py` |
| `part3/mcp.step1.json` · `part3/mcp.final.json` | ② 각 단계의 `.mcp.json` (biomcp·ols → +lab-mcp) |
| `part3/check_markers.py` | ③ 변형 1 — 스킬에 넣는 마커 검증 스크립트 |
| `part3/gene_signatures.lab.json` · `part3/merge_lab_signatures.py` | ③ 변형 2 — 우리 랩 마커 패널 병합 |
| `part3/scanpy_lab_defaults.md` | ① 변형 — SKILL.md 에 붙이는 우리 랩 QC 기본값 |
| `part3/scanpy_marker_step.md` | ③ 변형 3 — SKILL.md 에 붙이는 검증 워크플로우 |
| `part3/SKILL.final.md` | ①·③ 변형이 모두 적용된 scanpy SKILL.md 완성본 |
| `part3/settings.final.json` | ② 부록 — BioMCP 도구 범위 제한(클라이언트 권한) |
| `part3/prompts.md` | ①·②·③ 프롬프트 모음 |
| `skills/scanpy/` | `gh skill install` 이 안 될 때 `part3_setup.sh --with-skill` 이 복사하는 K-Dense scanpy 스킬 사본 |

전부 처음 상태로 되돌리려면:

```bash
bash agent_lab/part3_setup.sh
```
