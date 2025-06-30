"""
에이전트들을 생성하는 팩토리
"""
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelInfo
from typing import Dict, Optional
from app.config.settings import AppConfig
from app.utils.file_utils import read_message_file


class AgentFactory:
    """에이전트 팩토리"""

    def __init__(self):
        self.config = AppConfig()
        self.model_client = self._create_model_client()

    def _create_model_client(self) -> OpenAIChatCompletionClient:
        """모델 클라이언트 생성"""
        return OpenAIChatCompletionClient(
            model=self.config.GEMINI_MODEL,
            api_key=self.config.GEMINI_API_KEY,
            base_url=self.config.GEMINI_BASE_URL,
            model_info=ModelInfo(
                vision=True,
                function_calling=True,
                json_output=True,
                family="gemini"
            )
        )

    def create_simple_chat_agent(self, name: str = "ChatAssistant",
                                 custom_system_message: Optional[str] = None) -> AssistantAgent:
        """
        단순 채팅용 에이전트 생성

        Args:
            name (str): 에이전트 이름
            custom_system_message (str, optional): 커스텀 시스템 메시지

        Returns:
            AssistantAgent: 설정된 채팅 에이전트
        """
        system_message = custom_system_message or self._get_default_chat_system_message()

        return AssistantAgent(
            name=name,
            model_client=self._create_model_client(),
            system_message=system_message
        )

    def _get_default_chat_system_message(self) -> str:
        """기본 채팅 시스템 메시지"""
        return """당신은 친근하고 도움이 되는 AI 어시스턴트입니다.
        사용자의 질문에 정확하고 유용한 답변을 제공하세요.
        필요시 코드나 예제를 포함하여 설명해주세요.

        대화는 자연스럽고 친근하게 진행하되, 전문적인 정보도 제공할 수 있습니다."""

    def create_tdd_agents(self) -> Dict[str, AssistantAgent]:
        """TDD 전문 에이전트들 생성"""

        test_designer = AssistantAgent(
            name="TestDesigner",
            model_client=self._create_model_client(),
            system_message=read_message_file(f"{self.config.PROMPTS_DIR}/test_designer.txt")
        )

        code_generator = AssistantAgent(
            name="CodeGenerator",
            model_client=self._create_model_client(),
            system_message=read_message_file(f"{self.config.PROMPTS_DIR}/code_generator.txt")
        )

        test_runner = AssistantAgent(
            name="TestRunner",
            model_client=self._create_model_client(),
            system_message=read_message_file(f"{self.config.PROMPTS_DIR}/test_runner.txt")
        )

        refactor_agent = AssistantAgent(
            name="RefactorAgent",
            model_client=self._create_model_client(),
            system_message=read_message_file(f"{self.config.PROMPTS_DIR}/refactor_agent.txt")
        )

        return {
            'test_designer': test_designer,
            'code_generator': code_generator,
            'test_runner': test_runner,
            'refactor_agent': refactor_agent
        }

    async def cleanup(self):
        """리소스 정리"""
        try:
            await self.model_client.close()
        except Exception as e:
            print(f"⚠️ 모델 클라이언트 정리 중 오류: {e}")