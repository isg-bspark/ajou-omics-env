"""
오믹스 분석 MCP 서버 — 정답본 (막혔을 때만 여세요)

실제 공개 데이터를 미리 분석한 결과를 돌려줍니다.
  데이터: Sade-Feldman et al., Cell 2018 (GEO GSE120575)
          흑색종 면역관문억제제(ICI) 치료 · 종양 침윤 면역세포(CD45+) 단일세포 RNA-seq

파이프라인: preprocess → qc_check(품질 합격 도장) → differential_expression
실습 2단계에서, differential_expression 에 "QC 통과한 run 만 받는다" 게이트를 직접 넣습니다.

계산은 하지 않고, 미리 넣어둔 값을 돌려줍니다.
실행은 Claude Code 가 알아서 합니다. 직접 켜지 않아도 됩니다.
"""

import json
from datetime import datetime
from pathlib import Path

# mcp 패키지 버전에 따라 이름이 다릅니다. 둘 다 받습니다.
try:
    from mcp.server.mcpserver import MCPServer as _Server      # mcp 2.x
except ImportError:                                            # pragma: no cover
    from mcp.server.fastmcp import FastMCP as _Server          # mcp 1.x

mcp = _Server("sc-omics")


# ────────────────────────────────────────────────────────────
#  미리 정리해둔 결과 (실제 데이터 GSE120575 기반).
# ────────────────────────────────────────────────────────────

DATASET_ID = "1214"

DATASET = {
    "설명": "흑색종 면역관문억제제(ICI) 치료 · 종양 침윤 면역세포(CD45+) 단일세포 RNA-seq",
    "플랫폼": "Smart-seq2",
    "출처": "Sade-Feldman et al., Cell 2018 (GEO GSE120575)",
    "세포_수": 16291,
    "샘플_수": 48,
    "환자_수": 32,
    "군_세포수": {"반응군": 5564, "비반응군": 10727},
    "요법_세포수": {"anti-PD1": 11653, "anti-CTLA4+PD1": 4121, "anti-CTLA4": 517},
    "시점_세포수": {"Pre(치료 전)": 5928, "Post(치료 중)": 10363},
    "환자_응답": {
        "반응군": [7, 8, 17, 19, 21, 24, 26, 29, 33, 35],
        "비반응군": [2, 3, 6, 10, 11, 12, 13, 14, 15, 16,
                     18, 20, 22, 23, 25, 27, 30, 31],
        "혼재": [1, 4, 5, 28],
    },
}

CELL_TYPES = ["CD8 T세포", "CD4 T세포", "조절 T세포(Treg)", "B세포",
              "형질세포", "NK세포", "단핵구/대식세포", "수지상세포"]

# 반응군 vs 비반응군 차등발현 — 세포 유형별 (이 연구의 실제 시그니처)
DE_SIGNATURES = {
    "CD8 T세포": {
        "반응군_상향": ["TCF7", "IL7R", "CCR7", "SELL", "GZMK"],
        "비반응군_상향": ["PDCD1", "HAVCR2", "LAG3", "TIGIT", "CD38", "ENTPD1", "TOX", "CTLA4"],
        "유의_유전자_수": 312,
    },
    "CD4 T세포": {
        "반응군_상향": ["TCF7", "IL7R", "CCR7"],
        "비반응군_상향": ["CTLA4", "TIGIT", "TNFRSF9", "FOXP3"],
        "유의_유전자_수": 118,
    },
    "조절 T세포(Treg)": {
        "반응군_상향": [],
        "비반응군_상향": ["FOXP3", "CTLA4", "TNFRSF9", "IL2RA"],
        "유의_유전자_수": 64,
    },
}

# 품질 지표 (Smart-seq2 · QC 전 스냅샷)
QC_METRICS = {
    "세포_수": 16291,
    "중앙값_유전자수": 4200,
    "미토_비율_중앙값_%": 8.1,
    "이중체_추정_%": 5.2,
}


# run 상태는 파일에 저장됩니다 — claude(서버)를 재시작해도 유지됩니다.
# QC 합격 여부(qc_passed)도 함께 기록/영속됩니다.
_RUNS_FILE = Path(__file__).resolve().parent.parent / ".runs.json"


