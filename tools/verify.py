#!/usr/bin/env python3
"""
기능 분석 실습 환경 점검 — 시작 전에 한 번 돌리세요.

    python3 tools/verify.py

패키지 · gene set 캐시 · 입력 데이터를 봅니다.
분석 결과는 검사하지 않습니다.
"""
import json
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

OK = "  \033[32m✓\033[0m"
NO = "  \033[31m✗\033[0m"
WARN = "  \033[33m·\033[0m"
fails: list[str] = []
warns: list[str] = []


def check(name, ok, detail="", fix="", warn_only=False):
    print(f"{OK if ok else (WARN if warn_only else NO)} {name}"
          f"{('  — ' + detail) if detail else ''}")
    if not ok:
        (warns if warn_only else fails).append(f"{name}\n      → {fix}")
    return ok


def reachable(url, timeout=8):
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except urllib.error.HTTPError:
        return True          # 응답이 왔으면 망은 열린 것
    except Exception:
        return False


def repo_root() -> pathlib.Path:
    try:
        out = subprocess.run(["git", "worktree", "list", "--porcelain"],
                             capture_output=True, text=True, check=True).stdout
        for line in out.splitlines():
            if line.startswith("worktree "):
                return pathlib.Path(line[len("worktree "):])
    except (OSError, subprocess.CalledProcessError):
        pass
    return pathlib.Path(__file__).resolve().parent.parent


def main() -> int:
    print("\n기능 분석 실습 환경 점검\n")
    root = repo_root()

    # --- 패키지 ---------------------------------------------------------
    try:
        import decoupler as dc
        ver = getattr(dc, "__version__", "?")
        major = int(str(ver).split(".")[0]) if str(ver)[0].isdigit() else 0
        check("decoupler 2.x", major >= 2, f"v{ver}" + ("" if major >= 2 else "  ← 1.x 입니다"),
              "pip install -U 'decoupler>=2.2,<3'  "
              "(1.x 는 함수 이름이 전부 다릅니다 — decoupler-cheatsheet 스킬 1번 표)")
        if major >= 2:
            check("  dc.op / dc.mt / dc.pp 모듈",
                  all(hasattr(dc, m) for m in ("op", "mt", "pp", "pl", "tl")),
                  "", "설치가 깨졌습니다. pip install --force-reinstall 'decoupler>=2.2,<3'")
    except ImportError:
        check("decoupler 2.x", False, "없음",
              "pip install -r .devcontainer/requirements.txt")

    for mod, label, fix in [
        ("scanpy", "scanpy", "pip install -r .devcontainer/requirements.txt"),
        ("pydeseq2", "pydeseq2  (pseudobulk DE)", "pip install 'pydeseq2>=0.5,<1'"),
        ("gseapy", "gseapy  (대조 구현용)", "pip install 'gseapy>=1.1,<2'"),
    ]:
        try:
            import importlib.metadata as md
            check(label, True, f"v{md.version(mod)}")
        except Exception:
            check(label, False, "없음", fix)

    # --- gene set 캐시 --------------------------------------------------
    print()
    gsdir = root / "data" / "genesets"
    manifest_path = gsdir / "manifest.json"
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except json.JSONDecodeError:
            pass

    cached = sorted(p.name.removesuffix(".csv.gz") for p in gsdir.glob("*.csv.gz")) \
        if gsdir.is_dir() else []
    check("gene set 캐시", bool(cached),
          ", ".join(cached) if cached else "비어 있음",
          "저장소에 함께 들어 있어야 합니다 — git status 로 지워지지 않았는지 확인하세요")

    for name in cached:
        info = manifest.get(name, {})
        n_src, n_edge = info.get("n_sources"), info.get("n_edges")
        detail = (f"집합 {n_src}개 · 엣지 {n_edge:,}개" if n_src and n_edge
                  else "manifest 에 기록 없음")
        under = info.get("n_sources_under_15")
        if under:
            detail += f" · 15개 미만 {under}개"
        print(f"{OK} {'  ' + name:<24}{detail}")

    missing = [n for n in ("hallmark", "reactome", "progeny", "collectri") if n not in cached]
    if missing:
        check(f"  캐시에 없는 것: {', '.join(missing)}", False, "",
              "data/genesets/ 는 저장소에 함께 들어 있습니다. "
              "지워졌다면 git checkout -- data/genesets 로 되돌리세요",
              warn_only=True)

    # --- 입력 데이터 ----------------------------------------------------
    print()
    h5ad = root / "data" / "processed" / "gse96583_ifnb.h5ad"
    if check("입력 데이터", h5ad.exists(), str(h5ad.relative_to(root)) if h5ad.exists() else "없음",
             "python3 scripts/prepare_data.py"):
        try:
            import h5py
            with h5py.File(h5ad, "r") as f:
                cols = set(f["obs"].keys())
            for col, why in [("stim", "조건 대비의 대상"),
                             ("donor", "pseudobulk 의 생물학적 반복")]:
                check(f"  obs['{col}']", col in cols, why,
                      "prepare_data.py 를 다시 돌리세요")
        except Exception as e:                       # noqa: BLE001
            check("  obs 컬럼 확인", False, f"{type(e).__name__}: {e}",
                  "h5py 로 열지 못했습니다. scanpy 로 직접 확인하세요", warn_only=True)

    # --- 네트워크 -------------------------------------------------------
    print()
    check("omnipathdb.org  (캐시가 있으면 없어도 됨)",
          reachable("https://omnipathdb.org/queries/annotations"), "",
          "캐시를 미리 받아 두면 실습에는 지장이 없습니다", warn_only=True)

    # --- 정리 -----------------------------------------------------------
    print()
    if fails:
        print("아래를 먼저 해결하세요.\n")
        for i, f in enumerate(fails, 1):
            print(f"  {i}. {f}")
        print()
        return 1

    print("✅ 준비 완료 — decoupler-cheatsheet 스킬을 확인하세요.")
    if warns:
        print("\n  (아래는 없어도 진행할 수 있습니다)")
        for w in warns:
            print(f"    · {w}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
