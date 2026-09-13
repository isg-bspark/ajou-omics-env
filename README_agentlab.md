# 2일차 1교시 실습 · 기존 Skill과 MCP를 내 워크플로우에 맞게 변형하기 (30분)

> 전체 실습 환경 안내는 [README.md](README.md) 를, 2교시는 [README_omicslab.md](README_omicslab.md) 를 보세요.

우리 랩은 **NK 세포의 세포독성 상태**를 연구한다. 오늘은 공개 PBMC 데이터(10x, 1,000세포)를 재사용하려 한다. 이 데이터에는 저자가 붙인 세포유형 라벨이 있는데, 우리 연구는 **NK 라벨이 정확해야** 성립한다. 그런데 NK와 세포독성 CD8 T는 마커가 겹쳐 헷갈리기 쉽다. 그래서 남의 QC를 우리 기준으로 다시 걸고(①), 마커 근거를 우리 기준으로 받는 도구를 만들고(②), 라벨 검증 절차를 우리 방식으로 스킬에 심는다(③).

전제는 하나다. MCP와 Skill을 **연결하는 법은 이미 안다.** 오늘은 연결을 넘어 **변형**한다. 남의 것을 가져와 내 연구 방식에 맞게 고치는 경험이다.

> 데이터: `data/pbmc3k_mini.h5ad` (저자 세포유형 라벨 포함. 저자 QC 에서 빠진 세포는 라벨이 없다.)

```
①  SKILL 변형 · 파라미터      QC 기준을 우리 랩 것으로            9분   재시작 없음
②  MCP  변형 · 내 서버       마커 근거 도구를 만들어 연결          8분   재시작 2회
③  SKILL 변형 · 워크플로우    라벨 검증 절차를 심고 HTML 보고서     11분  재시작 없음
정리                                                             2분
```

---

## 0. 시작 상태 (1분)

```bash
bash agent_lab/part3_setup.sh      # .mcp.json 비움 · settings.json allow 만 · 스킬/서버 없음 · 점검
claude
```
```
/model         ← 학생과 같은 모델(Sonnet)인지 확인
/skills        ← scanpy 없음 (①에서 설치)
/mcp           ← 서버 없음 (②에서 연결)
```

---

## ① SKILL 변형 · QC 기준 (9분)

scRNA-seq 의 첫 관문은 QC 다. 세포를 잡는 과정은 완벽하지 않아 죽어가는 세포, 빈 방울, 두 세포가 한 방울에 겹친 이중체가 섞인다. 이걸 걸러야 뒤 분석이 산다. 대표 지표가 **미토콘드리아 비율**이다. 세포가 죽으면 막이 터져 세포질 mRNA 가 새어 나가고, 미토콘드리아 안의 mRNA 는 상대적으로 남아 그 비율이 오른다. 그래서 미토 비율이 높은 세포는 죽어가는 세포로 보고 뺀다.

문제는 **그 기준값이 조직마다 다르다**는 것이다. PBMC 는 5~10%, 종양이나 심장 조직은 훨씬 높다. 남이 만든 스킬은 PBMC 튜토리얼 기본값(미토 5%)을 쓴다. 우리 랩 기준(10%)이 아니다. 그래서 스킬을 그대로 쓰지 않고, 우리 기준을 스킬 문서에 심는다.

**연결** — 남의 스킬을 가져온다 (10초).
```bash
gh skill install K-Dense-AI/scientific-agent-skills scanpy --agent claude-code
```
> 안 되면: `bash agent_lab/part3_setup.sh --with-skill` (저장소에 든 사본으로 설치)

**실행** — 기준을 말하지 말고 QC 만 시킨다.
```
data/pbmc3k_mini.h5ad 를 scanpy 스킬로 QC 해줘
```
> `Skill(scanpy)` 가 불리고 `scripts/qc_analysis.py` 가 **스킬 기본값** `--mt-threshold 5 --min-genes 200` 으로 돈다. 결과: `Cells 1000 -> 943 (94.3% kept)`.
> Claude 요약에는 기준값(5%)이 안 보인다. **"Ran 1 shell command" 를 클릭해 펼치면** 명령줄에 임계값이 없다 = 스크립트 기본값 5% 다. 이게 PBMC 튜토리얼 기준이지 우리 것이 아니다.

