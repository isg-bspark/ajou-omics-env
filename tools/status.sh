#!/usr/bin/env bash
# 병렬 실험들의 현재 상태를 한 화면에 보여준다.
set -euo pipefail

# 항상 main 작업 트리를 기준으로 동작한다.
# 이 스크립트 자체는 worktree 에 링크되지 않지만, 실행 위치가 worktree 안일 수 있으므로
# worktree 안에서 실행했을 때 자기 자신을 루트로 착각한다.
ROOT="$(git worktree list --porcelain 2>/dev/null | sed -n '1s/^worktree //p')"
if [ -z "$ROOT" ] || [ ! -d "$ROOT/.git" ]; then
  echo "✗ git 저장소 안에서 실행하세요." >&2
  exit 1
fi
HERE="$(pwd)"
cd "$ROOT"
if [ "$HERE" != "$ROOT" ] && [ "${HERE#$ROOT/worktrees/}" != "$HERE" ]; then
  echo "· 실험 worktree 안에서 실행했습니다 — main($ROOT) 기준으로 동작합니다"
fi

if [ ! -d worktrees ]; then
  echo "worktrees/ 가 없습니다. 먼저 bash tools/setup.sh 를 실행하세요."
  exit 0
fi

exec python3 - <<'PY'
import json, pathlib, subprocess, unicodedata

root = pathlib.Path("worktrees")
dirs = sorted(p for p in root.iterdir() if p.is_dir())
if not dirs:
    print("worktrees/ 가 비어 있습니다.")
    raise SystemExit

def width(s):
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)

def pad(s, n):
    return s + " " * max(0, n - width(s))

def get(d, *path, default="-"):
    for k in path:
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return default if d is None else d

def branch_of(wt):
    try:
        return subprocess.run(
            ["git", "-C", str(wt), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "?"

rows, extra = [], []
for wt in dirs:
    m = wt / "results" / "summary" / "metrics.json"
    data = {}
    if m.exists():
        try:
            data = json.loads(m.read_text())
        except json.JSONDecodeError:
            data = {"stage": "metrics.json 파싱 실패"}

    done = todo = 0
    exp = wt / "EXPERIMENT.md"
    if exp.exists():
        for line in exp.read_text().splitlines():
            s = line.strip()
            if s.lower().startswith("- [x]"):
                done += 1
            elif s.startswith("- [ ]"):
                todo += 1

    decisions = [d for d in get(data, "decisions", default=[]) if isinstance(d, dict)]
    by_human = sum(1 for d in decisions if d.get("decided_by") == "human")

    n_files = sum(1 for sub in ("results", "figures")
                  for f in (wt / sub).rglob("*") if f.is_file()) if wt.exists() else 0

    rows.append({
        "실험": wt.name,
        "단계": str(get(data, "stage")),
        "체크": f"{done}/{done + todo}" if done + todo else "-",
        "세포수": str(get(data, "qc", "n_cells_after")),
        "클러스터": str(get(data, "clustering", "n_clusters")),
        "세포타입": str(get(data, "annotation", "n_cell_types")),
        "결정(사람/전체)": f"{by_human}/{len(decisions)}" if decisions else "-",
        "산출물": str(n_files),
        "report": "있음" if (wt / "results/summary/report.html").exists() else "-",
    })
    extra.append((wt.name, branch_of(wt)))

cols = list(rows[0])
w = {c: max([width(c)] + [width(r[c]) for r in rows]) for c in cols}
head = "  ".join(pad(c, w[c]) for c in cols).rstrip()
print(head)
print("-" * width(head))
for r in rows:
    print("  ".join(pad(r[c], w[c]) for c in cols).rstrip())

print()
nw = max(width(n) for n, _ in extra)
for name, br in extra:
    print(f"{pad(name, nw)}   branch {br}")
PY
