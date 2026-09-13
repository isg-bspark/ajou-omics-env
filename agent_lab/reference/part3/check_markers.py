#!/usr/bin/env python3
"""우리 랩 마커 패널로 세포유형 라벨을 데이터에서 확인한다.

사용법:
    python scripts/check_markers.py qc.h5ad --groupby cell_type \
        --signatures assets/gene_signatures.json \
        --expect NK_lab="NK cells" CD8_T_lab="CD8 T cells" --top 8

각 시그니처(마커 유전자 묶음)에 대해, 라벨별로 "마커가 검출된(>0) 세포 비율(%)"의 평균을 계산해
행렬로 보여주고, --expect 로 지정한 (시그니처 → 라벨) 쌍은 판정한다.
    확인   : 해당 라벨에서 70% 이상이고, 다른 라벨 최대치의 2배 이상 (세포 10개 미만 라벨은 비교에서 제외)
    약함   : 해당 라벨에서 40% 이상 → 재검토 (오분류 단정이 아니라 드롭아웃·패널 조정 등 사람이 확인)
    불일치 : 그 외
--top N 을 주면 라벨별 상위 마커 N개(wilcoxon)도 계산해 데이터베이스(enrichr) 대조에 쓴다.
데이터베이스 결과와 함께 보고, 최종 판정은 사람이 한다. 표준 라이브러리 + scanpy 만 사용.
"""
import argparse, json, sys
import numpy as np, pandas as pd
import scanpy as sc


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("--groupby", default="cell_type")
    p.add_argument("--signatures", required=True, help="{name: [genes]} JSON (스킬의 assets/gene_signatures.json)")
    p.add_argument("--sets", nargs="*", default=None, help="검사할 시그니처 이름 (기본: --expect 에 쓰인 것, 없으면 전부)")
    p.add_argument("--expect", nargs="*", default=[], help='시그니처=라벨 쌍. 예: NK_lab="NK cells"')
    p.add_argument("--exclude-prefix", default="unassigned", help="이 접두어로 시작하는 라벨은 제외")
    p.add_argument("--min-cells", type=int, default=10, help="이보다 세포가 적은 라벨은 판정에서 제외 (기본 10)")
    p.add_argument("--top", type=int, default=0, help="라벨별 상위 마커 N개를 함께 계산해 출력 (wilcoxon). 0이면 생략")
    a = p.parse_args()

    ad = sc.read_h5ad(a.input)
    if a.groupby not in ad.obs:
        sys.exit(f"obs 에 '{a.groupby}' 열이 없습니다. 있는 열: {list(ad.obs.columns)}")
    lab = ad.obs[a.groupby].astype(str)
    keep = ~lab.str.startswith(a.exclude_prefix)
    ad = ad[keep.values].copy(); lab = lab[keep.values]
    small = lab.value_counts()[lambda s: s < a.min_cells].index.tolist()
    if small:
        print(f"[check_markers] 세포 {a.min_cells}개 미만 라벨 제외: {small}")
        keep2 = ~lab.isin(small)
        ad = ad[keep2.values].copy(); lab = lab[keep2.values]
    X = ad.X
    mx = X.max() if not hasattr(X, "toarray") else X.max()
    if mx > 50:  # raw counts 로 보이면 정규화
        sc.pp.normalize_total(ad, target_sum=1e4); sc.pp.log1p(ad)

    sigs = json.load(open(a.signatures, encoding="utf-8"))
    expect = dict(kv.split("=", 1) for kv in a.expect)
    sets = a.sets or (list(expect) if expect else list(sigs))
    groups = sorted(lab.unique())

    def frac(gene):
        v = ad[:, gene].X
        v = v.toarray().ravel() if hasattr(v, "toarray") else np.asarray(v).ravel()
        return pd.Series(v > 0, index=ad.obs_names).groupby(lab.values).mean() * 100

    print(f"[check_markers] {ad.n_obs} cells · groupby={a.groupby} · 라벨 {len(groups)}개 · 시그니처 {sets}")
    matrix = {}
    detail = {}
    for s in sets:
        genes = [g for g in sigs.get(s, []) if g in ad.var_names]
        missing = [g for g in sigs.get(s, []) if g not in ad.var_names]
        if not genes:
            print(f"  ! {s}: 데이터에 있는 유전자가 없음 {sigs.get(s)}"); continue
        per_gene = pd.DataFrame({g: frac(g) for g in genes})
        detail[s] = per_gene
        matrix[s] = per_gene.mean(axis=1)
        if missing:
            print(f"  · {s}: 데이터에 없는 유전자 제외 {missing}")
    M = pd.DataFrame(matrix).T.reindex(columns=groups).round(0).astype(int)

    print("\n== 시그니처별 마커 검출 세포 비율(%) · 행=시그니처 · 열=라벨 ==")
    print(M.to_string())

    if a.top > 0:
        sc.tl.rank_genes_groups(ad, a.groupby, method="wilcoxon", n_genes=a.top)
        names = ad.uns["rank_genes_groups"]["names"]
        print(f"\n== 라벨별 상위 마커 {a.top}개 (wilcoxon, 해당 라벨 vs 나머지) · enrichr celltypes 대조용 ==")
        targets = list(expect.values()) if expect else groups
        for g in targets:
            if g in names.dtype.names:
                print(f"  {g:18s} {[str(x) for x in names[g][:a.top]]}")

    if expect:
        print("\n== 판정 (해당 라벨 vs 다른 라벨 최대) ==")
        rows = []
        for s, g in expect.items():
            if s not in M.index or g not in M.columns:
                rows.append((g, s, "-", "-", "라벨/시그니처 없음")); continue
            here = float(M.loc[s, g]); others = M.loc[s].drop(g)
            omax = float(others.max()); og = others.idxmax()
            if here >= 70 and here >= 2 * omax:
                v = "확인"
            elif here >= 40:
                v = "약함 → 재검토(드롭아웃·패널 조정 검토)"
            else:
                v = "불일치"
            rows.append((g, s, f"{here:.0f}%", f"{omax:.0f}% ({og})", v))
            pg = detail[s].loc[g].round(0).astype(int)
            print(f"  {g:18s} ← {s:12s} {here:3.0f}%  vs 최대 {omax:3.0f}% ({og})  → {v}")
            print(f"  {'':18s}   유전자별: " + ", ".join(f"{k} {int(x)}%" for k, x in pg.items()))
        print("\n| 라벨 | 시그니처 | 해당 라벨 | 다른 라벨 최대 | 판정 |")
        print("|---|---|---|---|---|")
        for r in rows:
            print("| " + " | ".join(str(x) for x in r) + " |")


if __name__ == "__main__":
    main()
