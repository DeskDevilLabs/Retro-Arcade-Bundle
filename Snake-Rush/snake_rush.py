import pygame
import sys
import random
from datetime import datetime
import json
import os
import platform

# Initialize pygame early for sound/mixer
pygame.init()
pygame.mixer.init()

# Determine the correct paths for data files
def get_data_path(filename):
    # If we're running as a PyInstaller bundle
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, filename)

def get_writable_path(filename):
    # Get appropriate writable location based on OS
    if platform.system() == "Windows":
        appdata = os.getenv('APPDATA')
        save_dir = os.path.join(appdata, 'SnakeRush')
    else:  # Linux/Mac
        home = os.path.expanduser("~")
        save_dir = os.path.join(home, '.snakerush')
    
    os.makedirs(save_dir, exist_ok=True)
    return os.path.join(save_dir, filename)

# Sound files
try:
    game_bg = pygame.mixer.Sound(get_data_path("snake_rush_bgm.wav"))
    game_bg.set_volume(0.6)
    game_over_sound = pygame.mixer.Sound(get_data_path("game_over.wav"))
    game_over_sound.set_volume(0.9)
    food_capture_sound = pygame.mixer.Sound(get_data_path("food_capture_sound.wav"))
    food_capture_sound.set_volume(0.7)
except:
    # Fallback if sound files aren't found
    class DummySound:
        def play(self): pass
        def stop(self): pass
        def set_volume(self, vol): pass
    
    game_bg = DummySound()
    game_over_sound = DummySound()
    food_capture_sound = DummySound()

# Leaderboard file path
LEADERBOARD_FILE = get_writable_path("snake_rush_leaderboard.json")

# Settings Variables
bgm_muted = False
sfx_muted = False
game_bg_playing = False
fullscreen = False

FPS = 60
clock = pygame.time.Clock()

# Calculate grid-aligned screen dimensions
BLOCK_SIZE = 30
info = pygame.display.Info()
GRID_WIDTH = info.current_w // BLOCK_SIZE
GRID_HEIGHT = info.current_h // BLOCK_SIZE
SCREEN_WIDTH = GRID_WIDTH * BLOCK_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * BLOCK_SIZE

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption('Snake Rush - Endless Mode')

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
LIGHT_GRAY = (150, 150, 150)
ORANGE = (255, 165, 0)

# Game settings
BASE_FPS = 8
MAX_FPS = 20
SPEED_INTERVAL = 5  # Increase speed every 5 points

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.font = pygame.font.Font(None, 36)
        
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)
        
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
        
    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

