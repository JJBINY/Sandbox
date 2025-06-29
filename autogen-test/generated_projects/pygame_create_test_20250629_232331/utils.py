import logging
import os
import pygame
import sys # sys 모듈 추가: 깔끔한 종료를 위해 사용
from config import ASSETS_DIR, GAME_OVER_SOUND, COLLECT_SOUND, PLAYER_SIZE, ENEMY_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT

# 로깅 설정
# 로깅 레벨을 DEBUG로 설정하면 모든 상세 로그를 볼 수 있습니다.
# 실 서비스에서는 INFO 이상으로 설정하는 것이 일반적입니다.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_image(path, scale=None, default_size=(50, 50), fill_color=(255, 255, 255)):
    """이미지를 로드하고 Pygame 표면으로 변환합니다. 파일이 없거나 에러 발생 시 플레이스홀더를 반환합니다."""
    try:
        if not os.path.exists(path):
            logging.warning(f"Image file not found: {path}. Creating a placeholder.")
            # 파일이 없으면 기본 크기 또는 지정된 크기의 단색 표면을 생성
            placeholder = pygame.Surface(scale if scale else default_size)
            placeholder.fill(fill_color)
            return placeholder
            
        image = pygame.image.load(path).convert_alpha()
        if scale:
            image = pygame.transform.scale(image, scale)
        logging.debug(f"Image loaded: {path}")
        return image
    except pygame.error as e:
        logging.error(f"Error loading image {path}: {e}. Creating an error placeholder.")
        # Pygame 오류 발생 시 빨간색 표면을 생성
        placeholder = pygame.Surface(scale if scale else default_size)
        placeholder.fill((255, 0, 0)) # Red for error
        return placeholder
    except Exception as e:
        logging.error(f"Unexpected error in load_image {path}: {e}. Creating an error placeholder.")
        # 예상치 못한 다른 오류 발생 시 빨간색 표면을 생성
        placeholder = pygame.Surface(scale if scale else default_size)
        placeholder.fill((255, 0, 0)) # Red for error
        return placeholder

def load_sound(path):
    """사운드 파일을 로드합니다. 파일이 없거나 에러 발생 시 None을 반환합니다."""
    try:
        if not os.path.exists(path):
            logging.warning(f"Sound file not found: {path}. Skipping sound loading.")
            return None # 사운드가 없으면 None 반환
            
        sound = pygame.mixer.Sound(path)
        logging.debug(f"Sound loaded: {path}")
        return sound
    except pygame.error as e:
        logging.error(f"Error loading sound {path}: {e}. Skipping sound loading.")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in load_sound {path}: {e}. Skipping sound loading.")
        return None

# 사운드 로드 (전역적으로 한 번만 로드) - pygame.mixer.init() 이후에 호출되어야 함
_collected_sound = None # collect.wav가 현재 게임 로직에는 사용되지 않지만, 확장성을 위해 변수는 유지
_game_over_sound = None

def init_sounds():
    """게임 시작 시 Pygame 믹서 초기화 후 사운드를 로드합니다."""
    global _collected_sound, _game_over_sound
    # pygame.mixer.init()이 game.py에서 호출된 후 이 함수가 호출되어야 함
    _collected_sound = load_sound(COLLECT_SOUND)
    _game_over_sound = load_sound(GAME_OVER_SOUND)
    logging.info("Sounds initialized.")

def play_sound(sound_type):
    """지정된 타입의 사운드를 재생합니다."""
    sound_map = {
        "collect": _collected_sound,
        "game_over": _game_over_sound
    }
    sound = sound_map.get(sound_type)
    if sound:
        sound.play()
        logging.debug(f"Playing sound: {sound_type}")
    else:
        logging.debug(f"Sound '{sound_type}' not available to play or not loaded.")

def handle_error(msg, exit_game=True):
    """에러를 로깅하고 필요에 따라 게임을 종료합니다."""
    logging.critical(msg) # 치명적인 에러는 CRITICAL 레벨로 로깅
    if exit_game:
        pygame.quit()
        sys.exit() # sys.exit()를 사용하여 깔끔하게 종료