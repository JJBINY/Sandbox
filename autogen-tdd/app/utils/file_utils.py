"""
파일 관련 유틸리티 함수들
"""
import os
import logging
from pathlib import Path
from typing import Optional

# 로거 설정
logger = logging.getLogger(__name__)

class FileReadError(Exception):
    """파일 읽기 관련 커스텀 예외"""
    pass

def read_message_file(file_path: str) -> str:
    """
    메시지 파일 읽기

    Args:
        file_path (str): 읽을 파일의 상대 경로

    Returns:
        str: 파일 내용

    Raises:
        FileReadError: 파일을 찾을 수 없거나 읽을 수 없는 경우
        PermissionError: 파일 접근 권한이 없는 경우
        UnicodeDecodeError: 파일 인코딩 오류가 있는 경우
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(current_dir, '..', file_path)

        # 절대 경로로 변환하여 정규화
        normalized_path = os.path.abspath(full_path)

        # 파일 존재 여부 확인
        if not os.path.exists(normalized_path):
            error_msg = f"파일을 찾을 수 없습니다: {normalized_path}"
            logger.error(error_msg)
            raise FileReadError(error_msg)

        # 파일인지 확인 (디렉토리가 아닌지)
        if not os.path.isfile(normalized_path):
            error_msg = f"지정된 경로가 파일이 아닙니다: {normalized_path}"
            logger.error(error_msg)
            raise FileReadError(error_msg)

        # 파일 읽기
        with open(normalized_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 성공 로그
        logger.info(f"파일 읽기 성공: {normalized_path} (크기: {len(content)}자)")

        return content

    except FileNotFoundError as e:
        error_msg = f"파일을 찾을 수 없습니다: {file_path} -> {normalized_path if 'normalized_path' in locals() else 'Unknown'}"
        logger.error(error_msg)
        raise FileReadError(error_msg) from e

    except PermissionError as e:
        error_msg = f"파일 접근 권한이 없습니다: {normalized_path if 'normalized_path' in locals() else file_path}"
        logger.error(error_msg)
        raise PermissionError(error_msg) from e

    except UnicodeDecodeError as e:
        error_msg = f"파일 인코딩 오류 (UTF-8이 아님): {normalized_path if 'normalized_path' in locals() else file_path}"
        logger.error(error_msg)
        raise UnicodeDecodeError(e.encoding, e.object, e.start, e.end, error_msg) from e

    except Exception as e:
        error_msg = f"예상치 못한 오류 발생: {file_path} - {str(e)}"
        logger.error(error_msg)
        raise FileReadError(error_msg) from e

def read_message_file_safe(file_path: str, default_message: Optional[str] = None) -> str:
    """
    메시지 파일을 안전하게 읽기 (기존 동작 호환용)

    Args:
        file_path (str): 읽을 파일의 상대 경로
        default_message (str, optional): 파일을 읽을 수 없을 때 반환할 기본 메시지

    Returns:
        str: 파일 내용 또는 기본 메시지
    """
    if default_message is None:
        default_message = "You are a helpful AI assistant specialized in Test-Driven Development."

    try:
        return read_message_file(file_path)
    except (FileReadError, PermissionError, UnicodeDecodeError) as e:
        logger.warning(f"파일 읽기 실패, 기본 메시지 사용: {e}")
        return default_message

def setup_file_logging(log_level: int = logging.INFO) -> None:
    """
    파일 유틸리티용 로깅 설정

    Args:
        log_level (int): 로깅 레벨 (기본값: INFO)
    """
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # 콘솔 출력
            logging.FileHandler('file_utils.log', encoding='utf-8')  # 파일 출력
        ]
    )
    logger.setLevel(log_level)

# 사용 예시
if __name__ == "__main__":
    # 로깅 설정
    setup_file_logging(logging.DEBUG)

    try:
        # 정상적인 파일 읽기 테스트
        content = read_message_file("prompts/test_designer.txt")
        print(f"파일 내용 길이: {len(content)}")

    except FileReadError as e:
        print(f"파일 읽기 오류: {e}")

    except Exception as e:
        print(f"예상치 못한 오류: {e}")

    # 안전한 읽기 테스트 (호환성 유지)
    safe_content = read_message_file_safe("non_existent_file.txt")
    print(f"안전한 읽기 결과: {safe_content[:100]}...")