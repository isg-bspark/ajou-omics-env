## 우리 랩 기본값 (10x PBMC)

QC 는 `scripts/qc_analysis.py` 로 실행한다. 사용자가 기준을 말하지 않으면 아래를 기본으로 쓴다.
`--mt-threshold 10 --min-genes 500 --max-genes 2500 --no-plots -o out/qc.h5ad`
근거: 미토 10% 초과는 죽어가는 세포, 유전자 500 미만은 빈 방울·저품질, 2,500 초과는 이중체 후보로 제외한다.
`--scrublet` 옵션은 쓰지 않는다. 실행 뒤 통과 세포 수(전/후)를 보고한다.
