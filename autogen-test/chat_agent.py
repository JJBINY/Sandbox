# chat_agent.py - 간소화된 단일 에이전트 채팅
import asyncio
import os
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelInfo

# .env 파일 로드
load_dotenv()

class Config:
    """환경 설정 관리"""
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    GEMINI_BASE_URL = os.getenv('GEMINI_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/openai/')
    
    @classmethod
    def validate_config(cls):
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
        print("✅ 설정이 유효합니다.")
        print(f"📱 사용 모델: {cls.GEMINI_MODEL}")
        return True

class ChatAgent:
    """단일 에이전트 채팅 시스템"""
    
    def __init__(self):
        # 설정 검증
        Config.validate_config()
        
        # Gemini 모델 클라이언트 생성 (OpenAI 호환 API 사용)
        self.model_client = OpenAIChatCompletionClient(
            model=Config.GEMINI_MODEL,
            api_key=Config.GEMINI_API_KEY,
            base_url=Config.GEMINI_BASE_URL,
            model_info=ModelInfo(
                vision=True,
                function_calling=True,
                json_output=True,
                family="gemini",
                structured_output=True
            )
        )
        
        # 어시스턴트 에이전트 생성
        self.assistant = AssistantAgent(
            name="ChatAssistant",
            model_client=self.model_client,
            system_message="""당신은 친근하고 도움이 되는 AI 어시스턴트입니다.
            사용자의 질문에 정확하고 유용한 답변을 제공하세요.
            필요시 코드나 예제를 포함하여 설명해주세요.
            
            대화는 자연스럽고 친근하게 진행하되, 전문적인 정보도 제공할 수 있습니다."""
        )
    
    async def start_conversation(self, initial_message: str = None):
        """대화 시작"""
        print("🚀 Autogen 0.4 + Gemini 채팅 시작!")
        print("대화를 종료하려면 'exit' 또는 'quit'을 입력하세요.\n")
        
        if not initial_message:
            initial_message = """안녕하세요! Autogen 0.4와 Gemini API를 사용한 채팅 시스템입니다.
            어떤 도움이 필요하신가요?"""
        
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
            if hasattr(self, 'model_client'):
                await self.model_client.close()
        except Exception as e:
            print(f"⚠️ 정리 중 오류: {e}")

async def main():
    """메인 실행 함수"""
    try:
        chat_agent = ChatAgent()
        await chat_agent.start_conversation()
        
    except Exception as e:
        print(f"❌ 초기화 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    asyncio.run(main())