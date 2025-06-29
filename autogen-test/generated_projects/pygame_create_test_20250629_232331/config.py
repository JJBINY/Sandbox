import os

# 게임 설정
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TITLE = "Simple Pygame Game"
FPS = 60

# 색상
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# 플레이어 설정
PLAYER_SPEED = 5
PLAYER_SIZE = (50, 50) # 플레이어 이미지 크기

# 적 설정
ENEMY_SPEED = 2
ENEMY_SIZE = (40, 40) # 적 이미지 크기
ENEMY_SPAWN_INTERVAL = 3000 # milliseconds

# 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# 이미지 파일
PLAYER_IMAGE = os.path.join(ASSETS_DIR, "player.png")
ENEMY_IMAGE = os.path.join(ASSETS_DIR, "enemy.png")
BACKGROUND_IMAGE = os.path.join(ASSETS_DIR, "background.png")

# 사운드 파일
COLLECT_SOUND = os.path.join(ASSETS_DIR, "collect.wav") # 현재 게임 로직에서는 사용되지 않음
GAME_OVER_SOUND = os.path.join(ASSETS_DIR, "game_over.wav")

# 폰트
FONT_PATH = None # 기본 폰트 사용 시 None, 특정 폰트 사용 시 경로 지정
FONT_SIZE_SCORE = 36
FONT_SIZE_GAME_OVER = 48
FONT_SIZE_INSTRUCTIONS = 24 # 안내 메시지 폰트 크기