**변형** — 우리 랩 기준을 스킬 문서에 심는다. `.claude/skills/scanpy/SKILL.md` **맨 끝**에 붙인다.
```markdown
## 우리 랩 기본값 (10x PBMC)

QC 는 `scripts/qc_analysis.py` 로 실행한다. 사용자가 기준을 말하지 않으면 아래를 기본으로 쓴다.
`--mt-threshold 10 --min-genes 500 --max-genes 2500 --no-plots -o out/qc.h5ad`
근거: 미토 10% 초과는 죽어가는 세포, 유전자 500 미만은 빈 방울·저품질, 2,500 초과는 이중체 후보로 제외한다.
`--scrublet` 옵션은 쓰지 않는다. 실행 뒤 통과 세포 수(전/후)를 보고한다.
```

**확인** — 같은 문장을 그대로 다시.
```
data/pbmc3k_mini.h5ad 를 scanpy 스킬로 QC 해줘
```
> 명령줄이 우리 랩 값으로 바뀌고 `out/qc.h5ad` 가 생긴다. `Cells 1000 -> 890 (89.0% kept)`. 943 대 890 = 더 엄격한 기준에 53세포가 더 빠졌다.
> **재시작 없음.** 문서 네 줄이 행동을 바꿨다. 스킬은 프로그램이 아니라 문서라 매 턴 다시 읽히기 때문이다. 남의 스킬이라도 내 사본은 내 것이다.
> (참고: 이 스킬의 `assets/pipeline_config.json` 은 미토 10% 인데 `qc_analysis.py` 기본값은 5% 다. 남의 스킬은 안에서도 어긋난다. 우리 기본값이 그것을 정리한다.)

---

## ② MCP 변형 · 내 서버 만들어 연결하기 (8분)

라벨을 검증하려면 "이 세포유형은 이 마커"라는 근거가 필요하다. 그 근거는 **재현 가능해야** 한다. 논문에 "왜 이 마커냐"를 쓸 수 있어야 하고, 리뷰어가 물으면 문헌을 대야 한다. BioMCP 같은 남의 서버는 문헌을 잘 찾아 주지만, **검색 조건을 매번 Agent 가 정한다.** 같은 질문에도 키워드와 건수가 달라지고, 우리 질문과 무관한 변이 요약까지 딸려 온다. 우리 랩은 근거를 항상 같은 기준으로 받고 싶다: 동료심사 논문만, 제목에 유전자가 있는 것 우선, 3건. 그 기준을 남의 서버 위에 **우리 도구로 감싼다.** 이게 MCP 변형이다.

**연결** — 남의 서버 두 개를 붙인다. `.mcp.json` **전체를** 아래로 교체하고 `/exit` → `claude`.
```json
{
  "mcpServers": {
    "biomcp": { "type": "stdio", "command": "biomcp", "args": ["run"] },
    "ols":    { "type": "http",  "url": "https://www.ebi.ac.uk/ols4/api/mcp" }
  }
}
```
```
/mcp           ← biomcp(도구 36개) · ols(도구 12개) connected
```

**실행** — 나중에 라벨 검증에 쓸 마커의 근거를 확인한다. 재시작한 Claude 는 앞 대화를 모르므로 문장은 그 자체로 완결되어야 한다.
```
NK 세포 마커로 NKG7 을 쓰려고 해. 우리 랩 기준으로 NKG7 이 세포독성 마커라는 근거 논문을 PMID 와 함께 찾아줘
```
> Claude 가 BioMCP 의 `article_searcher` 를 부른다. 답은 나온다(PMID 40538191). 그런데 도구 결과를 펼쳐 보면 **검색 조건을 Claude 가 매번 정한다.** 같은 문장인데 실행마다 키워드 수가 다르고, 초록 10편 전체와 cBioPortal 변이 요약이 컨텍스트로 들어온다. "우리 랩 기준" 이 무엇인지 Claude 는 모른다.

