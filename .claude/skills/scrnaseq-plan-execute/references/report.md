# REPORT 단계 — 산출물 규격과 여는 법

마지막 REPORT 단계에서 만드는 HTML 리포트가 지켜야 할 것. 두 스킬
(`scrnaseq-plan-execute`, `scrnaseq-stepwise-hitl`) 이 똑같이 따른다.

## 왜 규격이 필요한가

이 실습은 GitHub Codespaces 의 **웹 편집기**에서 돌아간다. 웹 편집기는 로컬 VS Code 와
두 가지가 다르고, 둘 다 리포트를 못 보게 만든다.

1. `.html` 파일을 열면 **소스 코드로만** 보여준다. 렌더링 미리보기가 없고 `file://` 도
   못 쓴다. 그래서 "리포트를 results/ 에 썼습니다" 로 끝내면 학생은 HTML 태그 덩어리를
   본다.
2. 학생이 Explorer 우클릭 → Download 로 HTML 만 내려받으면, 그림을 상대 경로로
   참조하는 리포트는 **그림이 전부 깨진 채** 열린다.

아래 두 규칙이 각각을 없앤다.

## 규칙 1 — 리포트 경로를 고정하고, 여는 법을 같이 알려준다

리포트는 `results/summary/report.html` 에 쓴다. 다 만든 뒤 사용자에게 **절대 경로와 함께
여는 법 한 줄**을 반드시 같이 알린다. 경로만 print 하면 학생은 그 파일을 클릭해 소스
코드를 보고 "리포트가 깨졌다" 고 판단한다.

> Codespace 왼쪽 파일 목록에서 `results/summary/report.html` 을 **우클릭 → Show Preview**
> 하면 편집기 탭 안에서 리포트가 그대로 열립니다.

이 미리보기는 devcontainer 에 미리 깔린 Live Preview 확장(`ms-vscode.live-server`)이
처리한다. 학생이 서버를 띄우거나 포트를 여는 일은 없다. 확장이 없는 환경이라면
`python -m http.server 8000 --directory results/summary` 를 띄우고 Codespaces 가 포워딩한
포트를 여는 것이 대안이지만, 이 저장소의 Codespace 에서는 먼저 우클릭 미리보기를 안내한다.

## 규칙 2 — 내려받아도 안 깨지게, 단일 파일 본을 같이 만든다

리포트 HTML 은 상대 경로로 그림을 참조해서 써도 된다. 리포트는 `results/summary/` 에
있고 그림은 각 단계의 `figures/` 안에 있으므로 경로는 한 단계 올라간다 —
`../04_clustering/figures/umap_leiden.png` 처럼 쓴다. 미리보기는
그걸로 잘 뜨고, 작성도 쉽다. 대신 다 쓴 뒤 **반드시** 아래를 돌려 그림을 본문에 박은
단일 파일 본을 하나 더 만든다.

```bash
python tools/build_report.py results/summary/report.html
# → results/summary/report_standalone.html
```

`report_standalone.html` 은 그림이 data URI 로 들어가 있어 파일 하나만 내려받아도 어디서든
열린다. 학생에게 공유·제출용으로 안내할 것은 **이 파일**이다.

스크립트가 `WARN: 파일을 못 찾아 그대로 둔 참조` 를 출력하면(종료 코드 2) 그 그림은 실제로
깨진 것이다. 경고를 무시하고 "리포트 완성" 이라고 보고하지 않는다 — 경로를 고치고 다시
돌린다. 그림 경로가 틀렸다는 것은 대개 앞 단계에서 그림을 약속한 자리에 안 썼다는 뜻이므로,
경로만 맞추지 말고 그림이 실제로 있는지 확인한다.

## 규칙 3 — 리포트에 들어가야 하는 것

- 각 단계에서 무엇을 했고 어떤 **실측 수치**가 나왔는지 (지어내지 않는다 — R3)
- 판단이 갈린 지점: 무엇을 골랐나 · 고르지 않은 대안 · 왜. `EXPERIMENT.md` 결정 로그와
  같은 내용이어야 한다
- `results/validation/` 의 단계별 채점 점수(정확성·완결성)와 WARN 으로 남긴 것
- 그림은 `scrnaseq-visualization-spec` 규격을 따른 것들. 그림마다 무엇을 보는 그림이고
  거기서 무엇을 읽어야 하는지 한 줄 설명을 붙인다 — 설명 없는 그림은 학생에게 장식이다

## 선택 — Artifact 로 게시해 링크로 공유하기

`Artifact` 도구를 쓸 수 있는 세션이라면, `report_standalone.html` 을 게시해서 브라우저
링크로 바로 볼 수 있게 해도 된다. 파일 경로 대신 URL 을 받으므로 남에게 공유하기 쉽다.

**선택 단계다. 안 되면 그냥 넘어간다.** 이 저장소의 Codespace 는 `ANTHROPIC_API_KEY`
(Console 종량제) 인증을 우선 쓰는데, Artifact 게시는 claude.ai 계정 기반이라 API key
세션에서는 도구가 아예 없을 수 있다. 도구가 없다고 사용자에게 로그인·토큰 발급을 요구하지
않는다 — 규칙 1·2 만으로 리포트는 이미 볼 수 있다.

게시한다면 그림이 임베드된 `report_standalone.html` 을 올린다(외부 파일 참조는 게시본에서
깨진다). 16MB 를 넘으면 게시할 수 없으므로, 그럴 땐 그림 해상도를 낮춘 뒤 다시 만들거나
게시를 건너뛴다.
