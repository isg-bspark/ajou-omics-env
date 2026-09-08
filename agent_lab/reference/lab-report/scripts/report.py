#!/usr/bin/env python3
"""우리 랩 표준 보고서 생성기 (결정론적).

사용법:  python report.py run_data.json > report.md

run_data.json 의 값을 고정된 서식으로 markdown 보고서로 만든다.
LLM 을 거치지 않으므로 같은 입력이면 항상 바이트 단위로 동일한 출력이 나온다.
표준 라이브러리만 사용한다 (설치 불필요).
"""
import json
import sys


def _yn(v):
    return "O" if v else "X"


def build(data):
    ds = data["dataset"]
    run = data["run"]
    qc = data["qc"]
    de = data["de"]

    기준 = qc.get("기준", {})
    미토기준 = 기준.get("미토_%", "?")
    최소세포 = 기준.get("최소세포", "?")
    분석일 = str(run.get("생성시각", "")).split("T")[0]

    L = []
    L.append("# [랩표준] 흑색종 ICI scRNA-seq 차등발현 보고")
    L.append("")
    L.append("| 항목 | 값 |")
    L.append("|---|---|")
    L.append(f"| 데이터셋 | {ds.get('출처', '')} (ID {ds.get('id', '')}) |")
    L.append(f"| run_id | {run.get('run_id', '')} "
             f"(배치보정 {_yn(run.get('batch_corrected'))}, 클러스터 {run.get('클러스터_수', '?')}) |")
    L.append(f"| 분석일 | {분석일} |")
    L.append(f"| QC | {'통과' if qc.get('통과') else '실패'} — "
             f"미토 중앙값 {qc.get('미토_비율_중앙값_%', '?')}% (기준 {미토기준}%) |")
    L.append("")

    L.append("## Methods")
    L.append(f"전처리: 정규화 {_yn(run.get('normalize', True))} · "
             f"환자·배치 통합 {_yn(run.get('batch_corrected'))}. "
             f"QC 기준: 미토 < {미토기준}%, 최소세포 {최소세포}. "
             f"DE: 반응군 vs 비반응군, 환자 단위. 유의: padj < 0.05.")
    L.append("")

    L.append("## 결과 (반응군 vs 비반응군)")
    L.append("")
    L.append("| 세포유형 (Cell Ontology) | 유의 유전자 | 반응군 ↑ | 비반응군 ↑ |")
    L.append("|---|---|---|---|")
    for row in de:
        cl = str(row.get("cl_id", "")).strip()
        name = f"{row.get('세포_유형', '')} ({cl})" if cl else row.get("세포_유형", "")
        up_r = ", ".join(row.get("반응군_상향", [])) or "—"
        up_n = ", ".join(row.get("비반응군_상향", [])) or "—"
        L.append(f"| {name} | {row.get('유의_유전자_수', '?')} | {up_r} | {up_n} |")
    L.append("")

    L.append("## 한계")
    L.append("반응군·비반응군이 서로 다른 환자에 몰려 있어(환자↔응답 얽힘) 환자 교란 가능. "
             f"배치보정 {'적용' if run.get('batch_corrected') else '미적용'}.")
    L.append("")

    L.append("## 재현")
    L.append(f"run_id={run.get('run_id', '')} · qc_passed={run.get('qc_passed')} · "
             f"미토기준={미토기준}% · 최소세포={최소세포} · 생성={run.get('생성시각', '')}")
    L.append("")
    return "\n".join(L)


def main():
    if len(sys.argv) != 2:
        sys.exit("사용법: python report.py run_data.json")
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    sys.stdout.write(build(data))


if __name__ == "__main__":
    main()
