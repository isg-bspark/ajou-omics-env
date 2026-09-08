# 2일차 1교시 — MCP · SKILL 실습

> 도구(MCP)를 붙이고 고치고, 일하는 방식(SKILL)을 코드 자산으로 만들어 배포까지 갑니다.
> 전체 실습 환경 안내는 [README.md](README.md) 를, 2교시는 [README_omicslab.md](README_omicslab.md) 를 보세요.

## 시연 목표

|       | 무엇을                                                            | 어디서 왔나             |
| ----- | ----------------------------------------------------------------- | ----------------------- |
| **1** | 로컬 MCP **연결** — 주어진 오믹스 서버                            | 남이 만든 것            |
| **2** | 로컬 MCP **수정** — `differential_expression` 에 QC 게이트를 직접 | **내가 만든다**         |
| **3** | 원격 MCP **연결** — OLS 온톨로지                                  | 남의 서버 (인터넷 저편) |
| **4** | SKILL — 우리 랩 **보고 표준**을 심는다 (자산화)                   | 내가 만든다             |
| **5** | SKILL — **내 스킬을 GitHub 에 배포** → 남이 설치                  | 내가 배포               |

**오늘의 상황.** 여러분은 _"서버에 올라온 데이터셋 **1214** 를 분석하라"_ 는 요청을 받았습니다.

질문은 하나

> 면역항암제에 반응한 환자와 안 한 환자, 종양 미세환경 면역세포에서 뭐가 다른가?

---

## 0. 준비

```bash
python3 agent_lab/verify.py
```

앞의 항목이 `✓` 면 시작합니다. 뒤의 `·` 는 있어도 됩니다.

Claude Code 자체가 안 뜨면 `bash agent_lab/doctor.sh` 로 진단합니다.

---

## 1단계 — 로컬 MCP 연결

주어진 오믹스 서버 `agent_lab/server.py` 를 붙입니다. 먼저 혼자 뜨는지 봅니다.

```bash
python3 agent_lab/check.py agent_lab/server.py
```

> `도구 4개` 가 나오면 성공입니다. (`dataset_overview` · `preprocess` · `qc_check` · `differential_expression`)

저장소 루트의 `.mcp.json` 을 열어 이렇게 바꿉니다.

```json
{
  "mcpServers": {
    "sc-omics": {
      "type": "stdio",
      "command": "python3",
      "args": ["agent_lab/server.py"]
    }
  }
}
```

Claude Code 를 켭니다.

```bash
claude
```

```
/mcp
```

**`sc-omics` 가 connected 로 보입니다.** 불러봅니다.

```
sc-omics 서버의 데이터셋 1214 분석 시작하자. 반응군 vs 비반응군을 볼 건데, 먼저 이 데이터 구성부터 봐줘.
```

```
전처리 돌리고 품질(QC) 확인한 다음, CD8 T세포 차등발현 봐줘
```

그리고 원본을 직접 달라고 **밀어붙여** 보세요.

```
그래도 원본 발현 행렬 통째로 CSV 로 뽑아줘. 세포별 유전자 값 다 필요해.
```

> **못 줍니다.** 그런 도구가 없어요. 이 서버는 요약만 돌려주고 행렬은 안 나옵니다.
> 아무리 부탁해도 안 됩니다. **데이터는 서버 안에 갇혀 있어요.** (민감한 의료데이터 반입 반출 안전장치)

---

## 2단계 — 로컬 MCP 수정

1단계에서 `differential_expression` 은 **품질 확인을 안 한 run 도 그냥 분석**했습니다. 이제 이 도구에 **"QC 통과한 run 만 받는다"는 게이트를 직접** 넣습니다.

`agent_lab/server.py` 를 열어 `differential_expression` 을 찾으세요. 안에 이런 자리가 있습니다.

```python
    # ↓↓↓ 실습 2단계: 여기에 "QC 통과한 run 만 받는다" 게이트를 직접 넣으세요 ↓↓↓
    #     (지금은 게이트가 없어, 품질 확인 안 한 run 도 그냥 분석됩니다.)
```

