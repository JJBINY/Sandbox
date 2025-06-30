"""
TDD 예제들을 관리하는 모듈
"""
from typing import Dict


class TDDExamples:
    """TDD 예제들"""

    @staticmethod
    def get_example_requirements() -> Dict[str, Dict[str, str]]:
        """예제 요구사항 목록"""
        return {
            "1": {
                "title": "계산기 클래스",
                "description": "기본 사칙연산(+, -, *, /)과 제곱근, 거듭제곱 기능을 제공하는 Calculator 클래스를 구현하세요. 0으로 나누기 오류와 음수의 제곱근 오류를 적절히 처리해야 합니다."
            },
            "2": {
                "title": "문자열 유틸리티",
                "description": "문자열을 처리하는 StringUtils 클래스를 구현하세요. 회문 검사, 단어 개수 세기, 첫 글자 대문자로 변환, 특수문자 제거 기능이 필요합니다."
            },
            "3": {
                "title": "은행 계좌 시스템",
                "description": "BankAccount 클래스를 구현하세요. 잔고 조회, 입금, 출금, 계좌 이체 기능이 필요하고, 잔고 부족 시 예외 처리가 필요합니다."
            },
            "4": {
                "title": "할 일 관리자",
                "description": "TodoManager 클래스를 구현하세요. 할 일 추가, 삭제, 완료 처리, 필터링(완료/미완료), 우선순위 설정 기능이 필요합니다."
            },
            "5": {
                "title": "커스텀 요구사항",
                "description": "직접 입력"
            }
        }