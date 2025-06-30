import asyncio
import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from simple_chat.chat_agent import SimpleChatAgent


async def main():
    """메인 실행 함수"""
    try:
        # 방법 1: 기본 채팅 에이전트
        print("=== 기본 채팅 에이전트 ===")
        chat_agent = SimpleChatAgent()
        await chat_agent.start_conversation()

    except Exception as e:
        print(f"❌ 실행 중 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main())
