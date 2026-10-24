import pygame
import json
import time
from gesture import GestureController
import numpy as np

# 初始化Pygame
pygame.init()

# 窗口设置
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
FPS = 60

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)

# 音轨设置
TRACKS = {
    'left': {
        'positions': [220, 220, 220],
        'keys': [pygame.K_1, pygame.K_2, pygame.K_3],
        'key_display': ['1', '2', '3']
    },
    'right': {
        'positions': [540, 540, 540],
        'keys': [pygame.K_6, pygame.K_7, pygame.K_8],
        'key_display': ['6', '7', '8']
    }
}

# 音游核心参数
NOTE_SIZE = 80
PRE_SPAWN_SECONDS = 1.0
HIT_WINDOW = 0.15
JUDGE_LINE_Y = SCREEN_HEIGHT * 0.7

# 高斯模糊简易函数
def blur_surface(surf, amount):
    if amount <= 0:
        return surf
    scale = max(1, amount)
    w, h = surf.get_size()
    small = pygame.transform.smoothscale(surf, (w//scale, h//scale))
    return pygame.transform.smoothscale(small, (w, h))

class Note:
    def __init__(self, track, note_type, spawn_time, duration=0.0):
        self.track = track
        self.note_type = note_type
        self.spawn_time = spawn_time
        self.duration = duration
        self.end_time = spawn_time + duration
        self.hit = False
        self.missed = False
        self.is_holding = False

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Music Game")
        self.clock = pygame.time.Clock()
        self.hp_font = pygame.font.Font(None, 52)
        self.font = pygame.font.Font(None, 36)
        self.game_over_font = pygame.font.Font(None, 100)
        self.result_font = pygame.font.Font(None, 80)
        
        self.background = pygame.image.load("gamepic/background.png").convert()
        self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.blur_bg = blur_surface(self.background, 3)
        self.gameover_img = pygame.image.load("gamepic/gameover.png").convert_alpha()

        self.hit_img = pygame.image.load("gamepic/hit.png").convert_alpha()
        self.miss_img = pygame.image.load("gamepic/miss.png").convert_alpha()
        self.hit_img = pygame.transform.scale(self.hit_img, (100, 100))
        self.miss_img = pygame.transform.scale(self.miss_img, (100, 100))

        self.note_img_left1 = pygame.image.load("gamepic/lefthand1.png").convert_alpha()
        self.note_img_left2 = pygame.image.load("gamepic/lefthand2.png").convert_alpha()
        self.note_img_left3 = pygame.image.load("gamepic/lefthand3.png").convert_alpha()
        self.note_img_right1 = pygame.image.load("gamepic/righthand1.png").convert_alpha()
        self.note_img_right2 = pygame.image.load("gamepic/righthand2.png").convert_alpha()
        self.note_img_right3 = pygame.image.load("gamepic/righthand3.png").convert_alpha()

        self.note_img_left1 = pygame.transform.scale(self.note_img_left1, (NOTE_SIZE, NOTE_SIZE))
        self.note_img_left2 = pygame.transform.scale(self.note_img_left2, (NOTE_SIZE, NOTE_SIZE))
        self.note_img_left3 = pygame.transform.scale(self.note_img_left3, (NOTE_SIZE, NOTE_SIZE))
        self.note_img_right1 = pygame.transform.scale(self.note_img_right1, (NOTE_SIZE, NOTE_SIZE))
        self.note_img_right2 = pygame.transform.scale(self.note_img_right2, (NOTE_SIZE, NOTE_SIZE))
        self.note_img_right3 = pygame.transform.scale(self.note_img_right3, (NOTE_SIZE, NOTE_SIZE))
        self.gameover_img = pygame.transform.scale(self.gameover_img, (SCREEN_HEIGHT, SCREEN_HEIGHT))

        self.running = True
        self.game_started = False
        self.game_over = False
        self.game_clear = False
        self.end_time = 0
        self.start_time = 0
        self.health = 10
        
        self.notes = []
        self.original_notes = []
        self.active_notes = []
        self.feedback = []

        self.max_note_time = 0
        self.load_chart("chart.json")
        self.get_max_time()

        # 初始化音乐
        pygame.mixer.init()
        pygame.mixer.music.load("music/kiyomi.mp3")
    
    def draw_glow_text(self, text, font, x, y, color, glow_color=(255,255,255), glow_size=1, letter_spacing=2):
        current_x = x
        for char in text:
            for dx in range(-glow_size, glow_size+1):
                for dy in range(-glow_size, glow_size+1):
                    if dx == 0 and dy == 0: continue
                    surf = font.render(char, True, glow_color)
                    self.screen.blit(surf, (current_x + dx, y + dy))
            char_surf = font.render(char, True, color)
            self.screen.blit(char_surf, (current_x, y))
            current_x += char_surf.get_width() + letter_spacing

    def get_max_time(self):
        if self.original_notes:
            self.max_note_time = max(n.end_time for n in self.original_notes)
            self.true_end_time = self.max_note_time + HIT_WINDOW

    def load_chart(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for note_data in data['notes']:
                    note = Note(
                        track=note_data['track'],
                        note_type=note_data['type'],
                        spawn_time=note_data['time'],
                        duration=note_data.get('duration', 0.0)
                    )
                    self.original_notes.append(note)
                print(f"成功加载谱面，共{len(self.original_notes)}个音符")
        except Exception as e:
            print(f"加载谱面失败：{e}")
    
    def reset_game(self):
        self.notes = [Note(n.track, n.note_type, n.spawn_time, n.duration) for n in self.original_notes]
        self.active_notes = []
        self.feedback = []
        self.health = 10
        self.game_started = True
        self.game_over = False
        self.game_clear = False
        self.start_time = time.time()
        # 开始游戏时播放背景音乐
        pygame.mixer.music.play()
    
    def get_current_time(self):
        if not self.game_started:
            return 0
        # 获取背景音乐已经播放了多少秒
        pos_ms = pygame.mixer.music.get_pos()
        if pos_ms < 0:
            return 0
        return pos_ms / 1000.0
    
    def update_notes(self):
        current_time = self.get_current_time()

        while self.notes and self.notes[0].spawn_time - PRE_SPAWN_SECONDS <= current_time:
            self.active_notes.append(self.notes.pop(0))

        for note in self.active_notes[:]:
            if note.hit or note.missed: continue
            note_x = TRACKS[note.track]['positions'][note.note_type - 1]

            if note.duration > 0 and current_time >= note.end_time and not note.hit:
                if note.is_holding:
                    note.hit = True
                    self.feedback.append({'type':'hit','x': note_x,'y': JUDGE_LINE_Y - 40,'lifetime':40})
                else:
                    note.missed = True
                    self.health -= 1
                    self.feedback.append({'type':'miss','x': note_x,'y': JUDGE_LINE_Y - 40,'lifetime':40})
                    if self.health <= 0: self.trigger_game_over()

            if note.duration == 0:
                time_diff = current_time - note.spawn_time
                if time_diff > HIT_WINDOW:
                    note.missed = True
                    self.health -= 1
                    self.feedback.append({'type':'miss','x': note_x,'y': JUDGE_LINE_Y - 40,'lifetime':40})
                    if self.health <= 0: self.trigger_game_over()

            note_y = self.get_note_y_position(note, current_time)
            if note_y > SCREEN_HEIGHT + 200:
                try: self.active_notes.remove(note)
                except: pass

        if current_time >= self.true_end_time and self.health > 0:
            self.trigger_game_clear()
            return

    def get_note_y_position(self, note, time_point):
        progress = (time_point - (note.spawn_time - PRE_SPAWN_SECONDS)) / PRE_SPAWN_SECONDS
        progress = max(0.0, min(1.0, progress))
        return -50 + progress * (JUDGE_LINE_Y + 50)

    def handle_input(self, key):
        if not self.game_started or self.game_over or self.game_clear: return
        current_time = self.get_current_time()

        for track_name, track_info in TRACKS.items():
            if key in track_info['keys']:
                idx = track_info['keys'].index(key)
                note_type = idx + 1
                for note in self.active_notes:
                    if note.track == track_name and note.note_type == note_type and not note.hit and not note.missed:
                        note_x = TRACKS[note.track]['positions'][note.note_type - 1]
                        if note.duration == 0:
                            time_diff = abs(current_time - note.spawn_time)
                            if time_diff <= HIT_WINDOW:
                                note.hit = True
                                self.feedback.append({'type':'hit','x': note_x,'y': JUDGE_LINE_Y - 40,'lifetime':40})
                            else:
                                note.missed = True
                                self.health -= 1
                                self.feedback.append({'type':'miss','x': note_x,'y': JUDGE_LINE_Y - 40,'lifetime':40})
                                if self.health <= 0: self.trigger_game_over()
                        else:
                            if note.spawn_time - HIT_WINDOW <= current_time <= note.spawn_time + HIT_WINDOW:
                                note.is_holding = True
                        return

    def handle_release(self, key):
        if not self.game_started or self.game_over or self.game_clear: return
        current_time = self.get_current_time()
        for track_name, track_info in TRACKS.items():
            if key in track_info['keys']:
                idx = track_info['keys'].index(key)
                note_type = idx + 1
                for note in self.active_notes:
                    if note.track == track_name and note.note_type == note_type and note.duration > 0 and note.is_holding:
                        note_x = TRACKS[note.track]['positions'][note.note_type - 1]
                        if current_time < note.end_time - HIT_WINDOW:
                            note.missed = True
                            note.is_holding = False
                            self.health -= 1
                            self.feedback.append({'type':'miss','x': note_x,'y': JUDGE_LINE_Y - 40,'lifetime':40})
                            if self.health <= 0: self.trigger_game_over()
                        return

    def trigger_game_over(self):
        self.game_started = False
        self.game_over = True
        self.end_time = time.time()
        pygame.mixer.music.stop()
    
    def trigger_game_clear(self):
        self.game_started = False
        self.game_clear = True
        self.end_time = time.time()
        pygame.mixer.music.stop()
    
    def update_end_screen(self):
        now = time.time()
        if (self.game_over or self.game_clear) and now - self.end_time >= 3:
            self.game_over = False
            self.game_clear = False
    
    def update_feedback(self):
        for fb in self.feedback[:]:
            fb['lifetime'] -= 1
            fb['y'] -= 2
            if fb['lifetime'] <= 0:
                self.feedback.remove(fb)
    
    def draw_notes(self):
        current_time = self.get_current_time()
        for note in self.active_notes:
            if note.hit or note.missed: continue

            x = TRACKS[note.track]['positions'][note.note_type - 1] - NOTE_SIZE // 2

            if note.track == 'left':
                if note.note_type == 1: img = self.note_img_left1
                elif note.note_type == 2: img = self.note_img_left2
                else: img = self.note_img_left3
            else:
                if note.note_type == 1: img = self.note_img_right1
                elif note.note_type == 2: img = self.note_img_right2
                else: img = self.note_img_right3

            if note.duration > 0:
                head_y = self.get_note_y_position(note, current_time)
                tail_y = self.get_note_y_position(note, current_time - note.duration)
                pygame.draw.rect(self.screen, WHITE, (x, tail_y, NOTE_SIZE, head_y - tail_y))
                self.screen.blit(img, (x, head_y))
            else:
                head_y = self.get_note_y_position(note, current_time)
                self.screen.blit(img, (x, head_y))
            
            pygame.draw.rect(self.screen, BLACK, (x, head_y, NOTE_SIZE, NOTE_SIZE), 2)
    
    def draw_ui(self):
        pygame.draw.line(self.screen, WHITE, (50, JUDGE_LINE_Y), (750, JUDGE_LINE_Y), 3)
        self.draw_glow_text(f"HP: {self.health}", self.hp_font, 10, 10, WHITE, letter_spacing=5)

        for fb in self.feedback:
            img = self.hit_img if fb['type'] == 'hit' else self.miss_img
            r = img.get_rect(center=(fb['x'], fb['y']))
            self.screen.blit(img, r)
    
    def draw_game_over(self):
        img_rect = self.gameover_img.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(self.gameover_img, img_rect)
    
    def draw_game_clear(self):
        clear_text = self.result_font.render(f"HP: {self.health}", True, WHITE)
        rect = clear_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(clear_text, rect)
    
    # ========== 绘制右上角手势画面 ==========
    def draw_gesture_preview(self):
        frame = self.gesture.get_frame()
        if frame:
            self.screen.blit(frame, (SCREEN_WIDTH - 240, 0))

    def run(self):
        self.gesture = GestureController()
        self.last_L = 0
        self.last_R = 0

        while self.running:
            self.gesture.update()
            L = self.gesture.left
            R = self.gesture.right

            if L == 1 and self.last_L != 1: self.handle_input(pygame.K_1)
            if L == 2 and self.last_L != 2: self.handle_input(pygame.K_2)
            if L == 3 and self.last_L != 3: self.handle_input(pygame.K_3)
            if R == 1 and self.last_R != 1: self.handle_input(pygame.K_6)
            if R == 2 and self.last_R != 2: self.handle_input(pygame.K_7)
            if R == 3 and self.last_R != 3: self.handle_input(pygame.K_8)

            self.last_L = L
            self.last_R = R

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and not self.game_started and not self.game_over and not self.game_clear:
                        self.reset_game()
                elif event.type == pygame.KEYUP:
                    self.handle_release(event.key)
            
            if self.game_started:
                self.update_notes()
                self.update_feedback()
            
            self.update_end_screen()
            
            self.screen.blit(self.blur_bg, (0, 0))
            dark_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            dark_surface.set_alpha(80)
            dark_surface.fill((0, 0, 0))
            self.screen.blit(dark_surface, (0, 0))
            
            self.draw_notes()
            self.draw_ui()
            self.draw_gesture_preview()  # 显示手势小窗口
            
            if self.game_over: self.draw_game_over()
            if self.game_clear: self.draw_game_clear()
            
            if not self.game_started and not self.game_over and not self.game_clear:
                start_str = "Press SPACE to Start"
                total_width = 0
                for char in start_str:
                    w = self.font.size(char)[0]
                    total_width += w + 5
                x = SCREEN_WIDTH//2 - total_width//2
                y = SCREEN_HEIGHT - 50
                self.draw_glow_text(start_str, self.font, x, y, WHITE, letter_spacing=5)
                        
            pygame.display.flip()
            self.clock.tick(FPS)
        
        self.gesture.close()
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()