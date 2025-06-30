"""
TDD 바이브코딩 시스템 설정 관리
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class AppConfig:
    """환경 설정 관리"""

    # API 설정
    GEMINI_API_KEY: Optional[str] = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL: str = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    GEMINI_BASE_URL: str = os.getenv('GEMINI_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/openai/')

    # 프로젝트 설정
    MAX_ITERATIONS: int = int(os.getenv('MAX_TDD_ITERATIONS', '3'))
    TIMEOUT_SECONDS: int = int(os.getenv('TEST_TIMEOUT', '30'))

    # 디렉토리 설정
    GENERATED_PROJECTS_DIR: str = os.getenv('GENERATED_PROJECTS_DIR', 'generated_projects')
    PROMPTS_DIR: str = os.getenv('PROMPTS_DIR', 'agents/prompts')

    @classmethod
    def validate_config(cls) -> bool:
        """설정 유효성 검사"""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
        print("✅ 설정이 유효합니다.")
        return True

    @classmethod
    def get_model_client_config(cls) -> dict:
        """모델 클라이언트 설정 반환"""
        return {
            'model': cls.GEMINI_MODEL,
            'api_key': cls.GEMINI_API_KEY,
            'base_url': cls.GEMINI_BASE_URL
        }