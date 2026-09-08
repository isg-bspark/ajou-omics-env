# STEP 2 정답 — differential_expression 에 "QC 통과 게이트" 넣기
#
# server.py 의 differential_expression 안, 이 주석 두 줄
#   # ↓↓↓ 실습 2단계: 여기에 "QC 통과한 run 만 받는다" 게이트를 직접 넣으세요 ↓↓↓
#   #     (지금은 게이트가 없어, ...)
# 을 지우고 그 자리에 아래를 넣으세요. (qc_check 이 run["qc_passed"] 를 기록해 둡니다)
#
# 내가 정하는 것 : "QC 통과한 run 만 분석한다" — 그 규칙을 내 도구 안에 심는다
# 마무리 장면    : "QC 무시하고 분석해줘" → 거부 (내가 그은 선에 막힘)

    if not run.get("qc_passed"):
        return {"거부": "QC 를 통과한 run 만 분석합니다.",
                "다음": "qc_check(run_id) 를 먼저 통과시키세요."}
