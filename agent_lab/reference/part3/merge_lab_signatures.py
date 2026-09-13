#!/usr/bin/env python3
"""우리 랩 마커 패널(gene_signatures.lab.json)을 scanpy 스킬의 assets/gene_signatures.json 에 합친다.
    python3 agent_lab/reference/part3/merge_lab_signatures.py
"""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[3]
lab = json.load(open(ROOT / "agent_lab/reference/part3/gene_signatures.lab.json", encoding="utf-8"))
target = ROOT / ".claude/skills/scanpy/assets/gene_signatures.json"
if not target.exists():
    raise SystemExit(f"스킬이 설치되어 있지 않습니다: {target}  (① gh skill install 또는 part3_setup.sh --with-skill)")
cur = json.load(open(target, encoding="utf-8"))
added = [k for k in lab if k not in cur]
cur.update(lab)
json.dump(cur, open(target, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"assets/gene_signatures.json 갱신: 추가 {added} · 전체 {list(cur)}")
