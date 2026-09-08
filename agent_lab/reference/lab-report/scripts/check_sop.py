#!/usr/bin/env python3
"""우리 랩 보고서 표준 준수 검사기.

사용법:  python check_sop.py report.md

표준 6요소가 있는지 검사해 PASS / FAIL 을 출력한다.
표준 라이브러리만 사용한다 (설치 불필요).
준수하면 종료코드 0, 아니면 1.
"""
import re
import sys

필수 = [
    ("메타(데이터셋·run_id)", lambda t: ("데이터셋" in t) and ("run_id" in t)),
    ("Methods",              lambda t: "## Methods" in t),
    ("결과표",               lambda t: ("## 결과" in t) and ("유의" in t) and ("|" in t)),
    ("Cell Ontology ID",     lambda t: bool(re.search(r"CL:\d{7}", t))),
    ("한계(환자 교란)",       lambda t: ("## 한계" in t) or ("교란" in t)),
    ("재현정보",             lambda t: ("## 재현" in t) and ("qc_passed" in t)),
]


def main():
    if len(sys.argv) != 2:
        sys.exit("사용법: python check_sop.py report.md")
    with open(sys.argv[1], encoding="utf-8") as f:
        t = f.read()

    누락 = [이름 for 이름, 검사 in 필수 if not 검사(t)]
    cl_수 = len(set(re.findall(r"CL:\d{7}", t)))

    if 누락:
        print("FAIL — 표준 미준수. 누락:")
        for 이름 in 누락:
            print(f"  ✗ {이름}")
        print(f"(Cell Ontology ID {cl_수}개 발견)")
        sys.exit(1)

    print(f"PASS — 표준 6요소 모두 충족 (Cell Ontology ID {cl_수}개)")
    sys.exit(0)


if __name__ == "__main__":
    main()
