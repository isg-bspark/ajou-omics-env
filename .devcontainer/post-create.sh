#!/usr/bin/env bash
# Codespace 가 처음 만들어질 때 한 번 실행됩니다.
set -euo pipefail

# uv · uvx · claude 네이티브 인스톨러가 쓰는 경로.
# 이 스크립트 안에서도 바로 부를 수 있도록 미리 얹는다.
export PATH="$HOME/.local/bin:$PATH"

echo "========================================"
echo " Setting up workshop environment"
echo "========================================"

echo
echo "[1/6] pip 업그레이드 & 분석·MCP 패키지 설치 (수 분 소요)"
python -m pip install --upgrade pip
pip install --no-cache-dir -r .devcontainer/requirements.txt

# --------------------------------------------------
# [2/6] MCP 서버 미리 받아두기
# --------------------------------------------------
# .devcontainer/tools.txt 에 적힌 서버를 uvx 환경에 미리 내려받는다.
# 실습 ③에서 처음 부를 때 기다리지 않기 위한 것이므로, 실패해도 진행한다.
# (uvx 는 실습 중에 필요하면 그때 다시 받는다)
echo
echo "[2/6] MCP 서버 미리 받아두기 (uvx)"

if ! command -v uv >/dev/null 2>&1; then
    echo "   ⚠ uv 를 찾지 못했습니다 — 실습 ③의 fetch 서버가 안 될 수 있습니다"
elif [ ! -f .devcontainer/tools.txt ]; then
    echo "   · .devcontainer/tools.txt 가 없어 건너뜁니다"
else
    if sed -e 's/#.*//' -e '/^[[:space:]]*$/d' .devcontainer/tools.txt \
        | xargs -r -n1 uv tool install; then
        uv tool list || true
    else
        echo "   ⚠ 일부 서버를 미리 받지 못했습니다 (실습 때 uvx 가 다시 시도합니다)"
    fi
fi

echo
echo "[3/6] Jupyter 커널 등록"
python -m ipykernel install --user --name ajou-omics --display-name "Python (ajou-omics)"

echo
echo "[4/6] Claude Code CLI 설치"
npm install -g @anthropic-ai/claude-code

# --------------------------------------------------
# [5/6] Claude Code 워크샵 설정
# --------------------------------------------------
echo
echo "[5/6] Claude Code 설정"

CLAUDE_SHELL_CONFIG="$HOME/.claude-workshop.sh"

cat > "$CLAUDE_SHELL_CONFIG" <<'EOF'
# --------------------------------------------------
# Claude Code workshop configuration
# --------------------------------------------------

# Claude Code 네이티브 인스톨러가 옮겨 놓는 경로
case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) export PATH="$HOME/.local/bin:$PATH" ;;
esac


# Codespaces secret 을 비워 둔 채 생성하면 빈 문자열이 주입될 수 있다.
# 빈 값이 남아 있으면 인증 순서 판단이 꼬이므로 아예 제거한다.
[ -n "${ANTHROPIC_API_KEY:-}" ]        || unset ANTHROPIC_API_KEY
[ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]  || unset CLAUDE_CODE_OAUTH_TOKEN


clear_claude_rejected_key() {

    # API Key 가 없으면 승인 프롬프트 자체가 뜨지 않으므로 할 일이 없음
    [ -n "${ANTHROPIC_API_KEY:-}" ] || return 0

    # ~/.claude.json 이 없으면 아무것도 하지 않음
    [ -f "$HOME/.claude.json" ] || return 0

    python3 <<'PY'
import json
import os
import tempfile

path = os.path.expanduser("~/.claude.json")

try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
except (OSError, json.JSONDecodeError):
    raise SystemExit(0)


responses = data.get("customApiKeyResponses")

if not isinstance(responses, dict):
    raise SystemExit(0)


# rejected 가 비어 있으면 수정할 필요 없음
if not responses.get("rejected"):
    raise SystemExit(0)


# rejected 기록 초기화
responses["rejected"] = []


# 안전하게 임시 파일을 만든 뒤 교체
directory = os.path.dirname(path)

fd, temp_path = tempfile.mkstemp(
    dir=directory,
    prefix=".claude.json.",
    text=True
)

try:
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    os.replace(temp_path, path)

except Exception:
    try:
        os.remove(temp_path)
    except OSError:
        pass

    raise
PY
}


claude() {

    # 이전에 API Key 사용 질문에서 No 를 선택했더라도
    # 다음 실행에서는 다시 선택할 수 있도록 rejected 초기화
    clear_claude_rejected_key

    # 실제 Claude Code 실행
    command claude "$@"
}
EOF


# --------------------------------------------------
# Shell 시작 시 설정 자동 로드
# --------------------------------------------------

SOURCE_LINE='source "$HOME/.claude-workshop.sh"'

# Bash
touch "$HOME/.bashrc"

if ! grep -Fq "$SOURCE_LINE" "$HOME/.bashrc"; then
    echo "$SOURCE_LINE" >> "$HOME/.bashrc"
fi

# Zsh 가 존재하면 같이 설정
if [ -f "$HOME/.zshrc" ]; then
    if ! grep -Fq "$SOURCE_LINE" "$HOME/.zshrc"; then
        echo "$SOURCE_LINE" >> "$HOME/.zshrc"
    fi
fi


# --------------------------------------------------
# 인증 상태 안내
# --------------------------------------------------
# Claude Code 의 인증 우선순위상 ANTHROPIC_API_KEY 가 CLAUDE_CODE_OAUTH_TOKEN
# 보다 앞서므로, 둘 다 등록되어 있으면 API Key 가 사용된다.
# https://code.claude.com/docs/en/authentication#authentication-precedence

if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    echo "   인증: ANTHROPIC_API_KEY 감지 — Console API Key 로 인증합니다"
    if [ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
        echo "         (CLAUDE_CODE_OAUTH_TOKEN 도 있지만 API Key 가 우선합니다)"
    fi
elif [ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
    echo "   인증: CLAUDE_CODE_OAUTH_TOKEN 감지 — 구독 계정으로 인증합니다"
else
    echo "   인증: 등록된 secret 이 없습니다."
    echo "         터미널에서 'claude' 실행 후 로그인하거나,"
    echo "         GitHub Settings ▸ Codespaces ▸ Secrets 에"
    echo "         ANTHROPIC_API_KEY 또는 CLAUDE_CODE_OAUTH_TOKEN 을 등록하세요"
fi


echo
python - <<'PY'
import anndata, scanpy
print(f"   scanpy {scanpy.__version__} / anndata {anndata.__version__}")
PY


# --------------------------------------------------
# [6/6] MCP 실습 환경 점검
# --------------------------------------------------
# 저장소가 마운트된 뒤에만 할 수 있는 일이라 여기에 있다.
# 점검일 뿐이므로 통과하지 못해도 Codespace 생성은 계속 진행한다.
echo
echo "[6/6] MCP · SKILL 실습 환경 점검"

if [ -f agent_lab/verify.py ]; then
    python3 agent_lab/verify.py || \
        echo "   ⚠ 준비되지 않은 항목이 있습니다 — 'bash agent_lab/doctor.sh' 로 자세히 볼 수 있습니다"
else
    echo "   · agent_lab/verify.py 가 없어 건너뜁니다"
fi


echo
echo "========================================"
echo " Setup complete!"
echo "========================================"
echo
echo "새 터미널을 열고 다음을 실행하세요:"
echo
echo "    claude"
echo
echo "MCP · SKILL 실습(2일차 1교시)은 README_agentlab.md 를 여세요."
echo