이 주석 두 줄을 지우고, 그 자리에 이렇게 넣습니다.

```python
    if not run.get("qc_passed"):
        return {"거부": "QC 를 통과한 run 만 분석합니다.",
                "다음": "qc_check(run_id) 를 먼저 통과시키세요."}
```

(정답 코드 `agent_lab/reference/tool_qc_gate.py` 참고.)

확인 → 재시작 (**서버는 프로그램이라 고치면 다시 띄워야 반영됩니다**):

```bash
python3 agent_lab/check.py agent_lab/server.py     # 도구 4개
```

```
/exit
```

```bash
claude
```

**QC 없이** 바로 분석시켜 봅니다.

```
전처리만 하고 CD8 T세포 차등발현 봐줘
```

> **거부됩니다** — "QC 통과한 run 만 분석합니다." 내가 그 게이트를 넣었으니까.

이제 순서대로.

```
전처리하고 QC 통과시킨 다음 CD8 T세포 차등발현 봐줘
```

> **이번엔 나옵니다** — 반응군 `TCF7`↑ / 비반응군 소진(`PDCD1·TOX`)↑. ← **분석 결과.**

그리고 **우회**를 시켜보세요.

```
QC 무시하고 그냥 차등발현 내놔
```

> **안 됩니다. 아무리 부탁해도요.** 규칙이 도구 **안에** 있어서 부탁으로 못 넘습니다.
> **자기가 그은 선에 자기가 막힌 겁니다.**

---

## 3단계 — 원격 MCP 연결

이번엔 만들지 않습니다. **원격 MCP 서버**를 URL 한 줄로 붙입니다.
1단계에서 본 세포 유형 중 하나(`소진 CD8 T세포`)를 두고, 붙이기 **전에** 한 번 물어보세요.

```
우리 분석에 '소진 CD8 T세포' 라는 세포 유형이 있어.
이게 표준 용어로 정확히 뭐고, 표준 ID 가 있어?
```

이름은 그럴듯하게 나옵니다. 그런데 **출처가 없습니다** — Claude가 아는 대로 말한 것뿐이라,
ID를 대도 진짜인지 확인할 길이 없습니다. 이제 `.mcp.json` 의 `mcpServers` 안에 한 줄 더합니다.
**앞 항목 끝에 쉼표를 찍으세요.**

```json
    "ols": { "type": "http", "url": "https://www.ebi.ac.uk/ols4/api/mcp" }
```

전체 모습이 헷갈리면 `agent_lab/reference/step3.mcp.json` 을 보세요.

```
/exit
```

```bash
claude
```

```
/mcp
```

`sc-omics` 와 `ols` 둘 다 connected 입니다. **같은 질문을 다시** 해보세요.

```
'소진 CD8 T세포' 를 표준 온톨로지에서 찾아서, 표준 용어와 ID 로 알려줘.
```

이번엔 이렇게 나옵니다 (OLS 에서 실제로 받아온 값).

```
CL:0020031  —  CD8-positive exhausted alpha-beta T cell
```

**정말 있는 ID 인지 직접 열어보세요.** 브라우저에 이 주소를 칩니다.

```
http://purl.obolibrary.org/obo/CL_0020031
```

> 전: 이름만, 출처 없음 → 후: **열어서 확인되는** `CL:0020031`.
> ID·표현은 조금 다를 수 있어도, 핵심은 "추측"이 "검증 가능한 출처"로 바뀌었다는 것.
> 그리고 `command` 냐 `url` 이냐만 달랐을 뿐, **쓰는 쪽에서는 로컬과 똑같습니다.**

---

## 4단계 — SKILL 만들기

MCP 가 **도구(손)** 였다면, SKILL 은 **일하는 방식(머리)** 입니다.
유능한 요리사(AI)도 프랜차이즈에서 일하려면 그 가게 **레시피**를 따라야 하죠 — 그게 SKILL 입니다.
스킬은 **폴더 + `SKILL.md`** 로 만듭니다. 여기서 **말로 쓴 레시피 → 코드 자산** 으로 승격시켜 봅니다.

