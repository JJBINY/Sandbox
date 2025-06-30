import difflib
from typing import List, Tuple, Optional

class ConflictResolver:
    def __init__(self):
        self.resolution_strategies = {
            'auto': self.auto_resolve,
            'user': self.user_resolve,
            'agent': self.agent_resolve
        }
        
    def detect_conflicts(self, base_content: str, local_content: str, 
                        remote_content: str) -> List[Tuple[int, int, str]]:
        """3-way 병합에서 충돌 감지"""
        conflicts = []
        
        base_lines = base_content.splitlines()
        local_lines = local_content.splitlines()
        remote_lines = remote_content.splitlines()
        
        # 3-way diff 분석
        local_diff = list(difflib.unified_diff(base_lines, local_lines))
        remote_diff = list(difflib.unified_diff(base_lines, remote_lines))
        
        # 충돌 영역 식별
        for i, (local_line, remote_line) in enumerate(zip(local_diff, remote_diff)):
            if local_line != remote_line and local_line.startswith('+') and remote_line.startswith('+'):
                conflicts.append((i, i+1, 'content_conflict'))
                
        return conflicts
        
    async def resolve_conflicts(self, conflicts: List, strategy: str = 'user'):
        """충돌 해결 전략 실행"""
        resolver = self.resolution_strategies.get(strategy, self.user_resolve)
        return await resolver(conflicts)
        
    async def user_resolve(self, conflicts: List):
        """사용자 개입을 통한 충돌 해결"""
        resolutions = []
        
        for conflict in conflicts:
            # UI를 통해 사용자에게 충돌 상황 제시
            resolution = await self.present_conflict_to_user(conflict)
            resolutions.append(resolution)
            
        return resolutions
        
    async def agent_resolve(self, conflicts: List):
        """AI 에이전트를 통한 자동 충돌 해결"""
        from autogen_agentchat.agents import AssistantAgent
        
        resolver_agent = AssistantAgent(
            name="Conflict_Resolver",
            system_message="""
            당신은 코드 충돌 해결 전문가입니다. 
            두 개의 코드 변경사항이 충돌할 때, 최선의 해결 방안을 제시해주세요.
            
            원칙:
            1. 기능 유지: 두 변경사항의 의도를 모두 보존
            2. 코드 품질: 더 나은 코드 품질을 가진 방향 선택
            3. 테스트 호환: 기존 테스트가 통과하는 방향 우선
            """
        )
        
        resolutions = []
        for conflict in conflicts:
            resolution = await resolver_agent.run(
                task=f"다음 코드 충돌을 해결해주세요: {conflict}"
            )
            resolutions.append(resolution)
            
        return resolutions