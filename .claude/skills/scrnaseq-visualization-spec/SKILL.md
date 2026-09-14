---
name: scrnaseq-visualization-spec
description: 'scRNA-seq 분석의 배치 통합·annotation·DEG·기능 분석(GSEA·pathway) 단계에서 그림을 그리는 코드를 짜기 전에 읽는다. 어떤 그림을 어떤 임베딩 위에 그려야 하는지에 대한 규격이며, step-validator 는 이 규격으로 그림을 채점한다. 그림의 한글 텍스트가 깨질 때, 그림 그리는 스크립트가 에러 없이 멈출 때도 읽는다. 트리거: "배치 통합 그림", "batch key", "보정 전후 UMAP", "과보정", "annotation 그림", "DEG 그림", "dotplot", "scatter plot", "volcano plot", "GSEA 그림", "pathway 그림", "stacked violin", "한글 깨짐", "폰트 깨짐", "스크립트가 멈췄다", "그림 그리다가 멈춤".'
---

이 스킬은 8단계 scRNA-seq 파이프라인(`scrnaseq-plan-execute`/`scrnaseq-stepwise-hitl` 공용)에서
**"그림을 그렸다"만으로는 부족한 지점**을 규격화한 것이다. 어떤 임베딩 위에 그릴지, 어떤
그림 형태(scatter vs volcano)를 쓸지가 결과 해석을 바꾸므로, 배치 통합·annotation·DEG·
기능분석 코드를 짜기 **전에** 이 문서를 읽고 아래 규격을 따른다. `step-validator` 는 이
규격을 기준으로 채점한다.

`sc.pl.*` 호출 방법 자체(함수·인자·기본 워크플로)는 `scanpy` 스킬이 있으면 **그 스킬을
읽고 따른다** — 기억에 의존해 인자를 짐작하지 않는다. 이 문서는 그 위에 얹히는 **이
프로젝트 전용 규격**이므로, 둘이 어긋나면 이 문서가 우선한다(예: `scanpy` 스킬이 DEG
그림으로 volcano 를 보여 주더라도 이 프로젝트에서는 `references/deg.md` 규격대로 발현
UMAP 을 그린다).

## 이 문서를 쓰는 법 — 지금 하는 단계의 파일 하나만 읽는다

아래 0번(모든 그림 공통)은 **항상** 지킨다. 단계별 규격은 네 파일로 나뉘어 있으니
**지금 그리려는 단계의 파일만 읽는다.** 네 개를 한꺼번에 읽지 않는다 — 다른 단계의
규격은 지금 판단에 쓰이지 않으면서 컨텍스트만 차지하고, 단계가 바뀔 때 다시 읽어야
어차피 최신 내용을 본다.

| 지금 끝낸 단계 | 읽을 파일 | 거기 있는 그림 |
|---|---|---|
| 배치 통합 | `references/integration.md` | 보정 전·후 UMAP 대조 패널(`batch_key` 색) · 과보정 확인 marker 패널 · 겹침 표 |
| Clustering · Annotation | `references/annotation.md` | cluster↔celltype 대조 패널 · cluster marker dotplot(positive/negative 묶음) |
| 조건 간 차등발현 | `references/deg.md` | celltype DEG 패널(post-integration) · 조건 DEG 그림(pre-integration) |
| 기능 분석(GSEA·pathway) | `references/functional.md` | pathway 활성 UMAP 패널 · ctrl/stim 구분 stacked violin |

파일을 건너뛰고 기억으로 그리지 않는다. 규격은 바뀌고, 이 파일들이 정본이다.

**단계를 가로지르는 규칙 하나** — 임베딩을 어느 쪽으로 쓰는지가 단계마다 다르다.
배치 통합에서 만든 **보정 전 UMAP 을 버리지 말고 보관한다**(`X_umap_pre` 등).
`annotation.md` 는 보정 **후** 임베딩을, `deg.md` 의 조건 DEG 그림과 `functional.md` 의
pathway 활성 UMAP 은 보정 **전** 임베딩을 기준으로 삼는다.

## 0. 모든 그림 공통 — 한글 폰트 깨짐(tofu) 방지

