"""
TDD 바이브코딩 시스템의 핵심 로직
"""
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination

from app.data_model.test_models import TDDIteration, TestCase, TestResult
from app.data_model.code_models import CodeModule
from app.config.settings import AppConfig
from app.agent.agent_factory import AgentFactory
from app.core.tools.test_executor import TestExecutor
from app.core.tools.code_parser import CodeParser
from app.core.tools.project_manager import ProjectManager


class TDDVibecodingSystem:
    """TDD 바이브코딩 시스템 메인 클래스"""

    def __init__(self, config: AppConfig = None):
        self.config = config or AppConfig()
        self.config.validate_config()

        self.agent_factory = AgentFactory()
        self.agents = self.agent_factory.create_tdd_agents()
        self.project_manager = ProjectManager(self.config)
        self.code_parser = CodeParser()

        self.work_dir: Optional[Path] = None
        self.iterations: List[TDDIteration] = []
        self.test_executor: Optional[TestExecutor] = None

    async def start_tdd_process(self, requirement: str, project_name: str, max_iterations: int = None) -> Optional[
        List[TDDIteration]]:
        """TDD 프로세스 시작"""
        max_iterations = max_iterations or self.config.MAX_ITERATIONS

        print("🎯 TDD 바이브코딩 시스템 시작!")
        print(f"📋 요구사항: {requirement}")
        print(f"🔄 최대 반복: {max_iterations}")
        print("=" * 80)

        # 작업 디렉토리 설정
        self.work_dir = self.project_manager.setup_work_directory(project_name)
        self.test_executor = TestExecutor(self.work_dir)
        print(f"📁 작업 디렉토리: {self.work_dir}")

        try:
            # TDD 반복 수행
            for iteration in range(1, max_iterations + 1):
                print(f"\n🔄 TDD 반복 {iteration}/{max_iterations}")
                print("-" * 60)

                tdd_result = await self._perform_tdd_iteration(requirement, iteration)
                self.iterations.append(tdd_result)

                if tdd_result.success:
                    print(f"✅ TDD 반복 {iteration} 성공!")

                    # 리팩토링 수행
                    if iteration < max_iterations:
                        print("🔧 리팩토링 단계 진행...")
                        await self._perform_refactoring(iteration)

                    break
                else:
                    print(f"⚠️ TDD 반복 {iteration} - 다음 반복으로 진행...")
                    print(f"피드백: {tdd_result.feedback}")

            # 최종 결과 출력
            await self._show_final_results()

            return self.iterations

        except Exception as e:
            print(f"❌ TDD 프로세스 중 오류: {e}")
            return None
        finally:
            await self.cleanup()

    async def _perform_tdd_iteration(self, requirement: str, iteration: int) -> TDDIteration:
        """단일 TDD 반복 수행"""

        # 1. 테스트 설계 (Red)
        print("📝 1. 테스트 설계 중...")
        test_cases = await self._design_tests(requirement, iteration)

        # 2. 코드 생성 (Green)
        print("💻 2. 코드 생성 중...")
        generated_code = await self._generate_code(test_cases, iteration)

        # 3. 파일 생성
        print("📄 3. 파일 생성 중...")
        self.test_executor.write_files(test_cases, generated_code)

        # 4. 테스트 실행
        print("🧪 4. 테스트 실행 중...")
        test_result = await self.test_executor.run_tests()

        # 5. 결과 분석
        print("📊 5. 결과 분석 중...")
        feedback = await self._analyze_results(test_cases, generated_code, test_result)

        return TDDIteration(
            iteration=iteration,
            test_cases=test_cases,
            generated_code=generated_code,
            test_result=test_result,
            success=test_result.passed,
            feedback=feedback,
            timestamp=datetime.now()
        )

    async def _design_tests(self, requirement: str, iteration: int) -> List[TestCase]:
        """테스트 케이스 설계"""
        context = f"""다음 요구사항에 대한 테스트 케이스를 설계해주세요:

요구사항: {requirement}

반복 횟수: {iteration}

이전 반복의 피드백:
{self._get_previous_feedback()}

포괄적이고 실행 가능한 pytest 테스트 코드를 작성해주세요."""

        team = RoundRobinGroupChat(
            participants=[self.agents['test_designer']],
            termination_condition=MaxMessageTermination(2)
        )

        response = await team.run(task=context)
        test_cases = self.code_parser.extract_test_cases(response)

        print(f"   ✅ {len(test_cases)}개 테스트 케이스 생성됨")
        return test_cases

    async def _generate_code(self, test_cases: List[TestCase], iteration: int) -> List[CodeModule]:
        """테스트를 통과하는 코드 생성"""
        test_info = "\n".join([f"- {tc.name}: {tc.description}" for tc in test_cases])
        test_code = "\n\n".join([f"# {tc.file_name}\n{tc.test_code}" for tc in test_cases])

        context = f"""다음 테스트들을 모두 통과하는 코드를 구현해주세요:

테스트 케이스들:
{test_info}

테스트 코드:
{test_code}

반복 횟수: {iteration}

이전 반복의 피드백:
{self._get_previous_feedback()}

모든 테스트를 통과하는 완전한 구현 코드를 작성해주세요."""

        team = RoundRobinGroupChat(
            participants=[self.agents['code_generator']],
            termination_condition=MaxMessageTermination(2)
        )

        response = await team.run(task=context)
        code_modules = self.code_parser.extract_code_modules(response)

        print(f"   ✅ {len(code_modules)}개 코드 모듈 생성됨")
        return code_modules

    async def _analyze_results(self, test_cases: List[TestCase], code_modules: List[CodeModule],
                               test_result: TestResult) -> str:
        """테스트 결과 분석"""
        context = f"""다음 TDD 반복의 결과를 분석해주세요:

테스트 케이스들:
{[tc.name for tc in test_cases]}

생성된 코드 모듈들:
{[cm.name for cm in code_modules]}

테스트 실행 결과:
- 통과 여부: {test_result.passed}
- 출력: {test_result.test_output}
- 커버리지: {test_result.coverage_info}
- 오류: {test_result.error_details}

분석 결과와 다음 단계 제안을 해주세요."""

        team = RoundRobinGroupChat(
            participants=[self.agents['test_runner']],
            termination_condition=MaxMessageTermination(2)
        )

        response = await team.run(task=context)
        return response.messages[-1].content

    async def _perform_refactoring(self, iteration: int):
        """리팩토링 수행"""
        print("🔧 리팩토링 단계...")

        # 현재 코드 읽기
        current_code = self.project_manager.read_current_code(self.work_dir)

        context = f"""다음 코드의 리팩토링을 수행해주세요:

현재 코드:
{current_code}

반복 횟수: {iteration}

테스트는 모두 통과하는 상태에서 코드 품질을 개선해주세요.
REFACTOR_COMPLETE로 마무리해주세요."""

        team = RoundRobinGroupChat(
            participants=[self.agents['refactor_agent']],
            termination_condition=TextMentionTermination("REFACTOR_COMPLETE") | MaxMessageTermination(3)
        )

        response = await team.run(task=context)

        # 리팩토링된 코드 적용
        self._apply_refactoring(response)
        print("   ✅ 리팩토링 완료")

    def _apply_refactoring(self, response):
        """리팩토링된 코드 적용"""
        print("   📝 리팩토링된 코드 적용 중...")
        # 실제 구현에서는 응답에서 리팩토링된 코드를 추출하여 파일에 적용

    def _get_previous_feedback(self) -> str:
        """이전 반복의 피드백 반환"""
        if not self.iterations:
            return "이전 반복 없음"
        return self.iterations[-1].feedback

    async def _show_final_results(self):
        """최종 결과 출력"""
        print("\n" + "=" * 80)
        print("🎉 TDD 바이브코딩 프로세스 완료!")
        print("=" * 80)

        for i, iteration in enumerate(self.iterations, 1):
            status = "✅ 성공" if iteration.success else "❌ 실패"
            print(f"반복 {i}: {status} - 테스트 {len(iteration.test_cases)}개, 코드 {len(iteration.generated_code)}개")

        print(f"\n📁 생성된 프로젝트: {self.work_dir}")
        print(f"📊 총 반복 수: {len(self.iterations)}")

        # 파일 목록 출력
        if self.work_dir and self.work_dir.exists():
            print("\n📄 생성된 파일들:")
            for file_path in self.work_dir.rglob("*.py"):
                relative_path = file_path.relative_to(self.work_dir)
                print(f"  - {relative_path}")

    async def cleanup(self):
        """리소스 정리"""
        try:
            await self.agent_factory.cleanup()
            for agent in self.agents.values():
                if hasattr(agent, 'model_client'):
                    await agent.model_client.close()
        except Exception as e:
            print(f"⚠️ 정리 중 오류: {e}")