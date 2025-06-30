"""
에이전트 응답에서 코드를 추출하는 파서
"""
import re
from typing import List
from app.data_model.test_models import TestCase
from app.data_model.code_models import CodeModule


class CodeParser:
    """코드 추출 및 파싱 유틸리티"""

    @staticmethod
    def extract_test_cases(response) -> List[TestCase]:
        """응답에서 테스트 케이스 추출"""
        test_cases = []

        for message in response.messages:
            content = message.content

            # Python 코드 블록 찾기
            code_blocks = re.findall(r'```python\s*\n(.*?)\n```', content, re.DOTALL)

            for i, code in enumerate(code_blocks):
                if 'test_' in code and 'import pytest' in code:
                    # 파일명 추출 (주석에서)
                    file_match = re.search(r'#\s*(test_\w+\.py)', code)
                    file_name = file_match.group(1) if file_match else f"test_module_{i + 1}.py"

                    test_cases.append(TestCase(
                        name=f"TestCase_{i + 1}",
                        description=f"Generated test case {i + 1}",
                        test_code=code,
                        file_name=file_name
                    ))

        return test_cases

    @staticmethod
    def extract_code_modules(response) -> List[CodeModule]:
        """응답에서 코드 모듈 추출"""
        code_modules = []

        for message in response.messages:
            content = message.content

            # Python 코드 블록 찾기
            code_blocks = re.findall(r'```python\s*\n(.*?)\n```', content, re.DOTALL)

            for i, code in enumerate(code_blocks):
                if 'class ' in code or 'def ' in code and 'test_' not in code:
                    # 파일명 추출 (주석에서)
                    file_match = re.search(r'#\s*(\w+\.py)', code)
                    file_name = file_match.group(1) if file_match else f"module_{i + 1}.py"

                    code_modules.append(CodeModule(
                        name=f"Module_{i + 1}",
                        file_name=file_name,
                        code=code,
                        description=f"Generated code module {i + 1}"
                    ))

        return code_modules