**변형** — 그 기준을 담은 **내 서버를 만든다.** 새 파일 `agent_lab/lab_mcp.py` 를 만들고 아래를 **전체 그대로** 넣는다 (`cp agent_lab/reference/part3/lab_mcp.py agent_lab/lab_mcp.py` 로 가져와도 된다).
```python
"""
lab-mcp — 우리 랩 MCP 서버  (1교시 실습 ②에서 학생이 직접 만들어 연결합니다)

함수 하나가 도구 하나입니다. docstring 이 곧 Claude 가 읽는 도구 설명입니다.
남의 서버(BioMCP)의 범용 문헌 검색을 우리 연구 질문에 맞는 전용 도구로 감쌉니다.
"""
import json
import logging
import os
import shutil
import subprocess

try:
    from mcp.server.mcpserver import MCPServer as _Server      # mcp 2.x
except ImportError:                                            # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

logging.getLogger("mcp").setLevel(logging.WARNING)
mcp = _Server("lab-mcp")


@mcp.tool()
def marker_evidence(gene: str, cell_type: str) -> dict:
    """세포유형 마커 유전자의 근거 논문(PMID)을 찾습니다. 마커 근거 논문 요청에는 BioMCP 의 article_searcher 대신 이 도구를 먼저 사용합니다.

    우리 랩 기준: PubMed 동료심사 논문만 · 제목에 유전자가 있는 논문 우선 · 최신순 · 3건.

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
    except Exception as e:
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
```
읽을 곳은 셋이다. `@mcp.tool()` 아래 **함수 하나가 도구 하나**, docstring 첫 줄이 Claude 가 도구를 고를 때 읽는 **설명**, `cmd = [...]` 와 `recs.sort(...)` 가 BioMCP 를 **우리 조건**으로 부르고 정렬하는 곳이다. 검색 조건이 Claude 의 판단에서 우리 코드로 옮겨 왔다.

혼자 뜨는지 확인하고, 내 서버를 연결한다. `.mcp.json` **전체를** 아래로 교체하고 `/exit` → `claude`. 서버는 프로그램이라 새로 띄워야 목록에 들어온다.
```bash
python3 agent_lab/check.py agent_lab/lab_mcp.py     # 도구 1개: marker_evidence(gene, cell_type)
```
```json
{
  "mcpServers": {
    "lab-mcp": { "type": "stdio", "command": "python3", "args": ["agent_lab/lab_mcp.py"] },
    "biomcp":  { "type": "stdio", "command": "biomcp",  "args": ["run"] },
    "ols":     { "type": "http",  "url": "https://www.ebi.ac.uk/ols4/api/mcp" }
  }
}
```

**확인** — 같은 문장을 그대로 다시.
```
NK 세포 마커로 NKG7 을 쓰려고 해. 우리 랩 기준으로 NKG7 이 세포독성 마커라는 근거 논문을 PMID 와 함께 찾아줘
```
> 이번엔 "우리 랩 기준" 이라는 말에서 Claude 가 **`lab-mcp` 의 `marker_evidence`** 를 고른다. 결과는 PMID · 제목 · 저널 · 연도 3건의 **고정 형식**이고, 첫 건이 40538191 이다. 검색 조건은 이제 우리 코드가 정한다.
> 여전히 BioMCP 를 고르면 "우리 서버(lab-mcp)의 marker_evidence 로 다시" 라고 한 번 말한다. 어느 도구를 고르는지는 **도구 설명(docstring)** 과 **요청 문장**이 좌우한다. ③에서는 스킬 규칙이 이 도구를 지정해 지목 없이도 쓰인다.

> 부록(시간이 남으면): Claude Code 권한 설정으로 BioMCP 의 임상시험·변이·FDA 도구를 시야에서 지울 수도 있다 (`.claude/settings.json` deny, [agent_lab/reference/part3/settings.final.json](agent_lab/reference/part3/settings.final.json)). 이것은 MCP 를 고치는 것이 아니라 **클라이언트 설정**이다.

