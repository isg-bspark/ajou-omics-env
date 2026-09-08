#!/usr/bin/env python3
"""GSE96583 (Kang et al. 2018) batch2 를 실습용 AnnData 로 정리한다.

연구 주제: IFN-beta 자극에 대한 말초혈액 면역세포(PBMC)의 세포타입별 반응

수행 내용
  1. GEO 에서 batch2 의 대조군(ctrl, GSM2560248) / IFN-beta 자극군(stim, GSM2560249)
     count matrix 와 유전자·바코드·세포 주석 파일을 내려받는다.
  2. demuxlet 으로 판정된 doublet / ambiguous 세포를 제거하고 singlet 만 남긴다.
  3. 세포타입이 할당되지 않은 세포를 제거한다.
  4. (조건 x 세포타입) 층화 다운샘플로 실습에 적당한 크기로 줄인다.
  5. 3개 미만의 세포에서만 검출되는 유전자를 제거한다.
  6. 원 저자의 세포타입 주석을 제거한 뒤, raw count 가 .X 에 그대로 담긴
     h5ad 파일 하나로 저장한다.
     (정규화 / HVG / 클러스터링 / 세포타입 주석은 실습에서 직접 수행할 부분이라
      일부러 결과를 넣지 않는다)

사용법
    python scripts/prepare_data.py                    # 기본 12,000 세포, 세포타입 주석 제외
    python scripts/prepare_data.py --n-cells 24000    # 다운샘플 없이 전체 singlet 수준
    python scripts/prepare_data.py --with-cell-type   # 강사용: 세포타입 주석 포함본을 별도 파일로 저장
"""

from __future__ import annotations

import argparse
import gzip
import urllib.request
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy.io import mmread
from scipy.sparse import csr_matrix

GEO_SERIES = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE96nnn/GSE96583/suppl"
GEO_SAMPLE = "https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2560nnn"

SAMPLES = {
    # 조건 : (GSM ID, matrix 파일명)
    "ctrl": ("GSM2560248", "GSM2560248_2.1.mtx.gz"),
    "stim": ("GSM2560249", "GSM2560249_2.2.mtx.gz"),
}

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "gse96583_ifnb.h5ad"