matplotlib 기본 폰트(DejaVu Sans)에는 한글 글리프가 없다. 그림 제목·축 라벨에 한글이
섞이면 네모(tofu)로 깨진다 — GSEA/pathway 그림처럼 제목에 "~ 경로 활성" 같은 한글 설명을
붙이는 자리에서 특히 자주 터진다. 아래 둘 중 하나를 **반드시** 지킨다.

1. **(권장) 그림 안 텍스트는 영어만 쓴다.** title·axis label·legend·주석 텍스트 전부.
   pathway/gene set 이름(`INTERFERON_ALPHA_RESPONSE` 등)과 유전자 심볼은 원래 영어이므로
   번역하지 않는다. 해석·설명은 그림이 아니라 리포트 본문(한글)에 쓴다 — 그림 캡션에서
   한글로 설명해도 되는 건 리포트 파일 쪽 텍스트이지 matplotlib 렌더링 텍스트가 아니다.
2. **부득이 그림 안에 한글을 넣어야 하면**, 렌더링 전에 이 환경에 실제로 설치된 한글
   폰트를 확인하고(`fc-list :lang=ko` 또는 `matplotlib.font_manager` 로 탐색) 그 폰트
   이름으로 `plt.rcParams['font.family']` 를 지정한다. `plt.rcParams['axes.unicode_minus']
= False` 도 같이 설정한다(안 하면 마이너스 부호가 깨진다). 어떤 폰트를 썼는지 결정
   로그에 남긴다.

어느 쪽을 택했든 **저장하기 전에 실제로 그림을 확인해서** 네모 깨짐이 없는지 본다.
확인 없이 "폰트 설정했으니 괜찮겠지"로 넘기지 않는다.

## 0.1 모든 그림 공통 — 저장 위치

그림은 **그 그림을 만든 단계의 디렉토리 안**에 둔다 — `results/<번호>_<단계>/figures/`.
최상위에 `figures/` 를 만들지 않는다. 표·수치는 같은 단계의 `results/<번호>_<단계>/`
바로 아래에 두므로, 한 단계의 산출물은 전부 한 디렉토리 아래에 모인다.

저장 직전에 그 경로를 만들고, scanpy 의 autosave 를 쓴다면 단계마다 `figdir` 을 바꿔 준다.
`sc.settings.figdir` 의 기본값은 `./figures/` 라서, 그대로 두면 `scanpy` 스킬의 예제를
그대로 따라 쓰는 순간 최상위에 그림이 쌓인다.

```python
import os, scanpy as sc

figdir = "results/05_annotation/figures"
os.makedirs(figdir, exist_ok=True)
sc.settings.figdir = figdir          # 단계가 바뀌면 이 줄도 같이 바꾼다
# 또는 직접 저장: fig.savefig(f"{figdir}/dotplot_core_markers.png", dpi=150, bbox_inches="tight")
```

리포트(`results/summary/report.html`)에서 참조할 때는 한 단계 올라간 상대 경로가 된다 —
`../05_annotation/figures/dotplot_core_markers.png`.

## 0.5 모든 그림 공통 — macOS에서 백그라운드 실행 시 무한 대기(hang) 방지

이 파이프라인의 그림 그리는 스크립트(annotation·DEG·기능분석 전부)는 실행 시간이 길어
`nohup ... &` 나 `run_in_background`로 뒤로 돌려 실행하는 일이 많다. **macOS에서
matplotlib 기본 백엔드가 `macosx`(네이티브 GUI)일 때, 터미널과 분리된 백그라운드
프로세스 안에서 그림을 그리거나 그 뒤에 별다른 이유 없이 스크립트가 멈춘다** — 에러
없이 CPU 사용률이 0%로 떨어진 채 영원히 끝나지 않는다. 특히 `sc.pl.dotplot`,
`sc.pl.umap`, `plt.savefig` 처럼 그림을 저장하는 호출 **직후**에 멈추는 패턴으로
나타나므로, 코드가 잘못됐다고 오인해 애먼 곳을 고치기 쉽다.

- **증상으로 알아채는 법**: 로그에 에러 없이 마지막 `print`/`WARNING: saving figure to
file ...` 뒤로 출력이 멈췄고, `ps -o pid,%cpu,time -p <PID>` 를 몇 초 간격으로
  반복해도 `TIME` 값이 전혀 늘지 않으면(CPU 0%) 이 문제다. 실제로 계산 중이라면
  CPU%가 0이 아니거나 TIME이 계속 증가한다.
