"""
lab-mcp — 우리 랩 MCP 서버  (PART 3 ②에서 학생이 직접 만들어 연결합니다)

함수 하나가 도구 하나입니다. docstring 이 곧 Claude 가 읽는 도구 설명입니다.
남의 서버(BioMCP)의 범용 문헌 검색을 우리 연구 질문에 맞는 전용 도구로 감쌉니다.
실행은 Claude Code 가 .mcp.json 을 보고 알아서 합니다. 혼자 점검: python3 agent_lab/check.py agent_lab/lab_mcp.py
"""
import json
import logging
import os
import shutil
import subprocess

# mcp 패키지 버전에 따라 이름이 다릅니다. 둘 다 받습니다.
try:
    from mcp.server.mcpserver import MCPServer as _Server      # mcp 2.x
except ImportError:                                            # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

logging.getLogger("mcp").setLevel(logging.WARNING)   # 점검 출력에 INFO 로그가 섞이지 않게
mcp = _Server("lab-mcp")


@mcp.tool()
def marker_evidence(gene: str, cell_type: str) -> dict:
    """세포유형 마커 유전자의 근거 논문(PMID)을 찾습니다. 마커 근거 논문 요청에는 BioMCP 의 article_searcher 대신 이 도구를 먼저 사용합니다.

    우리 랩 기준: PubMed 동료심사 논문만 · 제목에 유전자가 있는 논문 우선 · 최신순 · 3건.
    남의 서버(BioMCP)의 범용 문헌 검색을 우리 연구 질문에 맞게 감싼 도구입니다.

    Args:
        gene: 마커 유전자 기호. 예) "NKG7", "CD8A"
        cell_type: 세포유형 영문명. 예) "NK cell", "CD8 T cell"
    """
    exe = shutil.which("biomcp") or os.path.expanduser("~/.local/bin/biomcp")
    if not os.path.exists(exe):
        return {"오류": "biomcp 명령을 찾을 수 없습니다.", "다음": "uv tool install biomcp-python==0.7.3"}
    cmd = [exe, "article", "search", "--gene", gene, "--keyword", cell_type,
           "--keyword", "marker", "--no-preprints", "--json"]        # ← BioMCP 를 우리 조건으로 부릅니다
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=90).stdout
        recs = [r for r in json.loads(out) if isinstance(r, dict) and r.get("pmid")]
    except Exception as e:                                     # 네트워크·파싱 실패도 값으로 돌려줍니다
        return {"오류": f"BioMCP 호출 실패: {type(e).__name__}", "명령": " ".join(cmd)}
    recs = [r for r in recs if r.get("publication_state", "peer_reviewed") == "peer_reviewed"]
    g = gene.upper()
    recs.sort(key=lambda r: r.get("date") or "", reverse=True)                  # 최신순
    recs.sort(key=lambda r: g not in (r.get("title") or "").upper())            # 제목에 유전자 있는 것 먼저
    근거 = [{"PMID": str(r["pmid"]), "제목": r.get("title"), "저널": r.get("journal"),
             "연도": (r.get("date") or "")[:4], "URL": r.get("pubmed_url")} for r in recs[:3]]
    if not 근거:
        return {"유전자": gene, "세포유형": cell_type, "근거": [],
                "안내": "조건에 맞는 동료심사 논문이 없습니다. PMID 를 지어내지 않습니다."}
    return {"유전자": gene, "세포유형": cell_type,
            "기준": "PubMed 동료심사 · 제목에 유전자 포함 우선 · 최신순 · 3건",
            "근거": 근거,
            "다음": "보고 표에는 PMID 만 적고, 없는 PMID 는 지어내지 않습니다."}


if __name__ == "__main__":
    mcp.run()
