import pygame
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT, ENEMY_IMAGE, ENEMY_SPEED, ENEMY_SIZE
from utils import load_image, logging

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # 적 이미지 로드 및 크기 조절. 파일이 없으면 노란색 사각형 플레이스홀더 생성.
        self.original_image = load_image(ENEMY_IMAGE, scale=ENEMY_SIZE, default_size=ENEMY_SIZE, fill_color=(255, 255, 0)) 
        self.image = self.original_image
        self.rect = self.image.get_rect()
        
        self.spawn() # 초기 위치 설정

        self.speed = ENEMY_SPEED
        logging.debug(f"Enemy initialized at {self.rect.topleft}")

    def spawn(self):
        """적을 화면 위 랜덤 위치로 재배치합니다."""
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width) # 랜덤 x 위치
        self.rect.y = random.randint(-100, -40) # 화면 위에서 시작 (화면 밖에서 시작)

    def update(self):
        """적 위치를 아래로 업데이트합니다. 화면 아래로 벗어나면 재배치합니다."""
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.spawn() # 화면 밖으로 나가면 다시 스폰
            logging.debug(f"Enemy respawned at {self.rect.topleft}")

    def draw(self, screen):
        """적을 화면에 그립니다."""
        screen.blit(self.image, self.rect)