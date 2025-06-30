"""
테스트 실행 및 결과 분석을 담당하는 모듈
"""
import subprocess
from pathlib import Path
from typing import List
from app.data_model.test_models import TestCase, TestResult
from app.data_model.code_models import CodeModule
from app.config.settings import AppConfig


class TestExecutor:
    """테스트 실행 및 관리"""

    def __init__(self, work_dir: Path):
        self.work_dir = work_dir
        self.config = AppConfig()

    def write_files(self, test_cases: List[TestCase], code_modules: List[CodeModule]):
        """테스트와 코드 파일 생성"""
        # 테스트 파일 작성
        for tc in test_cases:
            test_path = self.work_dir / "tests" / tc.file_name
            with open(test_path, 'w', encoding='utf-8') as f:
                f.write(tc.test_code)

        # 코드 파일 작성
        for cm in code_modules:
            code_path = self.work_dir / "src" / cm.file_name
            with open(code_path, 'w', encoding='utf-8') as f:
                f.write(cm.code)

        # requirements.txt 생성
        self._create_requirements_file()

    def _create_requirements_file(self):
        """requirements.txt 생성"""
        requirements_content = """pytest>=7.0.0
pytest-cov>=4.0.0
"""
        with open(self.work_dir / "requirements.txt", 'w') as f:
            f.write(requirements_content)

    async def run_tests(self) -> TestResult:
        """실제 테스트 실행"""
        try:
            result = subprocess.run(
                [
                    "python", "-m", "pytest",
                    "tests/",
                    "-v",
                    "--tb=short",
                    f"--cov=src",
                    "--cov-report=term"
                ],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=self.config.TIMEOUT_SECONDS
            )

            passed = result.returncode == 0
            test_output = result.stdout + result.stderr
            coverage_info = self._extract_coverage_info(test_output)
            error_details = result.stderr if not passed else ""

            return TestResult(
                passed=passed,
                test_output=test_output,
                coverage_info=coverage_info,
                error_details=error_details
            )

        except subprocess.TimeoutExpired:
            return TestResult(
                passed=False,
                test_output="테스트 실행 시간 초과",
                coverage_info="",
                error_details="타임아웃"
            )
        except Exception as e:
            return TestResult(
                passed=False,
                test_output=str(e),
                coverage_info="",
                error_details=str(e)
            )

    def _extract_coverage_info(self, test_output: str) -> str:
        """테스트 출력에서 커버리지 정보 추출"""
        lines = test_output.split('\n')
        coverage_lines = [line for line in lines if '%' in line and 'TOTAL' in line]
        return coverage_lines[0] if coverage_lines else "커버리지 정보 없음"