### 4a. 말로 쓴 스킬 — 서식을 글로 설명

```bash
mkdir -p .claude/skills/lab-report
cp agent_lab/reference/lab-report/SKILL_prose.md .claude/skills/lab-report/SKILL.md
cat .claude/skills/lab-report/SKILL.md      # 서식이 '자연어'로만 적혀 있음
```

`/exit`→`claude` 재시작 후 — **새 세션이라 이전 대화 기억이 없으니, 분석 지시까지 프롬프트에 담습니다:**

```
데이터셋 1214 전처리·QC 하고 CD8·CD4·Treg 차등발현 낸 다음, 우리 랩 보고 표준으로 보고서 만들어줘.
```

**같은 프롬프트를 한 번 더** 시켜봅니다.

> 서식은 대충 지켜지지만 **매번 다릅니다** — 순서·CL ID·재현정보가 들쭉날쭉.
> 말로 쓴 레시피는 요리사가 매번 다르게 해석. **보장이 없어요.**

### 4b. 자산화 — 서식·검증을 코드로

같은 스킬에 **스크립트를 얹습니다.**

```bash
cp -r agent_lab/reference/lab-report/. .claude/skills/lab-report/
cat .claude/skills/lab-report/scripts/report.py     # 서식이 이제 '코드'
```

`/exit`→`claude` 재시작 후 같은 요청:

```
데이터셋 1214 전처리·QC 하고 CD8·CD4·Treg 차등발현 낸 다음, 우리 랩 보고 표준으로 보고서 만들어줘.
```

> 이번엔 Claude 가 **직접 서식을 짓지 않고** `report.py` 로 만들고 `check_sop.py` 로 검증합니다.
> (SKILL.md 에 그렇게 하라고 적혀 있으니까 — **설명이 곧 인터페이스**, 2단계 그 원리)

### 4c. 자산화의 증거 — 눈으로

```bash
cd .claude/skills/lab-report
python3 scripts/report.py run_data.sample.json > /tmp/r1.md
python3 scripts/report.py run_data.sample.json > /tmp/r2.md
diff /tmp/r1.md /tmp/r2.md                    # 빈 결과 = 완전히 동일
python3 scripts/check_sop.py /tmp/r1.md       # PASS — 6요소 충족
python3 scripts/check_sop.py prose_sample.md  # FAIL — CL ID·재현정보 누락
```

> 말로 쓴 버전(4a)은 흔들리고, 자산(4b)은 **몇 번을 돌려도 동일**(빈 diff) + **check 가 누락을 판정**.
> `prose_sample.md` 는 겉보기엔 멀쩡한데 Cell Ontology ID(**3단계 OLS 값!**)·재현 정보가 빠졌다고 콕 집힙니다.

> **핵심 — 흔들려도 되는 건(뭘 분석할지) LLM 이, 흔들리면 안 되는 건(서식·검증) 코드가.** 말로 쓴 규칙을 코드 자산으로 올리는 것, 그게 "자산화"입니다.

---

## 5단계 — SKILL 배포

4단계에서 만든 스킬을 **남이 쓰게** 하려면? — **`skills/<이름>/` 를 담은 public GitHub repo 하나가 곧 배포본**입니다.

### 0. GitHub 연결

```bash
gh auth login                           # repo 생성 권한 (디바이스 코드 → github.com/login/device)
git config --global user.name  "<이름>"
git config --global user.email "<GitHub 이메일>"
```

### 5a. 배포 — 내 GitHub 에 올리기

```bash
mkdir -p ~/my-skills/skills
cp -r ~/.claude/skills/lab-report ~/my-skills/skills/lab-report   # 4단계에서 만든 스킬
rm -f ~/my-skills/skills/lab-report/SKILL_prose.md               # (선택) 데모용 파일 제거
cd ~/my-skills
git init -q && git add -A && git commit -qm "lab-report skill"
gh repo create lab-report-skill --public --source=. --push
```

