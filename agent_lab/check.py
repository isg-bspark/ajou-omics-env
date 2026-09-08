"""
MCP 서버가 제대로 뜨는지 Claude 없이 혼자 확인합니다.

    python3 agent_lab/check.py                    # 기본: agent_lab/server.py
    python3 agent_lab/check.py agent_lab/server.py  # 특정 서버
"""
import asyncio, sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parent.parent
target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "agent_lab" / "server.py"
if not target.is_absolute():
    target = ROOT / target


def show(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


async def main() -> int:
    if not target.exists():
        print(f"\n  파일이 없습니다: {target}")
        print("  서버가 망가졌다면 정답본을 복사하세요:")
        print("    cp agent_lab/reference/server_완성본.py agent_lab/server.py\n")
        return 1

    print(f"\n{show(target)} 확인 중...\n")
    try:
        p = StdioServerParameters(command=sys.executable, args=[str(target)])
        async with stdio_client(p) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                tools = (await s.list_tools()).tools
                print(f"  서버가 떴습니다.  도구 {len(tools)}개\n")
                for t in tools:
                    first = (t.description or "").strip().split("\n")[0]
                    print(f"    · {t.name}  —  {first}")
                print("\n  점검 통과\n")
                return 0
    except Exception as e:
        print(f"  서버가 못 떴습니다: {type(e).__name__}")
        print(f"  {str(e)[:200]}\n")
        print("  직접 실행해서 에러를 보세요:")
        print(f"    python3 {show(target)}\n")
        return 1


raise SystemExit(asyncio.run(main()))
