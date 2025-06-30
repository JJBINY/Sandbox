from autogen_ext.code_executors import DockerCommandLineCodeExecutor

class ExecutionValidationAgent(AssistantAgent):
    def __init__(self, model_client):
        super().__init__(
            name="Execution_Validator",
            model_client=model_client,
            system_message="""
            당신은 테스트 실행 및 검증 전문가입니다.
            
            주요 역할:
            1. 테스트 스위트 자동 실행 및 결과 분석
            2. 성능 메트릭 수집 및 벤치마킹
            3. 코드 커버리지 분석 및 보고
            4. 회귀 테스트 및 품질 게이트 검증
            
            검증 기준:
            - 모든 테스트 통과 여부 확인
            - 코드 커버리지 90% 이상 달성
            - 성능 저하 없음 확인
            - 보안 취약점 스캐닝 결과 검토
            """
        )
        
        # Docker 환경에서 안전한 코드 실행
        self.code_executor = DockerCommandLineCodeExecutor(
            work_dir="./workspace",
            image="python:3.11-slim"
        )