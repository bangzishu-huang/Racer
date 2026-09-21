import pygame
import time 
import math
from utils import scale_image, blit_rotate_center
import asyncio

pygame.init()

GRASS = scale_image(pygame.image.load('./images/grass.jpg'), 2.5)
TRACK = scale_image(pygame.image.load('./images/track.png'), 0.9)
TRACK_BORDER = scale_image(pygame.image.load('./images/track-border.png'), 0.9)
TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)
FINISH = pygame.image.load('./images/finish.png')
FINISH_MASK = pygame.mask.from_surface(FINISH)
FINISH_POSITION = (130, 250)
RED_CAR = scale_image(pygame.image.load('./images/red-car.png'),  0.55)
GREEN_CAR = scale_image(pygame.image.load('./images/green-car.png'), 0.55)

WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()

MAIN_FONT = pygame.font.SysFont("comicsans", 44)
LAP_FONT = pygame.font.SysFont("comicsans", 20)
COUNTDOWN_FONT = pygame.font.SysFont("comicsans", 120)

FPS = 60
TOTAL_LAPS = 1
LAP_COOLDOWN_FRAMES = 30
PATH = [(176, 137), (148, 77), (65, 106), (61, 200), (60, 316), (59, 409), (71, 487), (125, 550), (179, 603), (241, 655), (310, 718), (382, 723), (409, 638), (420, 518), (492, 480), (590, 531), (596, 632), (624, 715), (707, 730), (741, 639), (738, 543), (737, 457), (725, 383), (619, 373), (533, 375), (447, 372), (392, 319), (425, 257), (500, 250), (571, 250), (641, 247), (717, 244), (746, 173), (723, 85), (640, 74), (536, 72), (445, 71), (364, 67), (291, 93), (284, 185), (284, 252), (281, 327), (272, 394), (218, 408), (163, 361), (152, 260), (152, 210)]

class AbstractCar():
    def __init__(self, max_vel, rotation_vel):
        self.max_vel = max_vel
        self.vel = 0
        self.rotation_vel = rotation_vel
        self.angle = 0
        self.x, self.y = self.START_POS
        self.acceleration = 0.1
        self.laps = 0
        self.lap_cooldown = 0
        self.lap_start_time = 0

    def rotate(self, left = False, right = False):
        if left:
            self.angle += self.rotation_vel
        elif right:
            self.angle -= self.rotation_vel

    def draw(self, win):
        blit_rotate_center(win, self.IMG, (self.x, self.y), self.angle)

    def move_forward(self):
        self.vel = min(self.vel + self.acceleration, self.max_vel)
        self.move()

    def move_backward(self):
        self.vel = max(self.vel - self.acceleration, self.max_vel / 2)
        self.move()

    def move(self):
        rads = math.radians(self.angle)
        vertical = math.cos(rads) * self.vel
        horizontal = math.sin(rads) * self.vel
        self.y -= vertical
        self.x -= horizontal

    def collide(self, mask, x=0, y=0):
        car_mask = pygame.mask.from_surface(self.IMG)
        offset = (int(self.x - x), int(self.y - y))
        poi = mask.overlap(car_mask, offset)
        return poi

    def reset(self):
        self.x, self.y = self.START_POS
        self.angle = 0
        self.vel = 0

class PlayerCar(AbstractCar):
    IMG = RED_CAR
    START_POS = (180, 200)
    bounce_factor = 1.0

    def reduce_speed(self):
        self.vel = max(self.vel - self.acceleration / 2, 0)
        self.move()

    def bounce(self):
        self.vel = max(-self.max_vel, min(self.max_vel, -self.vel * self.bounce_factor))
        self.move()

class ComputerCar(AbstractCar):
    IMG = GREEN_CAR
    START_POS = (150, 200)

    def __init__(self, max_vel, rotation_vel, path=None):
        super().__init__(max_vel, rotation_vel)
        self.path = path if path is not None else []
        self.current_point = 0
        self.vel = max_vel
        self.started = False

    def start(self):
        self.started = True

    def draw_points(self, win):
        for point in self.path:
            pygame.draw.circle(win, (255, 0, 0), point, 5)

    def draw(self, win):
        super().draw(win)
        # self.draw_points(win) # hidding the coordinate dots

    def calculate_angle(self):
        target_x, target_y = self.path[self.current_point]
        x_diff = target_x - self.x
        y_diff = target_y - self.y

        if y_diff == 0:
            desired_radian_angle = math.pi / 2
        else:
            desired_radian_angle = math.atan(x_diff / y_diff)

        if target_y > self.y:
            desired_radian_angle += math.pi

        difference_in_angle = self.angle - math.degrees(desired_radian_angle)
        if difference_in_angle >= 180:
            difference_in_angle -= 360

        if difference_in_angle > 0:
            self.angle -= min(self.rotation_vel, abs(difference_in_angle))
        else:
            self.angle += min(self.rotation_vel, abs(difference_in_angle))

    def update_path_point(self):
        target = self.path[self.current_point]
        target_x, target_y = target
        distance = math.hypot(target_x - self.x, target_y - self.y)
        if distance <= 25:
            self.current_point += 1

    def move(self):
        if not self.started:
            return
        if self.current_point >= len(self.path):
            return

        self.calculate_angle()
        self.update_path_point()
        super().move()

    def reset(self):
        super().reset()
        self.current_point = 0
        self.started = False
        self.vel = self.max_vel

