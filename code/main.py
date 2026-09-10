import pygame
import time 
import math
from utils import scale_image, blit_rotate_center

GRASS = scale_image(pygame.image.load('code/images/grass.jpg'), 2.5)
TRACK = scale_image(pygame.image.load('code/images/track.png'), 0.9)
TRACK_BORDER = scale_image(pygame.image.load('code/images/track-border.png'), 0.9)
TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)
FINISH = pygame.image.load('code/images/finish.png')
FINISH_MASK = pygame.mask.from_surface(FINISH)
FINISH_POSITION = (130, 250)
RED_CAR = scale_image(pygame.image.load('code/images/red-car.png'),  0.55)
GREEN_CAR = scale_image(pygame.image.load('code/images/green-car.png'), 0.55)

WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Racing Game!")

pygame.font.init()
MAIN_FONT = pygame.font.SysFont("comicsans", 44)

FPS = 60
PATH = [(176, 137), (148, 77), (65, 106), (61, 200), (60, 316), (59, 409), (71, 487), (125, 550), (179, 603), (241, 655), (310, 718), (382, 723), (409, 638), (420, 518), (492, 480), (590, 531), (596, 632), (624, 715), (707, 730), (741, 639), (738, 543), (737, 457), (725, 383), (619, 373), (533, 375), (447, 372), (392, 319), (425, 257), (500, 250), (571, 250), (641, 247), (717, 244), (746, 173), (723, 85), (640, 74), (536, 72), (445, 71), (364, 67), (291, 93), (284, 185), (284, 252), (281, 327), (272, 394), (218, 408), (163, 361), (152, 260), (152, 210)]

class AbstractCar():
    def __init__(self, max_vel, rotation_vel):
        self.max_vel = max_vel
        self.vel = 0
        self.rotation_vel = rotation_vel
        self.angle = 0
        self.x, self.y = self.START_POS
        self.acceleration = 0.1

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
        self.vel = -self.vel
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

def draw_button(win, rect, text, base_color, hover_color):
    mouse_pos = pygame.mouse.get_pos()
    color = hover_color if rect.collidepoint(mouse_pos) else base_color
    pygame.draw.rect(win, color, rect, border_radius=10)
    label = MAIN_FONT.render(text, True, (255, 255, 255))
    win.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

def draW_stepper(win, label, value, value_fmt, rect, minus_rect, plus_rect):
    label_text = MAIN_FONT.render(label, True, (255, 255, 255))
    win.blit(label_text, (rect.left, rect.top - 35))

    draw_button(win, minus_rect, '-', (70, 70, 70), (110, 110, 110))
    draw(win, plus_rect, '+', (70, 70, 70), (110, 110, 110))

    value_text = MAIN_FONT.render(value_fmt.format(value), True, (255, 255, 255))
    win.blit(value_text, (rect.centerx - value_text.get_width() // 2, rect.centery - value_text.get_height() // 2))

def level_select_screen(win, images):
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

    levels = [
        ('Easy', 3, easy_rect),
        ('Medium', 4.5, medium_rect),
        ('Hard', 6, hard_rect)
    ]

    waiting = True
    while waiting: 
        for img, pos in images:
            win.blit(img, pos)

        win.blit(overlay, (0, 0))
        win.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, start_y - 100))

        for label, speed, rect in levels:
            draw_button(win, rect, label, (70, 70, 70), (110, 110, 110))

        win.blit(hint_text, (WIDTH // 2 - hint_text.get_width() // 2, hard_rect.bottom + 30))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for label, speed, rect in levels:
                    if rect.collidepoint(event.pos):
                        return speed

def end_screen(win, images, won):
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

def draw(win, images, player_car, computer_car):
    for img, pos in images:
        win.blit(img, pos)

    player_car.draw(win)
    computer_car.draw(win)
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

def handle_collision(player_car, computer_car):
    if player_car.collide(TRACK_BORDER_MASK) != None:
        player_car.bounce()

    computer_finish_poi_collide = computer_car.collide(FINISH_MASK, *FINISH_POSITION)
    if computer_finish_poi_collide != None:
        return "lose"

    player_finish_poi_collide = player_car.collide(FINISH_MASK, *FINISH_POSITION)
    if player_finish_poi_collide != None:
        if player_finish_poi_collide[1] == 0:
            player_car.bounce()
        else: 
            return "win"

    return None


run = True
clock = pygame.time.Clock()
images = [(GRASS, (0, 0)), (TRACK, (0,0)), (FINISH, FINISH_POSITION), (TRACK_BORDER, (0, 0))]
player_car = PlayerCar(4, 4)
# path up 

while run:
    computer_speed = level_select_screen(WIN, images)
    computer_car = ComputerCar(computer_speed, 4, PATH)
    player_car.reset()

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

        if player_car.vel > 0 and not computer_car.started:
            computer_car.start()

        computer_car.move()
        result = handle_collision(player_car, computer_car)

        if result is not None: 
            end_screen(WIN, images, won=(result == 'win'))
            player = False

# print(computer_car.path)
pygame.quit()