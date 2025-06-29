import pygame
import sys
import os
import random
from config import * # config.py의 모든 상수를 가져옴
from player import Player
from enemy import Enemy
from utils import load_image, init_sounds, play_sound, handle_error, logging # utils 모듈의 함수들을 가져옴

class Game:
    def __init__(self):
        # Pygame 및 믹서 초기화
        try:
            pygame.init()
            pygame.mixer.init() # 사운드 초기화
            init_sounds() # 유틸리티에서 사운드 로드
        except Exception as e:
            handle_error(f"Failed to initialize Pygame or Mixer: {e}", exit_game=True)

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        # 배경 이미지 로드 (파일이 없으면 초록색 사각형 플레이스홀더 생성)
        self.background = load_image(BACKGROUND_IMAGE, scale=(SCREEN_WIDTH, SCREEN_HEIGHT), fill_color=(0, 200, 0)) 
        if self.background.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
            handle_error("Background image loaded with incorrect size or failed.", exit_game=True)

        self.player = Player()
        self.enemies = pygame.sprite.Group() # 적들을 관리할 그룹
        self.all_sprites = pygame.sprite.Group() # 모든 스프라이트를 관리할 그룹 (그리기용)

        self.all_sprites.add(self.player)

        self.score = 0
        self.running = True
        self.game_over = False

        self.last_enemy_spawn_time = pygame.time.get_ticks()
        self.game_start_time = pygame.time.get_ticks() # 게임 시작 시간 기록 (점수 계산용)
        logging.info("Game initialized successfully.")

    def spawn_enemy(self):
        """새로운 적을 생성하고 그룹에 추가합니다."""
        enemy = Enemy()
        self.enemies.add(enemy)
        self.all_sprites.add(enemy)
        logging.debug(f"New enemy spawned at {enemy.rect.topleft}")

    def reset_game(self):
        """게임을 초기 상태로 재설정합니다."""
        logging.info("Resetting game...")
        self.player = Player()
        self.enemies.empty() # 모든 적 제거
        self.all_sprites.empty() # 모든 스프라이트 제거
        self.all_sprites.add(self.player) # 플레이어 다시 추가
        self.score = 0
        self.game_over = False
        self.last_enemy_spawn_time = pygame.time.get_ticks()
        self.game_start_time = pygame.time.get_ticks() # 게임 시작 시간 재설정
        logging.info("Game reset completed.")

    def handle_input(self):
        """이벤트 입력을 처리합니다."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                logging.info("Game quit event detected.")
            if event.type == pygame.KEYDOWN:
                if self.game_over:
                    if event.key == pygame.K_r: # 'R' 키로 게임 재시작
                        self.reset_game()
                        logging.info("Restarting game via 'R' key.")
                    elif event.key == pygame.K_q: # 'Q' 키로 게임 종료
                        self.running = False
                        logging.info("Exiting game via 'Q' key.")
                # 게임이 진행 중일 때 특정 키 입력에 대한 추가 로직은 여기에 추가할 수 있습니다.
                else: 
                    logging.debug(f"Key pressed: {pygame.key.name(event.key)}")

    def update(self):
        """게임 상태를 업데이트합니다."""
        if self.game_over:
            return

        # 플레이어 업데이트
        keys = pygame.key.get_pressed()
        self.player.update(keys)

        # 적 업데이트
        self.enemies.update()

        # 적 생성 로직: 일정 시간마다 새로운 적 생성
        current_time = pygame.time.get_ticks()
        if current_time - self.last_enemy_spawn_time > ENEMY_SPAWN_INTERVAL:
            self.spawn_enemy()
            self.last_enemy_spawn_time = current_time

        # 충돌 감지: 플레이어와 적 그룹 간의 충돌 검사
        # dokill=False: 충돌해도 적 스프라이트를 그룹에서 제거하지 않음 (게임 오버 조건이므로)
        collisions = pygame.sprite.spritecollide(self.player, self.enemies, False)
        if collisions:
            play_sound("game_over") # 게임 오버 사운드 재생
            self.game_over = True
            logging.info(f"Collision detected! Player hit by enemy. Game Over. Final Score: {self.score}")
        
        # 점수 업데이트 (시간 기반): 게임이 시작된 시간으로부터의 경과 시간으로 점수 계산
        self.score = (current_time - self.game_start_time) // 100 # 밀리초를 100으로 나눈 값
        logging.debug(f"Current score: {self.score}")

    def draw(self):
        """화면에 모든 요소를 그립니다."""
        self.screen.blit(self.background, (0, 0)) # 배경 그리기

        self.all_sprites.draw(self.screen) # 모든 스프라이트 그리기 (플레이어, 적 등)

        # 점수 표시
        font = pygame.font.Font(FONT_PATH, FONT_SIZE_SCORE)
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        if self.game_over:
            self.draw_game_over_screen()
        
        # 게임 시작 후 처음 3초 동안 안내 메시지 표시
        elif self.score == 0 and (pygame.time.get_ticks() - self.game_start_time < 3000):
            self.draw_start_instruction()

        pygame.display.flip() # 화면 업데이트

    def draw_game_over_screen(self):
        """게임 오버 화면을 그립니다."""
        # 화면 전체를 덮는 반투명 검은색 오버레이 생성
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) # RGBA (Alpha: 180 = 반투명)
        self.screen.blit(overlay, (0, 0))

        font_large = pygame.font.Font(FONT_PATH, FONT_SIZE_GAME_OVER)
        font_small = pygame.font.Font(FONT_PATH, FONT_SIZE_SCORE)
        font_instructions = pygame.font.Font(FONT_PATH, FONT_SIZE_INSTRUCTIONS)

        game_over_text = font_large.render("GAME OVER", True, RED)
        final_score_text = font_small.render(f"Final Score: {self.score}", True, WHITE)
        restart_text = font_instructions.render("Press 'R' to Restart or 'Q' to Quit", True, WHITE)

        # 텍스트 위치 계산 (중앙 정렬)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
        final_score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))

        self.screen.blit(game_over_text, game_over_rect)
        self.screen.blit(final_score_text, final_score_rect)
        self.screen.blit(restart_text, restart_rect)

    def draw_start_instruction(self):
        """게임 시작 시 안내 메시지를 그립니다."""
        font = pygame.font.Font(FONT_PATH, FONT_SIZE_INSTRUCTIONS)
        instruction_text = font.render("Use Arrow Keys to Move! Avoid Enemies!", True, WHITE)
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        
        # 안내 메시지 배경을 위한 반투명 사각형
        text_bg = pygame.Surface((instruction_rect.width + 40, instruction_rect.height + 20), pygame.SRCALPHA)
        text_bg.fill((0, 0, 0, 150)) # 반투명 검은색 배경
        text_bg_rect = text_bg.get_rect(center=instruction_rect.center) # 텍스트 중앙에 맞춤

        self.screen.blit(text_bg, text_bg_rect)
        self.screen.blit(instruction_text, instruction_rect)

    def run(self):
        """메인 게임 루프."""
        logging.info("Game loop started.")
        while self.running:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS) # 프레임 속도 제어
        
        logging.info("Game loop ended. Quitting Pygame.")
        pygame.quit() # Pygame 모듈 종료
        sys.exit() # 프로그램 종료

if __name__ == "__main__":
    game = Game()
    try:
        game.run()
    except Exception as e:
        # 게임 실행 중 예기치 않은 최상위 레벨의 에러 발생 시 처리
        handle_error(f"An unhandled error occurred during game execution: {e}", exit_game=True)