---

## ③ SKILL 변형 · 라벨 검증 워크플로우 (11분)

이제 본론이다. **저자가 붙인 라벨을 믿어도 될까?**

단일세포 데이터는 "이건 NK"라고 알려주지 않는다. 누군가 세포를 무리 짓고 마커 발현을 보고 이름을 붙인다. 마커는 특정 세포유형에서 두드러지게 켜지는 유전자다. 문제는 **면역세포끼리 마커를 공유**한다는 것. NK 와 세포독성 CD8 T 는 둘 다 세포를 죽이고, 그래서 `NKG7`·`GZMB`·`PRF1` 같은 세포독성 유전자를 함께 켠다. `NKG7` 조차 "NK 전용"이 아니라 "세포독성" 마커다.

여기에 **드롭아웃**이라는 함정이 겹친다. 발현이 낮은 유전자는 켜져 있어도 시퀀싱에서 자주 0 으로 잡힌다. `CD8A`·`CD8B` 는 저발현 표면 유전자라 진짜 CD8 T 에서도 절반 정도만 검출된다. 반대로 `NKG7`·`GNLY` 는 과립에 잔뜩 든 고발현 유전자라 거의 다 잡힌다. 그래서 같은 데이터에서 **NK 라벨은 선명하고 CD8 라벨은 흐릿하다.** 오류가 아니라 scRNA-seq 의 성질이다.

그리고 저자 라벨은 정답이 아니다. 그 라벨도 결국 마커에서 나왔다. 우리가 다시 마커로 보는 건 정답 맞히기가 아니라 **일관성 점검**이다. 그래서 마커 하나, 데이터베이스 하나로는 부족하다. 우리 패널 발현 + 데이터베이스 대조 + 문헌 + 표준 ID 를 겹친다.

이 검증을 **이번 한 번만** 하나? 데이터셋마다 한다. Agent 에게 매번 시키면 매번 다르게 한다 — 아래에서 직접 볼 것이다. 그래서 이 절차를 스킬에 한 번 적어, 다음 데이터셋도 자동으로 같은 절차를 타게 한다. Agent 는 이미 요리할 줄 안다. 우리는 그 위에 **우리 랩 레시피**를 얹는다.

**연결** — OLS 는 ②에서 이미 붙었다. 표준 ID 를 하나 물어본다.
```
'CD8-positive exhausted alpha-beta T cell' 의 Cell Ontology ID 를 OLS 로 찾아줘
```
> `CL:0020031`. 브라우저로 `http://purl.obolibrary.org/obo/CL_0020031` 을 열면 **진짜 있는 ID** 다. 표준 ID 는 다른 연구와 이어 붙일 수 있는 공통 이름이다.

**실행 (변형 전)** — 우리 절차가 없는 상태에서 검증을 시킨다.
```
out/qc.h5ad 의 NK cells 와 CD8 T cells 라벨이 맞는지 scanpy 스킬로 검증해서 표로 정리해줘
```
> Claude 가 **즉흥으로** 한다. 스킬은 로드되지만 스킬 스크립트 대신 자체 scanpy 코드를 짜서, 마커를 스스로 고르고 결과를 `/tmp` 에 저장한다. 표가 나오더라도 마커·판정 기준·근거가 실행마다 다르고, 표준 ID 도 문헌도 없다. **잘하지만 재현되지 않는다.**
> 도구 결과를 펼쳐 무엇을 어떤 순서로 했는지 적어 둔다. 변형 후와 비교할 자료다.

**변형 1 · 우리 스크립트를 스킬에 추가** — 라벨별로 우리 패널의 **검출 세포 비율(%)** 과 상위 마커를 계산한다. 드롭아웃 때문에 평균보다 검출률이 견고한 신호다.
```bash
cp agent_lab/reference/part3/check_markers.py .claude/skills/scanpy/scripts/
```

