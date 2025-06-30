from app.agents.agent_factory import AgentFactory
from typing import Optional


class SimpleChatAgent:
    """단일 에이전트 채팅 시스템 - AgentFactory 사용"""

    def __init__(self, agent_factory: Optional[AgentFactory] = None,
                 custom_system_message: Optional[str] = None):
        """
        SimpleChatAgent 초기화

        Args:
            agent_factory (AgentFactory, optional): 에이전트 팩토리 인스턴스
            custom_system_message (str, optional): 커스텀 시스템 메시지
        """
        try:
            self.agent_factory = agent_factory or AgentFactory()
            self.assistant = self.agent_factory.create_simple_chat_agent(
                name="ChatAssistant",
                custom_system_message=custom_system_message
            )
            print("✅ 채팅 에이전트 초기화 완료")
        except Exception as e:
            print(f"❌ 채팅 에이전트 초기화 실패: {e}")
            raise

    async def start_conversation(self, initial_message: str = None):
        """대화 시작"""
        print("🚀 Autogen 0.4 + Gemini 채팅 시작!")
        print("대화를 종료하려면 'exit' 또는 'quit'을 입력하세요.\n")

        if not initial_message:
            initial_message = """가벼운 인삿말을 부탁해"""

        try:
            # 첫 번째 메시지 처리
            response = await self.assistant.run(task=initial_message)
            print(f"🤖 Assistant: {response.messages[-1].content}\n")

            # 대화 루프
            while True:
                user_input = input("👤 You: ").strip()

                if user_input.lower() in ['exit', 'quit', '종료']:
                    print("👋 대화를 종료합니다!")
                    break

                if not user_input:
                    continue

                # 에이전트 응답
                response = await self.assistant.run(task=user_input)
                print(f"🤖 Assistant: {response.messages[-1].content}\n")

        except KeyboardInterrupt:
            print("\n👋 대화가 중단되었습니다!")
        except Exception as e:
            print(f"❌ 오류가 발생했습니다: {e}")
        finally:
            # 리소스 정리
            await self.cleanup()

    async def cleanup(self):
        """리소스 정리"""
        try:
            if hasattr(self, 'agent_factory'):
                await self.agent_factory.cleanup()
        except Exception as e:
            print(f"⚠️ 정리 중 오류: {e}")