class ToggleButton(Button):
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=WHITE, is_on=False):
        super().__init__(x, y, width, height, text, color, hover_color, text_color)
        self.is_on = is_on
        
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)
        
        status = "ON" if self.is_on else "OFF"
        full_text = f"{self.text}: {status}"
        text_surf = self.font.render(full_text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def toggle(self):
        self.is_on = not self.is_on
        return self.is_on

class LeaderBoard:
    def __init__(self):
        self.scores = []
        self.load_scores()
    
    def reset_scores(self):
        self.scores = []
        self.save_scores()

    def load_scores(self):
        try:
            if os.path.exists(LEADERBOARD_FILE):
                with open(LEADERBOARD_FILE, 'r') as f:
                    self.scores = json.load(f)
                    # Ensure scores are sorted
                    self.scores.sort(key=lambda x: x['score'], reverse=True)
                    # Keep only top 10
                    self.scores = self.scores[:10]
            else:
                # Create file if it doesn't exist
                self.save_scores()
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading leaderboard: {e}")
            self.scores = []
    
    def save_scores(self):
        try:
            with open(LEADERBOARD_FILE, 'w') as f:
                json.dump(self.scores, f)
        except IOError as e:
            print(f"Error saving leaderboard: {e}")
    
    def add_score(self, score, length):
        if score > 0:
            new_entry = {
                'score': score,
                'length': length,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            
            # Add new score and sort
            self.scores.append(new_entry)
            self.scores.sort(key=lambda x: x['score'], reverse=True)
            
            # Keep only top 10
            if len(self.scores) > 10:
                self.scores = self.scores[:10]
            
            self.save_scores()
    
    def get_top_scores(self, limit=10):
        return self.scores[:limit]
    
    def get_high_score(self):
        return self.scores[0]['score'] if self.scores else 0
    
    def is_high_score(self, score):
        if not self.scores:
            return True
        return len(self.scores) < 10 or score > min(entry['score'] for entry in self.scores)

class Snake:
    def __init__(self):
        self.reset()
        
    def reset(self):
        grid_x = GRID_WIDTH // 2
        grid_y = GRID_HEIGHT // 2
        self.positions = [(grid_x * BLOCK_SIZE, grid_y * BLOCK_SIZE)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.length = 1
        self.score = 0
        self.color = GREEN
    
    def get_head_position(self):
        return self.positions[0]
    
    def update(self):
        self.direction = self.next_direction
        
        head_x, head_y = self.get_head_position()
        dir_x, dir_y = self.direction
        
        new_x = (head_x + dir_x * BLOCK_SIZE) % SCREEN_WIDTH
        new_y = (head_y + dir_y * BLOCK_SIZE) % SCREEN_HEIGHT
        
        if (new_x, new_y) in self.positions[1:]:
            return True  # Game over
            
        self.positions.insert(0, (new_x, new_y))
        if len(self.positions) > self.length:
            self.positions.pop()
        
        return False
    
    def change_direction(self, direction):
        if (direction[0] * -1, direction[1] * -1) != self.direction:
            self.next_direction = direction
    
    def draw(self, surface):
        for i, p in enumerate(self.positions):
            shade = 255 - (i * 3)
            shade = max(50, shade)
            color = (0, shade, 0)
            
            if i == 0:
                color = CYAN
            
            rect = pygame.Rect(p[0], p[1], BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, BLACK, rect, 1)

class Food:
    def __init__(self, food_type=1):
        self.type = food_type
        self.color = RED
        self.position = (0, 0)
        self.randomize_position()
        self.timer = 0
        self.active = True
        self.points = 1
        
        if self.type == 2:
            self.color = YELLOW
            self.timer = 150
            self.points = 2
        elif self.type == 3:
            self.color = BLUE
            self.timer = 100
            self.points = 3
        elif self.type == 4:
            self.color = PURPLE
            self.timer = 80
            self.points = 5
    
    def randomize_position(self):
        self.position = (
            random.randint(0, GRID_WIDTH - 1) * BLOCK_SIZE,
            random.randint(0, GRID_HEIGHT - 1) * BLOCK_SIZE
        )
    
    def update(self):
        if self.type > 1:
            self.timer -= 1
            if self.timer <= 0:
                self.active = False
        return self.active
    
    def draw(self, surface):
        if self.active:
            rect = pygame.Rect(self.position[0], self.position[1], BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(surface, self.color, rect)
            pygame.draw.rect(surface, BLACK, rect, 1)
            
            center_x = self.position[0] + BLOCK_SIZE//2
            center_y = self.position[1] + BLOCK_SIZE//2
            
            if self.type == 2:
                pygame.draw.circle(surface, BLACK, (center_x, center_y), BLOCK_SIZE//4)
            elif self.type == 3:
                points = [
                    (center_x, self.position[1] + 2),
                    (self.position[0] + BLOCK_SIZE - 2, center_y),
                    (center_x, self.position[1] + BLOCK_SIZE - 2),
                    (self.position[0] + 2, center_y)
                ]
                pygame.draw.polygon(surface, BLACK, points)
            elif self.type == 4:
                pygame.draw.line(surface, BLACK, 
                               (self.position[0] + 4, center_y), 
                               (self.position[0] + BLOCK_SIZE - 4, center_y), 3)
                pygame.draw.line(surface, BLACK, 
                               (center_x, self.position[1] + 4), 
                               (center_x, self.position[1] + BLOCK_SIZE - 4), 3)
            else:
                pygame.draw.circle(surface, BLACK, (center_x, center_y), BLOCK_SIZE//4)

class LogoScreen:
    def __init__(self):
        self.logos = []
        self.current_logo = 0
        self.logo_duration = 4000  # 4 seconds per logo set
        self.fade_duration = 1000  # 1 second fade in/out
        self.start_time = pygame.time.get_ticks()
        self.load_logos()
        self.fade_state = "in"  # "in", "hold", or "out"
        self.next_logo_time = self.start_time + self.fade_duration
        self.paired_logos = []  # Store pairs of logos to display together

        # Keys that should trigger skipping the logos
        self.skip_keys = {
            pygame.K_TAB, pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE
        }

    def load_logos(self):
        # Try to load multiple logo images
        logo_paths = [
            get_data_path("DD Lab1.png"),
            (get_data_path("logo1.png"), get_data_path("logo2.jpg")),
            get_data_path("snake_rush.png")
        ]
        
        for item in logo_paths:
            try:
                # Handle single logos
                if isinstance(item, str):
                    logo = pygame.image.load(item)
                    # Scale logo if needed
                    max_width = SCREEN_WIDTH * 0.9
                    max_height = SCREEN_HEIGHT * 0.8
                    logo_width, logo_height = logo.get_size()
                    scale = min(max_width / logo_width, max_height / logo_height)
                    if scale < 1:
                        logo = pygame.transform.scale(
                            logo, 
                            (int(logo_width * scale), int(logo_height * scale)))
                    self.logos.append([logo])  # Store as single-item list
                
                # Handle logo pairs
                elif isinstance(item, tuple) and len(item) == 2:
                    logo_pair = []
                    for path in item:
                        logo = pygame.image.load(path)
                        # Scale each logo to fit half the screen
                        max_width = SCREEN_WIDTH * 0.45
                        max_height = SCREEN_HEIGHT * 0.8
                        logo_width, logo_height = logo.get_size()
                        scale = min(max_width / logo_width, max_height / logo_height)
                        if scale < 1:
                            logo = pygame.transform.scale(
                                logo, 
                                (int(logo_width * scale), int(logo_height * scale)))
                        logo_pair.append(logo)
                    self.logos.append(logo_pair)
            
            except Exception as e:
                print(f"Error loading logo: {e}")
                pass
        
        # If no logos loaded, create text-based ones
        if not self.logos:
            font = pygame.font.Font(None, 72)
            for i in range(3):
                surf = pygame.Surface((400, 200), pygame.SRCALPHA)
                text = font.render(f"Desk Devil Labs", True, WHITE)
                text_rect = text.get_rect(center=(200, 100))
                surf.blit(text, text_rect)
                pygame.draw.rect(surf, WHITE, (0, 0, 400, 200), 2)
                self.logos.append([surf])
    
    def update(self):
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time

        # Check for key presses to skip
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                # Skip only if it's one of our allowed keys
                if event.key in self.skip_keys:
                    return True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Also allow skipping with mouse clicks
                return True
        
        # Update fade state
        if self.fade_state == "in" and current_time >= self.next_logo_time:
            self.fade_state = "hold"
            self.next_logo_time = current_time + (self.logo_duration - 2 * self.fade_duration)
        elif self.fade_state == "hold" and current_time >= self.next_logo_time:
            self.fade_state = "out"
            self.next_logo_time = current_time + self.fade_duration
        elif self.fade_state == "out" and current_time >= self.next_logo_time:
            self.current_logo += 1
            if self.current_logo >= len(self.logos):
                return True
            self.start_time = current_time
            self.fade_state = "in"
            self.next_logo_time = current_time + self.fade_duration
        
        return False
    
    def draw(self, surface):
        surface.fill(BLACK)
        
        if self.current_logo < len(self.logos):
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.start_time
            
            # Calculate alpha based on fade state
            if self.fade_state == "in":
                alpha = min(255, int(255 * (elapsed / self.fade_duration)))
            elif self.fade_state == "out":
                alpha = max(0, 255 - int(255 * ((current_time - (self.next_logo_time - self.fade_duration)) / self.fade_duration)))
            else:  # hold
                alpha = 255
            
            # Get current logo(s) - could be single or pair
            current_logos = self.logos[self.current_logo]
            
            # Create a composite surface if multiple logos
            if len(current_logos) > 1:
                # Calculate total width and max height
                total_width = sum(logo.get_width() for logo in current_logos) + 20 * (len(current_logos) - 1)
                max_height = max(logo.get_height() for logo in current_logos)
                
                # Create a temporary surface for the composite
                composite = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
                x_offset = 0
                for logo in current_logos:
                    composite.blit(logo, (x_offset, (max_height - logo.get_height()) // 2))
                    x_offset += logo.get_width() + 20
                
                # Apply alpha to the composite
                composite.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
                composite_rect = composite.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                surface.blit(composite, composite_rect)
            
            else:  # Single logo
                logo = current_logos[0]
                temp_surface = pygame.Surface((logo.get_width(), logo.get_height()), pygame.SRCALPHA)
                temp_surface.blit(logo, (0, 0))
                temp_surface.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
                logo_rect = temp_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                surface.blit(temp_surface, logo_rect)

def show_exit_credits():
    """Display exit credits sequence with scrolling credits and dedicated outro music"""
    # Stop any currently playing sounds
    pygame.mixer.stop()
    
    # Load outro music
    outro_music_path = get_data_path("outro_music.wav")
    try:
        outro_music = pygame.mixer.Sound(outro_music_path)
        outro_music.set_volume(0.7)
        outro_music.play(loops=-1)
    except:
        outro_music = None
    
    # Initialize parameters
    rolling_text_y = SCREEN_HEIGHT  # Start below screen
    rolling_text_speed = 2  # Pixels per frame
    total_duration = 14000  # 14 seconds total
    start_time = pygame.time.get_ticks()
    
    # Define credits content
    credit_font = pygame.font.Font(None, 32)
    credits = [
        "SNAKE RUSH",
        "",
        "Game Developed By",
        "Desk Devil Studios",
        "",
        "Programming",
        "Aryan Bhatt",
        "",
        "Artwork",
        "Aryan Bhatt",
        "",
        "Sound Design",
        "Aryan Bhatt in association with Pixabay",
        "",
        "Special Thanks To",
        "Python",
        "",
        "Pygame Library",
        "",
        "Pixabay for Sound Effects",
        "",
        "© 2025 Desk Devil Studios",
        "All Rights Reserved",
        ""
    ]
    
    # Keys that should trigger skipping the credits
    skip_keys = {
        pygame.K_TAB, pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE
    }
    
    # Main loop
    running = True
    while running:
        current_time = pygame.time.get_ticks()
        elapsed = current_time - start_time
        
        # Check if total duration has been reached
        if elapsed >= total_duration:
            if outro_music:
                outro_music.stop()
            return "quit"
        
        # Handle events (allow skipping only for specific keys)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if outro_music:
                    outro_music.stop()
                return "quit"
            elif event.type == pygame.KEYDOWN:
                # Skip only if it's one of our allowed keys
                if event.key in skip_keys:
                    if outro_music:
                        outro_music.stop()
                    return "quit"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Also allow skipping with mouse clicks
                if outro_music:
                    outro_music.stop()
                return "quit"
        
        # Update credits scrolling
        rolling_text_y -= rolling_text_speed
        if rolling_text_y < -2000:  # End when credits scroll past
            if outro_music:
                outro_music.stop()
            return "quit"
        
        # Draw everything
        screen.fill(BLACK)
        
        # Draw scrolling credits
        y_pos = rolling_text_y
        for credit in credits:
            if credit:
                text = credit_font.render(credit, True, WHITE)
                text_rect = text.get_rect(center=(SCREEN_WIDTH//2, y_pos))
                screen.blit(text, text_rect)
            y_pos += 40
        
        pygame.display.flip()
        clock.tick(FPS)
    
    # Clean up music if we exit early
    if outro_music:
        outro_music.stop()
    return 'quit'

class Game:
    def __init__(self):
        self.snake = Snake()
        self.foods = []
        self.game_over = False
        self.paused = False
        self.current_speed = BASE_FPS
        self.leaderboard = LeaderBoard()
        self.score_submitted = False
        self.title_screen = True
        self.show_leaderboard = False
        self.show_options = False
        
        # Pause menu buttons
        button_width = 200
        button_height = 50
        center_x = SCREEN_WIDTH // 2 - button_width // 2
        button_spacing = 70
        start_y = SCREEN_HEIGHT // 2 - 120
        
        self.resume_button = Button(center_x, start_y, button_width, button_height, 
                                   "Resume", GRAY, LIGHT_GRAY)
        self.leaderboard_button = Button(center_x, start_y + button_spacing, button_width, button_height, 
                                        "Leaderboard", BLUE, CYAN)
        self.restart_button = Button(center_x, start_y + button_spacing * 3, button_width, button_height, 
                                    "Restart", ORANGE, YELLOW)
        self.quit_button = Button(center_x, start_y + button_spacing * 4, button_width, button_height, 
                                 "Main Menu", RED, (255, 100, 100))
        
        # Leaderboard back button
        self.back_button = Button(center_x, SCREEN_HEIGHT - 100, button_width, button_height,
                                 "Back", GRAY, LIGHT_GRAY)
        self.reset_scores_button = Button(center_x + 220, SCREEN_HEIGHT - 100, 200, 50,
                                          "Reset Scores", RED, (255, 100, 100))
        
        
        # Title screen buttons
        self.start_button = Button(center_x, SCREEN_HEIGHT // 2 + 50, button_width, button_height,
                                 "Start Game", GREEN, (100, 255, 100))
        self.title_leaderboard_button = Button(center_x, SCREEN_HEIGHT // 2 + 50 + button_spacing, 
                                            button_width, button_height, "Leaderboard", BLUE, CYAN)
        self.title_quit_button = Button(center_x, SCREEN_HEIGHT // 2 + 50 + button_spacing * 3,
                                      button_width, button_height, "Quit", RED, (255, 100, 100))
        
        self.spawn_food()
        self.spawn_food()

        # When starting the game:
        global game_bg_playing
        if not game_bg_playing:
            game_bg.play(-1)
            game_bg_playing = True
            # Apply mute state
            if bgm_muted:
                game_bg.set_volume(0.0)
            else:
                game_bg.set_volume(0.3)
    
    def get_food_spawn_chances(self):
        score = self.snake.score
        
        if score < 10:
            return [85, 15, 0, 0]
        elif score < 25:
            return [70, 25, 5, 0]
        elif score < 50:
            return [60, 25, 12, 3]
        else:
            return [50, 30, 15, 5]
    
    def spawn_food(self):
        chances = self.get_food_spawn_chances()
        rand = random.randint(1, 100)
        
        if rand <= chances[0]:
            food_type = 1
        elif rand <= chances[0] + chances[1]:
            food_type = 2
        elif rand <= chances[0] + chances[1] + chances[2]:
            food_type = 3
        else:
            food_type = 4
        
        new_food = Food(food_type)
        
        while new_food.position in [pos for pos in self.snake.positions]:
            new_food.randomize_position()
        
        self.foods.append(new_food)
    
    def update_speed(self):
        speed_increase = self.snake.score // SPEED_INTERVAL
        self.current_speed = min(BASE_FPS + speed_increase, MAX_FPS)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "show_credits" 
            
            elif event.type == pygame.VIDEORESIZE:
                if not fullscreen:
                    global SCREEN_WIDTH, SCREEN_HEIGHT, screen
                    SCREEN_WIDTH, SCREEN_HEIGHT = event.size
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    
            
            elif event.type == pygame.KEYDOWN:
                if self.title_screen:
                    if (event.key == pygame.K_RETURN or event.key == pygame.K_SPACE) and not (self.show_leaderboard):
                        self.title_screen = False
                    elif event.key == pygame.K_ESCAPE:
                        if self.show_leaderboard:
                            self.show_leaderboard = False
                            self.show_options = False
                elif self.show_leaderboard:
                    if event.key == pygame.K_ESCAPE:
                        self.show_leaderboard = False
                        self.show_options = False
                elif self.paused:
                    if event.key == pygame.K_ESCAPE:
                        self.paused = False
                elif not self.game_over and not self.paused:
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.snake.change_direction((0, -1))
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.snake.change_direction((0, 1))
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.snake.change_direction((-1, 0))
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.snake.change_direction((1, 0))
                    elif event.key == pygame.K_ESCAPE:
                        self.paused = True
                    elif event.key == pygame.K_p:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        self.restart_game()
                elif self.game_over:
                    if event.key == pygame.K_r:
                        self.restart_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.__init__()
                        self.title_screen = True
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                if self.title_screen:
                    if not (self.show_leaderboard):
                        if self.start_button.is_clicked(mouse_pos, event):
                            self.title_screen = False
                        elif self.title_leaderboard_button.is_clicked(mouse_pos, event):
                            self.show_leaderboard = True
                            self.show_options = False
                        elif self.title_quit_button.is_clicked(mouse_pos, event):
                            return "show_credits"
                    elif self.show_leaderboard and self.back_button.is_clicked(mouse_pos, event):
                        self.show_leaderboard = False
                    elif self.show_leaderboard and self.reset_scores_button.is_clicked(mouse_pos, event):
                        # Add confirmation dialog
                        confirm = self.show_confirmation_dialog("Reset all scores?")
                        if confirm:
                            self.leaderboard.reset_scores()
                            # Force a refresh of the leaderboard display
                            self.show_leaderboard = True  # This will make it redraw
                
                elif self.paused and not (self.show_leaderboard):
                    if self.resume_button.is_clicked(mouse_pos, event):
                        self.paused = False
                    elif self.leaderboard_button.is_clicked(mouse_pos, event):
                        self.show_leaderboard = True
                        self.show_options = False
                    elif self.restart_button.is_clicked(mouse_pos, event):
                        self.restart_game()
                        self.paused = False
                    elif self.quit_button.is_clicked(mouse_pos, event):
                        self.__init__()
                        self.title_screen = True
                        self.paused = False
                
                elif self.show_leaderboard and self.back_button.is_clicked(mouse_pos, event):
                    self.show_leaderboard = False
                
                elif self.reset_scores_button.is_clicked(mouse_pos, event):
                        # Add confirmation dialog
                        confirm = self.show_confirmation_dialog("Reset all scores?")
                        if confirm:
                            self.leaderboard.reset_scores()
                
                elif self.game_over:
                    restart_text_rect = pygame.Rect(
                        SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 60, 300, 30
                    )
                    if restart_text_rect.collidepoint(mouse_pos):
                        self.restart_game()
        
        return True

    def show_confirmation_dialog(self, message):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 36)
        text = font.render(message, True, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
        screen.blit(text, text_rect)
        
        yes_button = Button(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 20, 120, 50, 
                          "Yes", RED, (255, 100, 100))
        no_button = Button(SCREEN_WIDTH//2 + 30, SCREEN_HEIGHT//2 + 20, 120, 50,
                         "No", GRAY, LIGHT_GRAY)
        
        pygame.display.flip()
        
        waiting = True
        while waiting:
            mouse_pos = pygame.mouse.get_pos()
            yes_button.check_hover(mouse_pos)
            no_button.check_hover(mouse_pos)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "show_credits" 
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if yes_button.is_clicked(mouse_pos, event):
                        return True
                    elif no_button.is_clicked(mouse_pos, event):
                        return False
            
            yes_button.draw(screen)
            no_button.draw(screen)
            pygame.display.flip()
            clock.tick(60)
        
        return False
    
    def update(self):
        if self.title_screen or self.game_over or self.paused or self.show_leaderboard:
            if self.game_over and not self.score_submitted:
                if self.leaderboard.is_high_score(self.snake.score):
                    self.leaderboard.add_score(self.snake.score, self.snake.length)
                self.score_submitted = True
            return
        
        game_over = self.snake.update()
        global game_bg_playing 
        if game_over:
            self.game_over = True
            game_bg.stop()
            game_bg_playing = False
            if not sfx_muted:
                game_over_sound.play()
            return
        
        for food in self.foods[:]:
            if not food.update():
                self.foods.remove(food)
        
        head = self.snake.get_head_position()
        head_rect = pygame.Rect(head[0], head[1], BLOCK_SIZE, BLOCK_SIZE)
        
        for food in self.foods[:]:
            food_rect = pygame.Rect(food.position[0], food.position[1], BLOCK_SIZE, BLOCK_SIZE)
            if head_rect.colliderect(food_rect) and food.active:
                self.foods.remove(food)

                if not sfx_muted:
                    food_capture_sound.play()
                
                self.snake.score += food.points
                
                if food.type == 1:
                    self.snake.length += 1
                elif food.type == 2:
                    self.snake.length += 2
                elif food.type == 3:
                    self.snake.length += 3
                elif food.type == 4:
                    self.snake.length += 4
                
                self.spawn_food()
                self.update_speed()
        
        min_foods = min(2 + (self.snake.score // 15), 4)
        while len(self.foods) < min_foods:
            self.spawn_food()
    
    def restart_game(self):
        self.snake.reset()
        self.foods = []
        self.game_over = False
        self.paused = False
        self.score_submitted = False
        self.current_speed = BASE_FPS
        
        self.spawn_food()
        self.spawn_food()

        # When restarting the game:
        global game_bg_playing 
        if not game_bg_playing:
            game_bg.play(-1)
            game_bg_playing = True
            # Restore mute state
            if bgm_muted:
                game_bg.set_volume(0.0)
            else:
                game_bg.set_volume(0.3)
    
    def draw_title_screen(self):
        screen.fill(BLACK)
        
        title_font = pygame.font.Font(None, 72)
        title_text = title_font.render("SNAKE RUSH", True, GREEN)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
        screen.blit(title_text, title_rect)
        
        # Draw a sample snake
        snake_length = 10
        for i in range(snake_length):
            x = SCREEN_WIDTH // 3 + i * BLOCK_SIZE
            y = SCREEN_HEIGHT // 2
            color = (0, 255 - (i * 20), 0)
            if i == 0:
                color = CYAN
            pygame.draw.rect(screen, color, (x, y, BLOCK_SIZE, BLOCK_SIZE))
            pygame.draw.rect(screen, BLACK, (x, y, BLOCK_SIZE, BLOCK_SIZE), 1)
        
        # Draw sample food
        pygame.draw.rect(screen, RED, (SCREEN_WIDTH // 3 + snake_length * BLOCK_SIZE + 20, 
                                     SCREEN_HEIGHT // 2, BLOCK_SIZE, BLOCK_SIZE))
        
        mouse_pos = pygame.mouse.get_pos()
        self.start_button.check_hover(mouse_pos)
        self.title_leaderboard_button.check_hover(mouse_pos)
        self.title_quit_button.check_hover(mouse_pos)
        
        if not (self.show_leaderboard):
            self.start_button.draw(screen)
            self.title_leaderboard_button.draw(screen)
            self.title_quit_button.draw(screen)
        
        # Show high score on title screen
        high_score = self.leaderboard.get_high_score()
        if high_score > 0:
            hs_font = pygame.font.Font(None, 36)
            hs_text = hs_font.render(f"High Score: {high_score}", True, YELLOW)
            hs_rect = hs_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3 + 50))
            screen.blit(hs_text, hs_rect)
        
        controls_font = pygame.font.Font(None, 24)
        controls = [
            "Controls:",
            "WASD / Arrow Keys to Move",
            "P to Pause",
            "ESC for Menu",
            "R to Restart"
        ]
        for i, control in enumerate(controls):
            text = controls_font.render(control, True, WHITE)
            screen.blit(text, (50, SCREEN_HEIGHT - 150 + i * 25))
    
    def draw_pause_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        big_font = pygame.font.Font(None, 72)
        title = big_font.render("GAME PAUSED", True, WHITE)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 200)))
        
        mouse_pos = pygame.mouse.get_pos()
        self.resume_button.check_hover(mouse_pos)
        self.leaderboard_button.check_hover(mouse_pos)
        self.restart_button.check_hover(mouse_pos)
        self.quit_button.check_hover(mouse_pos)
        
        self.resume_button.draw(screen)
        self.leaderboard_button.draw(screen)
        self.restart_button.draw(screen)
        self.quit_button.draw(screen)
    
    
    def draw_leaderboard(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))
        
        big_font = pygame.font.Font(None, 72)
        title = big_font.render("LEADERBOARD", True, CYAN)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, 100)))
        
        header_font = pygame.font.Font(None, 48)
        rank_header = header_font.render("RANK", True, YELLOW)
        score_header = header_font.render("SCORE", True, YELLOW)
        length_header = header_font.render("LENGTH", True, YELLOW)
        date_header = header_font.render("DATE", True, YELLOW)
        
        header_y = 180
        screen.blit(rank_header, (200, header_y))
        screen.blit(score_header, (350, header_y))
        screen.blit(length_header, (550, header_y))
        screen.blit(date_header, (700, header_y))
        
        pygame.draw.line(screen, WHITE, (150, header_y + 50), (SCREEN_WIDTH - 150, header_y + 50), 2)
        
        score_font = pygame.font.Font(None, 36)
        scores = self.leaderboard.get_top_scores()
        
        if not scores:
            no_scores_text = score_font.render("No scores yet! Be the first to play!", True, WHITE)
            screen.blit(no_scores_text, no_scores_text.get_rect(center=(SCREEN_WIDTH//2, 300)))
        else:
            for i, entry in enumerate(scores):
                y_pos = 250 + i * 40
                
                color = GREEN if (self.game_over and entry['score'] == self.snake.score and 
                                entry['length'] == self.snake.length) else WHITE
                
                rank_text = score_font.render(f"{i + 1}.", True, color)
                score_text = score_font.render(f"{entry['score']:,}", True, color)
                length_text = score_font.render(f"{entry['length']}", True, color)
                date_text = score_font.render(entry['date'][:10], True, color)
                
                screen.blit(rank_text, (200, y_pos))
                screen.blit(score_text, (350, y_pos))
                screen.blit(length_text, (550, y_pos))
                screen.blit(date_text, (700, y_pos))
        
        mouse_pos = pygame.mouse.get_pos()
        
        self.back_button.check_hover(mouse_pos)
        self.reset_scores_button.check_hover(mouse_pos)
        
        self.back_button.draw(screen)
        self.reset_scores_button.draw(screen)
    
    def draw(self, screen):
        screen.fill(BLACK)
        
        if not (self.title_screen or self.show_leaderboard or self.paused or self.game_over):
            # Draw grid
            for x in range(0, SCREEN_WIDTH, BLOCK_SIZE):
                pygame.draw.line(screen, (20, 20, 20), (x, 0), (x, SCREEN_HEIGHT))
            for y in range(0, SCREEN_HEIGHT, BLOCK_SIZE):
                pygame.draw.line(screen, (20, 20, 20), (0, y), (SCREEN_WIDTH, y))
            
            # Draw game elements
            for food in self.foods:
                food.draw(screen)
            self.snake.draw(screen)
            
            # Draw HUD
            font = pygame.font.Font(None, 36)
            score_text = font.render(f'Score: {self.snake.score}', True, WHITE)
            length_text = font.render(f'Length: {self.snake.length}', True, WHITE)
            speed_text = font.render(f'Speed: {self.current_speed}', True, WHITE)
            high_score = self.leaderboard.get_high_score()
            high_score_text = font.render(f'High Score: {high_score}', True, YELLOW)
            
            screen.blit(score_text, (10, 10))
            screen.blit(length_text, (10, 50))
            screen.blit(speed_text, (10, 90))
            screen.blit(high_score_text, (10, 130))
            
            legend_font = pygame.font.Font(None, 20)
            legends = [
                ("Red: +1 point", RED),
                ("Yellow: +2 points", YELLOW),
                ("Blue: +3 points", BLUE),
                ("Purple: +5 points", PURPLE)
            ]
            for i, (text, color) in enumerate(legends):
                legend_text = legend_font.render(text, True, color)
                screen.blit(legend_text, (10, 180 + i * 22))
            
            controls_font = pygame.font.Font(None, 24)
            controls = [
                "WASD: Move",
                "P: Pause",
                "ESC: Menu",
                "R: Restart"
            ]
            for i, control in enumerate(controls):
                text = controls_font.render(control, True, WHITE)
                screen.blit(text, (SCREEN_WIDTH - 180, 10 + i * 25))
        
        if self.title_screen:
            self.draw_title_screen()
        
        if self.show_leaderboard:
            self.draw_leaderboard()
        
        if self.paused and not (self.show_leaderboard):
            self.draw_pause_menu()
        
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            
            big_font = pygame.font.Font(None, 72)
            small_font = pygame.font.Font(None, 36)
            
            game_over_text = big_font.render('GAME OVER', True, RED)
            score_text = small_font.render(f'Final Score: {self.snake.score}', True, WHITE)
            length_text = small_font.render(f'Final Length: {self.snake.length}', True, WHITE)
            
            restart_text = small_font.render('Press R to Restart or Click Here', True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70))
            screen.blit(restart_text, restart_rect)
            
            quit_text = small_font.render('Press ESC for Main Menu', True, WHITE)
            quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 110))
            screen.blit(quit_text, quit_rect)
            
            screen.blit(game_over_text, game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40)))
            screen.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))
            screen.blit(length_text, length_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30)))