def render_outlined_text(font, text, text_color, outline_color, outline_width=3):
    base = font.render(text, True, text_color)
    size = (base.get_width() + outline_width * 2, base.get_height() + outline_width * 2)
    surface = pygame.Surface(size, pygame.SRCALPHA)

    outline = font.render(text, True, outline_color)
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                surface.blit(outline, (dx + outline_width, dy + outline_width))

    surface.blit(base, (outline_width, outline_width))
    return surface

def format_time(ms):
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    return f"{minutes:02}.{seconds:02}.{millis:03}"

def draw_button(win, rect, text, base_color, hover_color):
    mouse_pos = pygame.mouse.get_pos()
    color = hover_color if rect.collidepoint(mouse_pos) else base_color
    pygame.draw.rect(win, color, rect, border_radius=12)
    label = MAIN_FONT.render(text, True, (255, 255, 255))
    win.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

def draw_stepper(win, label, value, value_fmt, rect, minus_rect, plus_rect):
    label_text = MAIN_FONT.render(label, True, (255, 255, 255))
    win.blit(label_text, (WIDTH // 2 - label_text.get_width() // 2, rect.top - 55))

    draw_button(win, minus_rect, '-', (70, 70, 70), (110, 110, 110))
    draw_button(win, plus_rect, '+', (70, 70, 70), (110, 110, 110))

    value_text = MAIN_FONT.render(value_fmt.format(value), True, (255, 255, 255))
    win.blit(value_text, (rect.centerx - value_text.get_width() // 2, rect.centery - value_text.get_height() // 2))

async def settings_screen(win, images, player_speed, bounce_factor):
    title_text = MAIN_FONT.render("Settings", True, (255, 255, 255))

    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(200)

    speed_min, speed_max, speed_step = 2.0, 10.0, 0.5
    bounce_min, bounce_max, bounce_step = 0.2, 2.0, 0.1

    speed_row_y = HEIGHT // 2 - 140
    bounce_row_y = HEIGHT // 2 - 20

    speed_value_rect = pygame.Rect(0, 0, 100, 40)
    speed_value_rect.center = (WIDTH // 2, speed_row_y)
    speed_minus_rect = pygame.Rect(0, 0, 40, 40)
    speed_minus_rect.center = (speed_value_rect.left - 40, speed_row_y)
    speed_plus_rect = pygame.Rect(0, 0, 40, 40)
    speed_plus_rect.center = (speed_value_rect.right + 40, speed_row_y)

    bounce_value_rect = pygame.Rect(0, 0, 100, 40)
    bounce_value_rect.center = (WIDTH // 2, bounce_row_y)
    bounce_minus_rect = pygame.Rect(0, 0, 40, 40)
    bounce_minus_rect.center = (bounce_value_rect. left - 40, bounce_row_y)
    bounce_plus_rect = pygame.Rect(0, 0, 40, 40)
    bounce_plus_rect.center = (bounce_value_rect.right + 40, bounce_row_y)

    back_rect = pygame.Rect(0, 0, 220, 60)
    back_rect.center = (WIDTH // 2, bounce_row_y + 160)

    waiting = True
    while waiting:
        for img, pos in images:
            win.blit(img, pos)

        win.blit(overlay, (0, 0))
        win.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, speed_row_y - 160))

        draw_stepper(win, "Your Top Speed", player_speed, "{:.1f}", speed_value_rect, speed_minus_rect, speed_plus_rect)
        draw_stepper(win, "Wall Bounciness", bounce_factor, "{:.1f}", bounce_value_rect, bounce_minus_rect, bounce_plus_rect)

        draw_button(win, back_rect, "Back", (70, 70, 70), (110, 110, 110))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if speed_minus_rect.collidepoint(event.pos):
                    player_speed = max(speed_min, round(player_speed - speed_step, 1))
                elif speed_plus_rect.collidepoint(event.pos):
                    player_speed = min(speed_max, round(player_speed + speed_step, 1))
                elif bounce_minus_rect.collidepoint(event.pos):
                    bounce_factor = max(bounce_min, round(bounce_factor - bounce_step, 1))
                elif bounce_plus_rect.collidepoint(event.pos):
                    bounce_factor = min(bounce_max, round(bounce_factor + bounce_step, 1))
                elif back_rect.collidepoint(event.pos):
                    waiting = False
        await asyncio.sleep(0)
    return player_speed, bounce_factor 

async def level_select_screen(win, images, player_speed, bounce_factor):
    title_text = MAIN_FONT.render("Select Difficulty", True, (255, 255, 255))
    hint_font = pygame.font.SysFont("comicsans", 24)
    hint_text = hint_font.render('Use WASD or Arrow Keys to drive', True, (200, 200, 200))

    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(200)

    button_width, button_height, spacing = 220, 60, 20
    total_height = button_height * 3 + spacing * 2
    start_y = HEIGHT // 2 - total_height // 2 + 20

    easy_rect = pygame.Rect(0, 0, button_width, button_height)
    easy_rect.center = (WIDTH // 2, start_y)
    medium_rect = pygame.Rect(0, 0, button_width, button_height)
    medium_rect.center = (WIDTH // 2, start_y + button_height + spacing)
    hard_rect = pygame.Rect(0, 0, button_width, button_height)
    hard_rect.center = (WIDTH // 2, start_y + 2 * (button_height + spacing))

    settings_rect = pygame.Rect(0, 0, button_width, button_height)
    settings_rect.center = (WIDTH // 2, hard_rect.bottom + spacing + button_height // 2)

    levels = [
        ('Easy', 3, easy_rect, False, (40, 120, 40), (60, 160, 60)),
        ('Medium', 4.5, medium_rect, False, (150, 140, 40), (190, 180, 60)),
        ('Wonky', 6, hard_rect, True, (150, 40, 40), (190, 60, 60))
    ]

    waiting = True
    while waiting: 
        for img, pos in images:
            win.blit(img, pos)

        win.blit(overlay, (0, 0))
        win.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, start_y - 100))

        for label, speed, rect, noclip, base_color, hover_color in levels:
            draw_button(win, rect, label, base_color, hover_color)

        draw_button(win, settings_rect, "Settings", (60, 60, 90), (90, 90, 130))

        win.blit(hint_text, (WIDTH // 2 - hint_text.get_width() // 2, hard_rect.bottom + 100))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if settings_rect.collidepoint(event.pos):
                    player_speed, bounce_factor = await settings_screen(win, images, player_speed, bounce_factor)
                else:
                    for label, speed, rect, noclip, base_color, hover_color in levels:
                        if rect.collidepoint(event.pos):
                            return speed, player_speed, bounce_factor, noclip
        await asyncio.sleep(0)

async def countdown_screen(win, images, player_car, computer_car):
    numbers = ["3", "2", "1", "GO!"]
    clock = pygame.time.Clock()

    for number in numbers:
        text = render_outlined_text(COUNTDOWN_FONT, number, (255, 255, 255), (0, 0, 0), outline_width=4)
        display_ms = 700
        elapsed = 0

        while elapsed < display_ms:
            clock.tick(FPS)
            elapsed += clock.get_time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

            for img, pos in images:
                win.blit(img, pos)

            player_car.draw(win)
            computer_car.draw(win)

            win.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
            pygame.display.update()
            await asyncio.sleep(0)

async def end_screen(win, images, won):
    message = "You Win!" if won else "Too Slow!"
    result_text = MAIN_FONT.render(message, True, (255, 255, 255))

    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(200)

    button_rect = pygame.Rect(0, 0, 220, 60)
    button_rect.center = (WIDTH // 2, HEIGHT // 2 + 60)

    waiting = True
    while waiting:
        for img, pos in images:
            win.blit(img, pos)

        win.blit(overlay, (0, 0))
        win.blit(result_text, (WIDTH // 2 - result_text.get_width() // 2, HEIGHT // 2 - 60))
        draw_button(win, button_rect, "Restart", (70, 70, 70), (110, 110, 110))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    waiting = False
        await asyncio.sleep(0)

def draw(win, images, player_car, computer_car):
    for img, pos in images:
        win.blit(img, pos)

    player_car.draw(win)
    computer_car.draw(win)

    current_lap = min(player_car.laps + 1, TOTAL_LAPS)
    lap_num_text = LAP_FONT.render(f"Lap {current_lap}/{TOTAL_LAPS}", True, (255, 255, 255))

    elapsed_ms = pygame.time.get_ticks() - player_car.lap_start_time
    time_text = LAP_FONT.render(f'Time: {format_time(elapsed_ms)}', True, (255, 255, 255))

    lines = [lap_num_text, time_text]
    padding = 6
    line_spacing = 2

    box_width = max(line.get_width() for line in lines) + padding * 2
    box_height = sum(line.get_height() for line in lines) + padding * 2 + line_spacing * (len(lines) - 1)
    box_rect = pygame.Rect(10, 10, box_width, box_height)

    box_surface = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(box_surface, (0, 0, 0, 150), box_surface.get_rect(), border_radius=12)
    win.blit(box_surface, (box_rect.x, box_rect.y))

    y = box_rect.y + padding
    for line in lines:
        win.blit(line, (box_rect.x + padding, y))
        y += line.get_height() + line_spacing

    pygame.display.update()
     
def move_player(player_car):
    keys = pygame.key.get_pressed()
    moved = False

    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        player_car.rotate(left = True)
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        player_car.rotate(right = True)
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        moved = True
        player_car.move_forward()
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        moved = True
        player_car.move_backward()

    if not moved: player_car.reduce_speed()

def handle_collision(player_car, computer_car, noclip = False):
    car_half_w = player_car.IMG.get_width() // 2
    car_half_h = player_car.IMG.get_height() // 2

    hit_edge = False
    if player_car.x < car_half_w:
        player_car.x = car_half_w
        hit_edge = True 
    elif player_car.x > WIDTH - car_half_w:
        player_car.x = WIDTH - car_half_w
        hit_edge = True

    if player_car.y < car_half_h:
        player_car.y = HEIGHT - car_half_h
        hit_edge = True
    elif player_car.y > HEIGHT - car_half_h:
        player_car.y = HEIGHT - car_half_h
        hit_edge = True

    if hit_edge:
        player_car.bounce()

    if not noclip and player_car.collide(TRACK_BORDER_MASK) != None:
        player_car.bounce()

    if player_car.lap_cooldown > 0:
        player_car.lap_cooldown -= 1
    if computer_car.lap_cooldown > 0:
        computer_car.lap_cooldown -= 1

    computer_finish_poi_collide = computer_car.collide(FINISH_MASK, *FINISH_POSITION)
    if computer_finish_poi_collide != None and computer_car.lap_cooldown == 0:
        computer_car.laps += 1
        computer_car.lap_cooldown = LAP_COOLDOWN_FRAMES
        if computer_car.laps >= TOTAL_LAPS:
            return "lose"

    player_finish_poi_collide = player_car.collide(FINISH_MASK, *FINISH_POSITION)
    if player_finish_poi_collide != None and player_car.lap_cooldown == 0:
        if player_finish_poi_collide[1] == 0:
            player_car.bounce()
        else:
            player_car.laps += 1
            player_car.lap_cooldown = LAP_COOLDOWN_FRAMES
            if player_car.laps >= TOTAL_LAPS:
                return "win"

async def main():
    WIN = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Racing Game!")


    

    run = True
    clock = pygame.time.Clock()
    images = [(GRASS, (0, 0)), (TRACK, (0,0)), (FINISH, FINISH_POSITION), (TRACK_BORDER, (0, 0))]
    player_car = PlayerCar(4, 4)
    player_speed = 4.0
    bounce_factor = 1.0
    # path up 
        
    while run:
        computer_speed, player_speed, bounce_factor, noclip = await level_select_screen(WIN, images, player_speed, bounce_factor)
        player_car = PlayerCar(player_speed, 4)
        player_car.bounce_factor = bounce_factor
        computer_car = ComputerCar(computer_speed, 4, PATH)

        await countdown_screen(WIN, images, player_car, computer_car)
        computer_car.start()
        player_car.lap_start_time = pygame.time.get_ticks()

        playing = True

        while playing:
            clock.tick(FPS)

            draw(WIN, images, player_car, computer_car)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    playing = False
                    break

            if not run:
                break

            move_player(player_car)
            computer_car.move()
            result = handle_collision(player_car, computer_car, noclip)

            if result is not None: 
                await end_screen(WIN, images, won=(result == 'win'))
                playing = False

            await asyncio.sleep(0)

# print(computer_car.path)
asyncio.run(main())