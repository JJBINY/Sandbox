from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination

class InteractiveTDDWorkflow:
    def __init__(self, agents, user_proxy):
        self.agents = agents
        self.user_proxy = user_proxy
        self.current_phase = "planning"
        self.user_approvals = {}
        
    async def execute_tdd_cycle(self, requirement):
        """사용자 피드백이 포함된 TDD 사이클 실행"""
        
        # 1. 기획 단계 - 사용자 개입 가능
        await self.planning_phase(requirement)
        
        # 2. 테스트 생성 → 사용자 검증 → 수정 → 확인
        await self.test_generation_phase()
        
        # 3. 코드 구현 → 사용자 피드백 → 수정
        await self.code_implementation_phase()
        
        # 4. 리팩토링 → 사용자 승인
        await self.refactoring_phase()
        
    async def planning_phase(self, requirement):
        """기획 단계에서 사용자 개입 처리"""
        planning_team = RoundRobinGroupChat(
            [self.agents['orchestrator'], self.user_proxy],
            termination_condition=TextMentionTermination("PLANNING_APPROVED")
        )
        
        result = await planning_team.run(
            task=f"다음 요구사항에 대한 TDD 계획을 수립해주세요: {requirement}"
        )
        
        self.user_approvals['planning'] = result
        
    async def test_generation_phase(self):
        """테스트 생성 단계의 사용자 검증 루프"""
        while True:
            # 테스트 생성
            test_result = await self.agents['test_generator'].run(
                task="계획된 요구사항에 대한 테스트 케이스를 생성해주세요."
            )
            
            # 사용자 검증 요청
            validation_team = RoundRobinGroupChat(
                [self.agents['orchestrator'], self.user_proxy],
                termination_condition=TextMentionTermination(["APPROVED", "MODIFY"])
            )
            
            validation = await validation_team.run(
                task=f"생성된 테스트를 검토해주세요:\n{test_result}"
            )
            
            if "APPROVED" in validation.messages[-1].content:
                break
            elif "MODIFY" in validation.messages[-1].content:
                # 수정 요청 처리
                continue