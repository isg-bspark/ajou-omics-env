#!/usr/bin/env bash
# PART 3 (2일차 1교시 · 30분) 시작 상태 만들기 + 환경 점검
#   bash agent_lab/part3_setup.sh              # 시작 상태로 되돌리고 점검
#   bash agent_lab/part3_setup.sh --with-skill # gh skill install 이 안 될 때: 저장소 사본으로 scanpy 스킬 설치
#
# 공유 파일(.claude/settings.json)은 건드리지 않는다 — 저장소에 커밋된 그대로 둔다(2교시와 공유).
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
WITH_SKILL=0; [ "${1:-}" = "--with-skill" ] && WITH_SKILL=1

echo "════════════════════════════════════════"
echo "  PART 3 · 시작 상태 만들기"
echo "════════════════════════════════════════"

# ① .mcp.json 은 비운다 — ②에서 학생이 biomcp·ols·lab-mcp 를 직접 넣는다 (2교시도 빈 상태에서 시작)
printf '{\n  "mcpServers": {}\n}\n' > .mcp.json
echo "  ✓ .mcp.json  비움 (②에서 채움)"

# ② 내 서버(lab-mcp)는 ②에서 학생이 직접 만든다 — 시작 상태에는 없다
rm -f agent_lab/lab_mcp.py
echo "  ✓ agent_lab/lab_mcp.py  없음 (②에서 직접 만든다)"

# ③ scanpy 스킬은 ①에서 gh skill install 로 설치한다 (2교시 스킬은 건드리지 않는다)
rm -rf .claude/skills/scanpy
if [ "$WITH_SKILL" = "1" ]; then
  mkdir -p .claude/skills
  cp -R agent_lab/reference/skills/scanpy .claude/skills/scanpy
  echo "  ✓ .claude/skills/scanpy  저장소 사본으로 설치 (--with-skill)"
else
  echo "  ✓ .claude/skills/scanpy  없음 (①에서 gh skill install)"
fi

# ④ 1교시 산출물만 정리 (2교시의 results/ figures/ 는 건드리지 않는다)
rm -rf out; mkdir -p out
rm -f agent_lab/.runs.json
echo "  ✓ out/  정리"

echo
python3 agent_lab/verify.py