**변형 2 · 우리 랩 마커 패널을 스킬 assets 에 추가** — 스킬이 개인화용으로 배포한 `assets/gene_signatures.json` 에 우리 패널 5개를 합친다. Agent 가 매번 마커를 새로 고르지 않게, 우리 캐노니컬 패널을 고정한다.
```bash
python3 agent_lab/reference/part3/merge_lab_signatures.py
grep -c "_lab" .claude/skills/scanpy/assets/gene_signatures.json      # 5 가 나오면 성공
```

**변형 3 · 워크플로우 단계 추가** — `.claude/skills/scanpy/SKILL.md` 맨 끝에 붙인다. 네 종류의 증거를 겹치고, 마지막에 HTML 보고서로 낸다.
```markdown
## 우리 랩 워크플로우: Annotate 뒤 Marker 검증

`cell_type` 라벨이 있는 QC 통과 데이터(`out/qc.h5ad`)의 라벨을 검증할 때는 아래 순서로 하고,
마지막에 HTML 보고서로 정리한다. 데이터베이스 결과만 믿지 않는다. 우리 랩 패널의 발현(1)과
데이터베이스 대조(2)를 함께 보고 판정한다. (이 스킬은 라벨 검증만 한다. 클러스터링·어노테이션은 범위 밖.)

1. 패널 발현 확인 + 상위 마커 계산 (우리 스크립트):
   `python scripts/check_markers.py out/qc.h5ad --groupby cell_type --signatures assets/gene_signatures.json --top 8 --expect NK_lab="NK cells" CD8_T_lab="CD8 T cells"`
   출력의 판정(확인 / 약함 → 재검토 / 불일치)과 라벨별 상위 마커 8개를 그대로 쓴다.
2. 데이터베이스 대조: 라벨별 상위 마커 8개를 BioMCP `enrichr_analyzer(genes=[...], database="celltypes")` 에 넣어 상위 3개 세포유형을 받는다.
3. 문헌 근거: 패널 대표 마커 1개(NK cells → NKG7, CD8 T cells → CD8A)를 우리 서버 lab-mcp 의 `marker_evidence(gene=마커, cell_type=세포유형 영문명)` 으로 조회해 PMID 1건을 받는다.
4. 표준 명명: OLS `searchClasses(query=<Cell Ontology 정식 명칭>, ontologyId="cl")` 로 CL ID 를 받는다. 질의는 정식 명칭으로 한다 (NK cells → "natural killer cell", CD8 T cells → "CD8-positive, alpha-beta T cell").
5. 표 구성: `라벨 | 세포 수 | 패널 발현% (해당 라벨 / 다른 라벨 최대) | 판정 | DB 상위 유형 | CL ID | 대표 마커 · PMID`. 못 찾은 칸은 비워 두고 지어내지 않는다. 판정이 "재검토"면 이유(예: CD8A 검출 46%)를 덧붙인다.
6. 보고서: 위 표를 자체완결 HTML 보고서로 만들어 `out/label_report.html` 에 저장하고, artifact 로 발행한다. 판정 배지(확인/재검토), CL ID, PMID 링크를 넣는다. 외부 스크립트·CSS 없이 한 파일로 완결한다.
```

**확인 (변형 후)** — 같은 문장을 그대로 다시.
```
out/qc.h5ad 의 NK cells 와 CD8 T cells 라벨이 맞는지 scanpy 스킬로 검증해서 표로 정리해줘
```
> 이번엔 SKILL.md 단계대로 움직인다: `check_markers.py` → BioMCP `enrichr_analyzer` ×2 → lab-mcp `marker_evidence` ×2 → OLS `searchClasses` ×2 → **HTML 보고서 → artifact 발행.**
> 결말을 데이터가 낸다:
> - **NK cells: 확인.** 패널 79% (다른 라벨 최대 33%). NKG7 100% · GNLY 96% · PRF1 96%. 우리 연구의 NK 라벨은 안심해도 된다. CL:0000623.
> - **CD8 T cells: 약함 → 재검토.** CD3D 90% 로 T 세포는 확실하나 CD8A 46% · CD8B 35%. 앞 소개대로 드롭아웃 때문일 수도, 실제 혼재일 수도 있다. "재검토" 는 오분류 단정이 아니라 **사람이 다시 보라는 플래그**다. CL:0000625.
> 발행된 artifact 링크를 열면 판정 배지와 PMID 링크가 붙은 보고서가 보인다. 다음 세션에서 같은 요청을 해도 같은 절차, 같은 보고서가 나온다.