def main():
    # Initialize pygame and screen
    pygame.init()
    global screen, SCREEN_WIDTH, SCREEN_HEIGHT, BLOCK_SIZE, GRID_WIDTH, GRID_HEIGHT
    
    # Calculate grid-aligned screen dimensions
    BLOCK_SIZE = 30
    GRID_WIDTH = pygame.display.Info().current_w // BLOCK_SIZE
    GRID_HEIGHT = pygame.display.Info().current_h // BLOCK_SIZE
    SCREEN_WIDTH = GRID_WIDTH * BLOCK_SIZE
    SCREEN_HEIGHT = GRID_HEIGHT * BLOCK_SIZE

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption('Snake Rush - Endless Mode')

    # Show logo screen first
    logo_screen = LogoScreen()
    logo_done = False
    
    # Logo screen loop
    while not logo_done:
        result = logo_screen.update()
        if result == "quit":  # If user quits during logo screen
            pygame.quit()
            sys.exit()
        elif result:  # If logo sequence is done or skipped
            logo_done = True
        
        logo_screen.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)
    
    # Now proceed to main game
    game = Game()
    running = True
    
    while running:
        result = game.handle_events()
        if result == "show_credits":  # Handle quit from game
            running = False
        elif result == "quit":  # Handle immediate quit
            pygame.quit()
            sys.exit()
        elif not result:  # Handle other cases
            running = False
            
        game.update()
        game.draw(screen)
        pygame.display.flip()
        clock.tick(game.current_speed)
        
    # When quitting the game, show exit credits
    result = show_exit_credits()
    if result == "quit":
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    main()