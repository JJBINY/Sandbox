# config.py - 간소화된 설정 관리
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """환경 설정 관리 클래스"""
    
    # Gemini API 설정 (OpenAI 호환 API 사용)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    GEMINI_TEMPERATURE = float(os.getenv('GEMINI_TEMPERATURE', '0.7'))
    GEMINI_BASE_URL = os.getenv('GEMINI_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/openai/')
    
    @classmethod
    def validate_config(cls):
        """필수 설정 값들이 있는지 확인"""
        if not cls.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY가 설정되지 않았습니다. "
                ".env 파일을 확인해주세요."
            )
        
        print("✅ 설정이 유효합니다.")
        print(f"📱 사용 모델: {cls.GEMINI_MODEL}")
        print(f"🌐 Base URL: {cls.GEMINI_BASE_URL}")
        return True

# 설정 검증
if __name__ == "__main__":
    Config.validate_config()