def download(url: str, dest: Path) -> Path:
    """이미 받아둔 파일이면 건너뛴다."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  · 이미 존재: {dest.name}")
        return dest
    print(f"  · 다운로드: {dest.name}")
    urllib.request.urlretrieve(url, dest)
    return dest


def fetch_all() -> dict[str, Path]:
    print("[1/6] GEO 원본 파일 준비")
    paths = {
        "genes": download(
            f"{GEO_SERIES}/GSE96583_batch2.genes.tsv.gz", RAW / "GSE96583_batch2.genes.tsv.gz"
        ),
        "annot": download(
            f"{GEO_SERIES}/GSE96583_batch2.total.tsne.df.tsv.gz",
            RAW / "GSE96583_batch2.total.tsne.df.tsv.gz",
        ),
    }
    for cond, (gsm, mtx) in SAMPLES.items():
        paths[f"{cond}_mtx"] = download(f"{GEO_SAMPLE}/{gsm}/suppl/{mtx}", RAW / mtx)
        paths[f"{cond}_bc"] = download(
            f"{GEO_SAMPLE}/{gsm}/suppl/{gsm}_barcodes.tsv.gz", RAW / f"{gsm}_barcodes.tsv.gz"
        )
    return paths


def read_matrix(mtx_path: Path, bc_path: Path, genes: pd.DataFrame, cond: str) -> ad.AnnData:
    """GEO 의 mtx 는 (유전자 x 세포) 이므로 전치해서 (세포 x 유전자) 로 만든다."""
    with gzip.open(mtx_path, "rb") as fh:
        mat = mmread(fh)
    barcodes = pd.read_csv(bc_path, header=None)[0].astype(str).values
    assert mat.shape == (len(genes), len(barcodes)), (
        f"{mtx_path.name}: 행렬 크기 {mat.shape} 가 "
        f"유전자 {len(genes)} x 바코드 {len(barcodes)} 와 맞지 않습니다"
    )
    adata = ad.AnnData(
        X=csr_matrix(mat.T, dtype=np.float32),
        obs=pd.DataFrame({"barcode": barcodes, "stim": cond}, index=barcodes),
        var=genes.copy(),
    )
    adata.obs_names = [f"{cond}_{bc}" for bc in barcodes]
    return adata


def main(n_cells: int, seed: int, with_cell_type: bool) -> None:
    paths = fetch_all()

    genes = pd.read_csv(paths["genes"], sep="\t", header=None, names=["gene_id", "symbol"])
    genes.index = pd.Index(genes["symbol"].astype(str)).where(
        ~pd.Index(genes["symbol"].astype(str)).duplicated(),
        genes["symbol"].astype(str) + "_" + genes["gene_id"].astype(str),
    )
    genes.index.name = None

    print("[2/6] count matrix 읽기")
    adatas = [
        read_matrix(paths[f"{c}_mtx"], paths[f"{c}_bc"], genes, c) for c in SAMPLES
    ]
    adata = ad.concat(adatas, join="outer", index_unique=None)
    adata.var = genes.loc[adata.var_names]
    print(f"      원본: {adata.n_obs:,} 세포 x {adata.n_vars:,} 유전자")

    print("[3/6] demuxlet 주석 병합 후 singlet 선별")
    annot = pd.read_csv(paths["annot"], sep="\t", index_col=0)
    annot.index = annot.index.astype(str)
    # 같은 바코드가 ctrl/stim 양쪽에 존재할 수 있어 (조건, 바코드) 조합으로 매칭한다.
    annot = annot.reset_index(names="barcode")
    annot["key"] = annot["stim"].astype(str) + "_" + annot["barcode"].astype(str)
    annot = annot.drop_duplicates("key").set_index("key")

    shared = adata.obs_names.intersection(annot.index)
    print(f"      주석이 있는 세포: {len(shared):,} / {adata.n_obs:,}")
    adata = adata[shared].copy()
    meta = annot.loc[adata.obs_names]
    adata.obs["donor"] = meta["ind"].astype(str).values
    adata.obs["cell_type"] = meta["cell"].astype(str).values
    adata.obs["multiplets"] = meta["multiplets"].astype(str).values

    counts = adata.obs["multiplets"].value_counts()
    print("      " + ", ".join(f"{k}={v:,}" for k, v in counts.items()))

    keep = (adata.obs["multiplets"] == "singlet") & (~adata.obs["cell_type"].isin(["nan", "NA"]))
    adata = adata[keep.values].copy()
    del adata.obs["multiplets"]  # 전부 singlet 이므로 더 이상 의미 없음
    print(f"      singlet + 세포타입 확정: {adata.n_obs:,} 세포")

    print(f"[4/6] (조건 x 세포타입) 층화 다운샘플 → 목표 {n_cells:,} 세포")
    if adata.n_obs > n_cells:
        rng = np.random.default_rng(seed)
        frac = n_cells / adata.n_obs
        idx = adata.obs.groupby(["stim", "cell_type"], observed=True).indices
        picked = np.concatenate(
            [
                rng.choice(pos, size=max(1, int(round(len(pos) * frac))), replace=False)
                for pos in idx.values()
            ]
        )
        adata = adata[np.sort(picked)].copy()
    print(f"      {adata.n_obs:,} 세포")

    print("[5/6] QC 지표 계산 및 저성립 유전자 제거")
    counts_per_cell = np.asarray(adata.X.sum(axis=1)).ravel()
    genes_per_cell = np.asarray((adata.X > 0).sum(axis=1)).ravel()
    adata.obs["total_counts"] = counts_per_cell
    adata.obs["n_genes"] = genes_per_cell

    # 이 데이터는 유전자 목록에 MT- 유전자가 있긴 하지만 count 가 전부 0 이다
    # (원 저자가 미토콘드리아 리드를 제외했다). 값이 전부 0 인 가짜 QC 지표를 남기지 않도록,
    # 실제로 미토콘드리아 count 가 잡힐 때만 pct_counts_mt 를 만든다.
    mt = adata.var["symbol"].astype(str).str.upper().str.startswith("MT-").values
    mt_counts = (
        np.asarray(adata[:, mt].X.sum(axis=1)).ravel() if mt.any() else np.zeros(adata.n_obs)
    )
    if mt_counts.sum() > 0:
        adata.obs["pct_counts_mt"] = np.where(
            counts_per_cell > 0, mt_counts / counts_per_cell * 100, 0
        )
        adata.var["mt"] = mt
    else:
        print(
            f"      ⚠ MT- 유전자 {int(mt.sum())}개의 count 가 모두 0 이라 "
            "pct_counts_mt 는 만들지 않습니다"
        )

    cells_per_gene = np.asarray((adata.X > 0).sum(axis=0)).ravel()
    adata = adata[:, cells_per_gene >= 3].copy()
    print(f"      {adata.n_obs:,} 세포 x {adata.n_vars:,} 유전자")

    # 원 저자의 세포타입 주석은 여기까지(필터링·층화 다운샘플)만 쓰고 결과물에서는 뺀다.
    # 세포타입 주석은 수강생이 클러스터링과 마커 유전자로 직접 붙일 부분이다.
    summary = pd.crosstab(adata.obs["cell_type"], adata.obs["stim"])
    if not with_cell_type:
        adata.obs = adata.obs.drop(columns=["cell_type"])

    keep_cols = ["stim", "donor"] + (["cell_type"] if with_cell_type else [])
    for col in keep_cols:
        adata.obs[col] = adata.obs[col].astype("category")
    adata.obs = adata.obs.drop(columns=["barcode"])
    adata.uns["about"] = {
        "study": "Kang et al. 2018, Nat Biotechnol (GSE96583, batch2)",
        "design": "PBMC, control vs IFN-beta stimulated, 8 lupus donors",
        "processing": (
            "demuxlet doublet/ambiguous removed; stratified downsample; raw counts in .X; "
            + ("original cell type annotation included (instructor copy)" if with_cell_type
               else "original cell type annotation intentionally withheld")
        ),
    }

    out = OUT if not with_cell_type else OUT.with_name(OUT.stem + "_with_celltype.h5ad")
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f"[6/6] 저장: {out.relative_to(ROOT)}")
    adata.write_h5ad(out, compression="gzip")
    print(f"      파일 크기: {out.stat().st_size / 1e6:.1f} MB")
    print(f"      obs 컬럼: {list(adata.obs.columns)}")
    print("\n[참고] 원 저자 주석 기준 구성 (결과 파일에는 포함되지 않음)")
    print(summary)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-cells", type=int, default=12000, help="다운샘플 목표 세포 수")
    parser.add_argument("--seed", type=int, default=0, help="난수 시드")
    parser.add_argument(
        "--with-cell-type",
        action="store_true",
        help="원 저자의 세포타입 주석을 포함한 강사용 파일을 별도로 저장한다",
    )
    args = parser.parse_args()
    main(args.n_cells, args.seed, args.with_cell_type)
