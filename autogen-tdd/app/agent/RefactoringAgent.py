class RefactoringAgent(AssistantAgent):
    def __init__(self, model_client):
        super().__init__(
            name="Refactoring_Specialist",
            model_client=model_client,
            system_message="""
            당신은 코드 리팩토링 및 품질 개선 전문가입니다.
            
            주요 역할:
            1. 코드 스멜 감지 및 개선 방안 제시
            2. 중복 코드 제거 및 추상화 적용
            3. 성능 최적화 및 메모리 효율성 개선
            4. 아키텍처 개선 및 확장성 증대
            
            리팩토링 원칙:
            - 기능 변경 없이 구조만 개선
            - 각 리팩토링 후 테스트 실행으로 검증
            - 점진적 개선으로 리스크 최소화
            - 가독성과 유지보수성 우선 고려
            """
        )