- **예방(권장, 매번 이렇게 시작한다)**: scRNA-seq 그림을 그리는 모든 스크립트 맨 위,
  `import scanpy` 보다 먼저 아래 두 줄을 넣는다. `matplotlib.use()`는 반드시 다른
  matplotlib 관련 import(scanpy 포함, scanpy가 내부에서 matplotlib을 import한다)보다
  **먼저** 호출해야 적용된다.

  ```python
  import matplotlib
  matplotlib.use("Agg")
  import scanpy as sc
  ```

  또는 스크립트를 실행하는 셸에서 환경변수로 지정해도 된다: `MPLBACKEND=Agg
python script.py` (`.venv/` 가 있는 환경이면 `.venv/bin/python`). 둘 중 하나만 있으면 충분하고, 스크립트 안에 넣는 쪽이
  실행 방법(포그라운드/백그라운드, 어떤 셸)에 관계없이 항상 적용되므로 더 안전하다.

- **이미 멈춘 경우 복구**: `ps aux | grep <script.py>`로 PID를 찾고, `ps -o
pid,%cpu,time -p <PID>`를 두세 번 간격을 두고 찍어 TIME이 안 늘어나는 것을 확인한
  뒤 `kill -9 <PID>`로 종료한다. 그 다음 위 예방 조치를 스크립트에 추가하고 **처음부터
  다시 실행**한다 — 중간부터 이어가지 않는다(그림을 그리기 전 단계까지는 이미 끝났을
  수 있지만, 안전하게 전체를 재실행하는 편이 무엇이 저장됐는지 추적하기 쉽다).
- 이 문제는 Linux 컨테이너나 CI처럼 애초에 GUI 백엔드가 없는 환경에서는 발생하지
  않는다 — 로컬 macOS 환경에서 실험할 때만 해당한다는 것을 기억한다.

## step-validator 채점 포인트 (요약)

- 배치 통합 단계: **보정 전·후 UMAP 대조 패널**이 `batch_key` 색으로 있는지(좌우가
  조건이 아니라 보정 전/후인지), 과보정 확인용 marker 패널이 있는지, 겹침을 **표**로도
  남겼는지, 보정 전 임베딩을 뒤 단계용으로 보관했는지.
- annotation 단계: **cluster↔celltype 대조 패널**(같은
  post-integration 임베딩 위에 clustering 결과와 celltype 을 나란히) 존재, 1차 dotplot
  존재, 필요시 2차 축소 dotplot과 그 판단 근거. **dotplot 의 marker 가 세포 타입별로
  묶여 있는지**(알파벳 순 평평한 리스트면 완결성을 깎는다). 리포트에서 대조 패널과
  dotplot 이 **같은 절에 함께** 배치되어 있는지.
- 조건 간 차등발현 단계: celltype DEG 패널(post-integration UMAP + marker scatter)과
  조건 DEG 그림(pre-integration UMAP + 유전자 발현량 색)이 각각 올바른 임베딩을 쓰는지,
  둘을 뒤바꿔 쓰지 않았는지. **volcano·MA plot 이 있으면 규격 위반**이고, **ctrl 과 stim
  이 좌우 패널로 쪼개져 있어도 규격 위반**이다.
- 기능 분석 단계: pathway 활성 UMAP 패널(비보정 UMAP, 조건 색 패널 + pathway 하나당
  한 패널, ctrl+stim 을 모든 패널에 함께)과 ctrl/stim 구분 stacked violin 이 둘 다
  있는지, 그림 텍스트에 한글 폰트 깨짐(tofu)이 없는지.
- 리포트 단계: **각 절에 그 절의 그림만 들어갔는지.** 조건 간 차등발현 절에 celltype
  DEG 패널(세포 타입 구조를 보여주는 그림)을 넣는 것은 흔한 혼동이다 — celltype DEG
  패널은 annotation 절에, 조건 DEG 그림은 조건 간 차등발현 절에 둔다.
- 공통: 그림 그리는 스크립트를 백그라운드로 실행했다면 `matplotlib.use("Agg")`(또는
  `MPLBACKEND=Agg`)를 적용했는지 — 안 했다면 macOS에서 조용히 멈췄다가 재실행됐을
  가능성이 있으므로, 로그에 재실행 흔적(같은 산출물을 두 번 만든 기록)이 있는지 본다.
