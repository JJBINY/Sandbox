from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination

class TDDOrchestrator(AssistantAgent):
    def __init__(self, model_client):
        super().__init__(
            name="TDD_Orchestrator",
            model_client=model_client,
            system_message="""
            당신은 TDD 바이브코딩 시스템의 총 책임자입니다.
            
            주요 역할:
            1. 사용자 요구사항을 분석하여 TDD 워크플로우 계획 수립
            2. 테스트 생성, 코드 구현, 검증, 리팩토링 에이전트들의 작업 조율
            3. 각 단계에서 사용자 피드백 요청 및 처리
            4. 품질 기준 확인 및 최종 승인
            
            작업 프로세스:
            - 사용자 승인 없이는 다음 단계로 진행하지 않음
            - 각 에이전트의 결과물에 대해 사용자 검토 요청
            - 피드백을 반영한 수정 작업 지시
            """
        )