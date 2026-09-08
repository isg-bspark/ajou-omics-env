#!/usr/bin/env bash
# 코드스페이스에서 Claude Code 가 안 될 때.  bash agent_lab/doctor.sh
echo ""
echo "════════ 1. claude 설치 ════════"
command -v claude && claude --version 2>&1 | head -1 || echo "✗ PATH 에 claude 없음"
echo "PATH: $PATH"
ls -la ~/.local/bin/claude 2>/dev/null || echo "(~/.local/bin/claude 없음)"

echo ""
echo "════════ 2. API 키 ════════"
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  echo "✓ ANTHROPIC_API_KEY 있음  (${#ANTHROPIC_API_KEY}자, 앞 12자: ${ANTHROPIC_API_KEY:0:12}…)"
  case "$ANTHROPIC_API_KEY" in sk-ant-*) echo "  형식 OK";; *) echo "  ⚠ sk-ant- 로 시작하지 않음";; esac
else
  echo "✗ ANTHROPIC_API_KEY 없음"
fi
[ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ] && echo "  (CLAUDE_CODE_OAUTH_TOKEN 도 있음)"
env | grep -c ANTHROPIC | xargs echo "ANTHROPIC 관련 환경변수 개수:"

echo ""
echo "════════ 3. 네트워크 ════════"
for h in api.anthropic.com claude.ai registry.npmjs.org pypi.org; do
  if curl -s -o /dev/null -w "%{http_code}" -m 8 "https://$h" >/tmp/_c 2>/dev/null; then
    echo "✓ $h  → HTTP $(cat /tmp/_c)"
  else
    echo "✗ $h  → 연결 실패 (차단 가능)"
  fi
done

echo ""
echo "════════ 4. 파이썬 · mcp ════════"
python3 --version 2>&1
echo "python3 = $(python3 -c 'import sys;print(sys.executable)')"
echo "pip     = $(command -v pip || echo 없음)"
if python3 -c "import mcp" 2>/dev/null; then
  python3 -c "import importlib.metadata as m;print('✓ mcp v'+m.version('mcp'))"
else
  echo "✗ mcp 없음  →  python3 -m pip install -r .devcontainer/requirements.txt"
fi
echo ""
echo "════════ 4b. 스킬 설치 도구 (실습 4단계) ════════"
if command -v gh >/dev/null; then
  echo "✓ gh = $(gh --version 2>&1 | head -1)  (gh skill 은 2.90+ 필요)"
else
  echo "✗ gh 없음  (npx 로 대체 가능)"
fi
command -v node >/dev/null && echo "✓ node = $(node --version)" || echo "✗ node 없음  →  npx 경로 불가"

echo ""
echo "════════ 5. 환경 점검 ════════"
python3 agent_lab/verify.py 2>&1 | tail -14

echo ""
echo "════════ 6. Claude Code 설정 ════════"
ls -la ~/.claude* 2>/dev/null | head -5 || echo "(~/.claude 없음 — 아직 한 번도 실행 안 함)"
echo ""
