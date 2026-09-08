---
name: lab-report
description: 오믹스 단일세포 차등발현(반응군 vs 비반응군) 분석을 우리 랩 표준 보고서로 정형화할 때 사용한다. run 데이터를 표준 서식(메타·Methods·결과표·Cell Ontology ID·한계·재현정보)으로 결정론적으로 생성하고 표준 준수를 검증한다.
allowed-tools: Read Write Bash
---

# 우리 랩 분석 보고 표준 (SOP)

분석 결과를 보고할 때는 **직접 서식을 지어내지 않는다.** 서식은 매번 같아야 하므로
아래 자산(스크립트)으로 **생성**하고 **검증**한다.

## 절차

1. **데이터 수집** — 도구로 값을 모아 `run_data.json` 으로 저장한다.
   - `dataset_overview` · `qc_check` · `differential_expression`
   - 각 세포유형의 **Cell Ontology ID 는 OLS(원격 MCP)로 조회**해 `cl_id` 에 넣는다.
     (예: 소진 CD8 T세포 → `CL:0020031`)
   - 입력 형식은 `references/report_standard.md` 참고.

2. **보고서 생성** — `python scripts/report.py run_data.json > report.md`
   - 이 스크립트가 표준 서식을 **결정론적으로** 만든다. 같은 입력이면 항상 같은 출력.
   - 서식을 손으로 바꾸지 않는다.

3. **표준 검증** — `python scripts/check_sop.py report.md`
   - 반드시 `PASS` 여야 한다. `FAIL` 이면 누락 항목(특히 **Cell Ontology ID**)을 채워 다시 생성한다.

## 원칙

- 흔들려도 되는 부분(무엇을 분석할지 · 도구 호출)은 **판단**으로,
  흔들리면 안 되는 부분(**서식 · 검증**)은 **코드**로.
- 세포유형에는 **반드시 Cell Ontology ID 병기**(OLS 조회) — 표준 명명.
- 보고서에는 **한계(환자 교란)** 와 **재현정보(run_id·qc_passed·기준값)** 를 항상 포함한다.
