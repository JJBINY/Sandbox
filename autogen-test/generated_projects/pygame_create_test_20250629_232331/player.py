import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, PLAYER_IMAGE, PLAYER_SPEED, PLAYER_SIZE
from utils import load_image, logging

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # 플레이어 이미지 로드 및 크기 조절. 파일이 없으면 파란색 사각형 플레이스홀더 생성.
        self.original_image = load_image(PLAYER_IMAGE, scale=PLAYER_SIZE, default_size=PLAYER_SIZE, fill_color=(0, 0, 255)) 
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50) # 초기 위치
        self.speed = PLAYER_SPEED
        logging.info(f"Player initialized at {self.rect.center}")

    def update(self, keys):
        """키 입력에 따라 플레이어 위치를 업데이트합니다."""
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        if keys[pygame.K_UP]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.rect.y += self.speed

        # 화면 경계 유지
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
        
        logging.debug(f"Player position: {self.rect.topleft}")

    def draw(self, screen):
        """플레이어를 화면에 그립니다."""
        screen.blit(self.image, self.rect)