---

## 정리 (2분)

```
                고친 곳                                  무엇이 바뀌었나
①  SKILL.md 4줄   (남의 스킬 · 문서)                    QC 기준 5/200 → 10/500~2500 (우리 조직 기준)
②  lab_mcp.py 새 서버 (내 서버 · 코드)                    범용 문헌 검색 → 우리 기준 전용 도구(PMID 3건)
③  스크립트+패널+SKILL.md 단계 (남의 스킬 · 절차)          라벨 검증 SOP: 발현→DB→문헌→표준명→HTML 보고서
```
**연결을 넘어 변형으로.** MCP = 무엇을 사용할지 · SKILL = 어떻게 할지. 스킬은 문서·스크립트·assets 로, MCP 는 내 서버의 코드로 고친다. 남의 서버는 그대로 두고 감싼다. 마지막 요청 하나에 오늘 고친 세 곳이 전부 쓰였고, **결론은 데이터가 냈다.** 다음 데이터셋에도 이 Agent 는 우리 랩 방식으로 움직인다.

---

## 안 될 때

| 증상 | 해볼 것 |
|---|---|
| `gh skill install` 실패 | `bash agent_lab/part3_setup.sh --with-skill` |
| ① 두 번째 실행에도 플래그가 안 바뀜 | SKILL.md 맨 끝에 붙였는지 · 프롬프트에 기준을 쓰지 않았는지 → 그래도 안 되면 `/exit` → `claude` |
| ① Agent 가 `--scrublet` 을 붙여 오류 | 이 스킬 버그(scikit-image 필요). "우리 랩 기본값대로 scrublet 없이" 라고 한 번 더 말한다 |
| `/mcp` 에 서버가 빠져 있다 | `.mcp.json` 쉼표·중괄호 확인 → `agent_lab/reference/part3/mcp.final.json` 복사 · `python3 agent_lab/check.py agent_lab/lab_mcp.py` · `biomcp --version` |
| `ols` 가 안 붙는다 | 네트워크 정책. ③의 CL ID 는 `CL:0000623 (NK)` · `CL:0000625 (CD8 T)` 로 손으로 채운다 |
| ② `check.py` 가 "서버가 못 떴습니다" | 파일을 전체 그대로 넣었는지(`...` 생략 없음) · `cp agent_lab/reference/part3/lab_mcp.py agent_lab/lab_mcp.py` 로 통째 교체 |
| ② 두 번째에도 BioMCP `article_searcher` 를 쓴다 | `/mcp` 에 lab-mcp connected 인지(재시작) · 문장에 "우리 랩 기준으로" 가 있는지 · "우리 서버(lab-mcp)의 marker_evidence 로 다시" |
| ② `marker_evidence` 가 오류를 돌려준다 | 터미널에서 `biomcp --version` · 네트워크(PubMed) |
| ③ `check_markers.py` 를 못 찾는다 | 변형 1 의 `cp` 를 했는지 · `ls .claude/skills/scanpy/scripts/` |
| ③ `NK_lab` 시그니처가 없다 | 변형 2 의 `merge_lab_signatures.py` 를 했는지 |
| ③ artifact 발행이 안 된다 | `out/label_report.html` 로는 저장됨 → VS Code 에서 열기(우클릭 Open Preview) · "artifact 로 발행해줘" 재요청 |
| `No module named scanpy` | 코드스페이스 이미지 밖에서 실행 중. `python3 -c "import scanpy"` 확인 |
| 처음부터 다시 | `bash agent_lab/part3_setup.sh` |
