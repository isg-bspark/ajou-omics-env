# 정답본 — 막혔을 때만 여세요

| 파일 | 언제 |
|---|---|
| `server_완성본.py` | 2단계(differential_expression 에 QC 게이트)가 안 될 때. 완성된 서버 |
| `tool_qc_gate.py` | 2단계 정답 조각 (DE 에 넣는 QC 게이트) |
| `step1~3.mcp.json` | 각 단계가 끝난 시점의 `.mcp.json` |
| `lab-report/` | 4단계 시연 자산(우리 랩 보고표준) — `.claude/skills/` 로 복사해 씀 |

## 서버가 안 뜰 때 — 통째로 되돌리기

```bash
cp agent_lab/reference/server_완성본.py agent_lab/server.py
```

## `.mcp.json` 따라잡기

```bash
cp agent_lab/reference/step1.mcp.json .mcp.json   # 1단계 끝 (sc-omics)
cp agent_lab/reference/step3.mcp.json .mcp.json   # 3단계 끝 (+ ols)
```

> 2단계는 `.mcp.json` 이 아니라 `server.py` 를 고칩니다 (`step2` 는 `step1` 과 같음).
> 조각(`tool_qc_gate.py`)은 `differential_expression` 안에 넣는 게이트 코드입니다.

## 스킬 (4·5단계)

**4단계** 자산(우리 랩 보고표준)은 `lab-report/` 에 있습니다 — 시연 때 `.claude/skills/` 로 복사:

```bash
cp -r agent_lab/reference/lab-report .claude/skills/lab-report
```

`report.py`(결정론적 보고서) · `check_sop.py`(6요소 검증) · `run_data.sample.json` · `prose_sample.md`(FAIL 데모).

**5단계** `scanpy` 는 정답본을 두지 않습니다 — `gh skill install … scanpy` 로 실제로 가져옵니다.

전부 되돌리려면:

```bash
git checkout agent_lab/ .mcp.json && rm -rf .claude/skills/lab-report .claude/skills/scanpy
```