def _load_runs() -> dict:
    try:
        return json.loads(_RUNS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_runs() -> None:
    try:
        _RUNS_FILE.write_text(json.dumps(_RUNS, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    except Exception:
        pass


_RUNS: dict[str, dict] = _load_runs()   # 서버가 들고 있는 상태 (파일에서 복원)


# ────────────────────────────────────────────────────────────
#  도구 ①  개요
# ────────────────────────────────────────────────────────────

@mcp.tool()
def dataset_overview(dataset_id: str) -> dict:
    """데이터셋 ID 로 그 데이터셋의 개요(규모 · 샘플 · 군 · 환자 · 요법)를 돌려줍니다.

    Args:
        dataset_id: 분석할 데이터셋 번호 (이 서버에는 "1214" 이 있습니다)
    """
    if DATASET_ID not in str(dataset_id):
        return {"거부": f"이 서버에는 데이터셋 {dataset_id} 이 없습니다.",
                "가진_데이터셋": [DATASET_ID]}
    return {"데이터셋_ID": DATASET_ID, **DATASET}


# ────────────────────────────────────────────────────────────
#  도구 ②  전처리
# ────────────────────────────────────────────────────────────

@mcp.tool()
def preprocess(normalize: bool = True, integrate: bool = False) -> dict:
    """전처리 파이프라인을 실행하고 run_id 를 돌려줍니다.

    결과 데이터가 아니라 손잡이(run_id)만 옵니다. 아직 QC 는 안 된 상태입니다.

    Args:
        normalize: 정규화 수행 여부
        integrate: 환자·배치 통합(보정) 수행 여부
    """
    run_id = "r_int" if integrate else "r_raw"
    _RUNS[run_id] = {
        "normalize": normalize,
        "batch_corrected": integrate,
        "클러스터_수": 11 if integrate else 16,
        "데이터셋": DATASET_ID,
        "qc_passed": False,                       # QC 전
        "생성시각": datetime.now().isoformat(timespec="seconds"),
    }
    _save_runs()
    return {
        "run_id": run_id,
        "batch_corrected": integrate,
        "클러스터_수": 11 if integrate else 16,
        "qc_passed": False,
        "상태": "전처리 완료 — qc_check 로 품질을 확인하세요.",
    }


# ────────────────────────────────────────────────────────────
#  도구 ③  품질 점검 (합격 여부를 run 에 기록 · 영속)
# ────────────────────────────────────────────────────────────

@mcp.tool()
def qc_check(run_id: str) -> dict:
    """전처리한 run 의 품질을 점검하고, 합격 여부를 run 에 기록합니다.

    Args:
        run_id: preprocess 이 돌려준 손잡이
    """
    run = _RUNS.get(run_id)
    if run is None:
        return {"거부": f"모르는 run_id 입니다: {run_id}",
                "다음": "preprocess() 를 먼저 부르세요."}

    q = QC_METRICS
    문제 = []
    if q["미토_비율_중앙값_%"] > 20:
        문제.append(f"미토 비율 중앙값 {q['미토_비율_중앙값_%']}% > 기준 20%")
    if q["세포_수"] < 500:
        문제.append(f"세포 수 {q['세포_수']} < 기준 500")

    run["qc_passed"] = (len(문제) == 0)          # ← 합격 도장을 run 에 기록
    _save_runs()                                 # ← 매번 영속 (.runs.json)

    if 문제:
        return {"통과": False, "사유": 문제, "지표": q}
    return {"통과": True, "지표": q,
            "다음": "이제 이 run 으로 differential_expression 을 쓸 수 있습니다."}


# ────────────────────────────────────────────────────────────
#  도구 ④  차등발현
#
#  실습 2단계: 아래 함수에 "QC 통과한 run 만 받는다" 게이트를 직접 넣습니다.
#  (qc_check 이 run["qc_passed"] 에 합격 여부를 기록해 둡니다. README_agentlab.md 2단계 참고)
# ────────────────────────────────────────────────────────────

@mcp.tool()
def differential_expression(run_id: str, cell_type: str) -> dict:
    """세포 유형 안에서 반응군 vs 비반응군 차등발현을 돌려줍니다.

    Args:
        run_id: preprocess 이 돌려준 손잡이
        cell_type: 예) "CD8 T세포"
    """
    run = _RUNS.get(run_id)
    if run is None:
        return {"거부": f"모르는 run_id 입니다: {run_id}",
                "다음": "preprocess() 를 먼저 부르세요."}

    if not run.get("qc_passed"):
        return {"거부": "QC 를 통과한 run 만 분석합니다.",
                "다음": "qc_check(run_id) 를 먼저 통과시키세요."}

    sig = DE_SIGNATURES.get(cell_type)
    if sig is None:
        return {"거부": f"{cell_type} 의 차등발현은 이 데이터셋에 준비돼 있지 않습니다.",
                "준비된_세포유형": list(DE_SIGNATURES)}
    return {"세포_유형": cell_type, **sig}


if __name__ == "__main__":
    mcp.run()
