"""
TDD 바이브코딩 시스템의 데이터 모델들
"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class TestCase:
    """테스트 케이스 정의"""
    name: str
    description: str
    test_code: str
    file_name: str
    created_at: Optional[datetime] = None

@dataclass
class CodeModule:
    """코드 모듈 정의"""
    name: str
    file_name: str
    code: str
    description: str
    created_at: Optional[datetime] = None

@dataclass
class TestResult:
    """테스트 실행 결과"""
    passed: bool
    test_output: str
    coverage_info: str
    error_details: str
    execution_time: Optional[float] = None

@dataclass
class TDDIteration:
    """TDD 반복 주기 결과"""
    iteration: int
    test_cases: List[TestCase]
    generated_code: List[CodeModule]
    test_result: TestResult
    success: bool
    feedback: str
    timestamp: Optional[datetime] = None