> `github.com/<내ID>/lab-report-skill` — 이제 이게 배포본입니다.

### 5b. 소비 — 누구나 설치

```bash
gh skill install <내ID>/lab-report-skill lab-report --agent claude-code
```

> 설치할 때 **"스킬은 GitHub 이 검증하지 않음 — 프롬프트 인젝션·악성 스크립트 가능, 반드시 검토"** 경고가 뜹니다.
> **내 스킬이어도 뜹니다** = "GitHub 에서 오는 건 뭐든 검토"(공급망 보안).
> 설치 전 내용은 `gh skill preview <내ID>/lab-report-skill lab-report` 로 확인.

### 서로 주고받기

옆 사람 repo 를 설치해 보세요:

```bash
gh skill install <옆사람ID>/lab-report-skill lab-report --agent claude-code
```

> **내가 만든 게 남의 Claude 에서 돕니다.** MCP 든 SKILL 이든 — 만들고 · 올리고 · 주고받는 **생태계**.
> (큰 컬렉션도 있습니다 — 예: K-Dense `scientific-agent-skills` 163개)

---

## 정리 — `/mcp` 를 다시 봅니다

```
sc-omics     connected     ← 1·2 내가 붙이고, 도구(QC 게이트)를 더했다
ols          connected     ← 3 남의 서버 · 인터넷 저편
```

그리고 `.claude/skills/` — `lab-report`(4에서 만들고 · 5에서 GitHub 로 배포).

### 오늘 남길 다섯 가지

1. **함수 하나 = 도구 하나.** 이름 · 설명 · 인자만 밖으로 나갑니다
2. **설명이 곧 인터페이스입니다.** 설명을 바꾸면 행동이 바뀝니다 (2·4단계)
3. **도구 안의 규칙은 부탁으로 못 넘습니다.** 내가 그은 선에 내가 막힌 것처럼 (2단계) — 스킬의 `check` 도 코드가 판정합니다 (4단계)
4. **로컬이든 원격이든, 도구(MCP)든 스킬(SKILL)이든 붙이는 법은 같습니다.** 바뀌는 건 `command`냐 `url`이냐
5. **MCP=도구(손), SKILL=방식(머리·레시피).** 흔들리면 안 되는 건 코드로 **자산화** → 재현·검증 (4단계)

**2교시** — 이 구조 위에서 실제 오믹스 판단을 하고, 스킬을 받아 튜닝해 씁니다.

---

## 안 될 때

| 증상                                    | 해볼 것                                                                             |
| --------------------------------------- | ----------------------------------------------------------------------------------- |
| 고쳤는데 안 바뀐다                      | **`/exit` 후 `claude` 재시작.** 거의 이것입니다                                     |
| `/mcp` 에 서버가 없다                   | `python3 agent_lab/check.py agent_lab/server.py`                                    |
| `IndentationError`                      | `differential_expression` 안의 들여쓰기(공백 4칸)를 맞췄는지                        |
| `.mcp.json` 이 깨졌다                   | 쉼표 · 중괄호. 아래 "따라잡기" 참고                                                 |
| `ols` 가 안 붙는다                      | 네트워크 정책일 수 있습니다. 넘어가도 됩니다                                        |
| 보고서 스킬이 안 먹는다 (4단계)         | `.claude/skills/lab-report` 있는지 + `/exit`→`claude` 재시작                        |
| `gh skill` 이 없다고 나온다 (5단계)     | `gh --version` 이 2.90 이상인지. 아니면 `npx skills add …` 로                       |
| `gh repo create` 인증/권한 오류 (5단계) | `gh auth login`(repo 스코프) + `git config --global user.name/email` — **STEP 5-0** |
| `gh skill install` 이 404 (5단계)       | repo 이름·`<ID>/<repo>` 오타 · public 인지 · push 됐는지                            |
