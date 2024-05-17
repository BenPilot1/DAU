import pygame
from pygame import mixer
from fighter import Fighter
import socket
from encryption import *

mixer.init()
pygame.init()

music = True
ADDRESS = '127.0.0.1', 60000  # replace with server's IP and PORT

# create game window
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Divekicks Among Us")

# set framerate
clock = pygame.time.Clock()
FPS = 60

# define colours
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# define game variables
intro_count = 3
player_1_text = "You Are Red"
player_2_text = "You Are Blue"
last_count_update = pygame.time.get_ticks()
score = [0, 0]  # player scores. [P1, P2]
round_over = False
ROUND_OVER_COOLDOWN = 2000
round_over_time = 0
run = True

# define fighter variables
RED_SIZE = 245
RED_SCALE = 0.8
RED_OFFSET = [72, -60]
RED_DATA = [RED_SIZE, RED_SCALE, RED_OFFSET]
BLUE_SIZE = 245
BLUE_SCALE = 0.8
BLUE_OFFSET = [112, -60]
BLUE_DATA = [BLUE_SIZE, BLUE_SCALE, BLUE_OFFSET]

# load music and sounds
pygame.mixer.music.load("assets/audio/music.mp3")
pygame.mixer.music.set_volume(0.5)
if music:
    pygame.mixer.music.play(-1, 0.0, 5000)
# load background image
bg_image = pygame.image.load("assets/images/background/background.jpg")
login_image = pygame.image.load("assets/images/login.jpg")
wrong_image = pygame.image.load("assets/images/wrong.jpg")
wait_image = pygame.image.load("assets/images/waiting.jpg")
taken_image = pygame.image.load("assets/images/taken.jpg")
exists_image = pygame.image.load("assets/images/exists.jpg")
# load spritesheets
red_sheet = pygame.image.load("assets/images/crewmate/red.png")
blue_sheet = pygame.image.load("assets/images/crewmate/blue.png")

# load vicory image

# define number of steps in each animation
RED_ANIMATION_STEPS = [1, 1, 1, 1]
BLUE_ANIMATION_STEPS = [1, 1, 1, 1]

# define font
count_font = pygame.font.Font("assets/fonts/turok.ttf", 80)
score_font = pygame.font.Font("assets/fonts/turok.ttf", 30)
login_font = pygame.font.Font("assets/fonts/amongus vector.ttf", 80)

# class
class Client:
    def __init__(self, address):
        global run
        self.address = address
        try:
            self.sock = socket.socket()
            self.sock.connect(address)
            set_key(list(self.sock.recv(95).decode()))
            self.sock.settimeout(0.02)
        except socket.error:
            run = False

    def recv_by_size(self) -> str:
        try:
            data_length = int(self.sock.recv(9)[:8])
            data_bytes = decrypt(self.sock.recv(data_length).decode())
            print(f'recv {data_bytes}')
            return data_bytes
        except socket.timeout:
            return 'Time Out'
        except socket.error:
            return ''
        except ValueError:
            return ''

    def send_with_size(self, data: str) -> bool:
        data_bytes = encrypt(data).encode()
        data_length = str(len(data_bytes)).zfill(8).encode()
        while True:
            try:
                self.sock.send(data_length + b'~' + data_bytes)
                print(f'sent {data_bytes}')
                return False
            except socket.timeout:
                pass
            except socket.error:
                return True


# function for drawing text
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


# function for drawing background
def draw_bg():
    scaled_bg = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(scaled_bg, (0, 0))

def draw_login():
    screen.blit(login_image, (0, 0))

def draw_wrong():
    screen.blit(wrong_image, (0,0))

def draw_taken():
    screen.blit(taken_image, (0, 0))

def draw_exists():
    screen.blit(exists_image, (0, 0))
def draw_wi():
    scaled_wi = pygame.transform.scale(wait_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(scaled_wi, (0, 0))
# function for drawing fighter health bars
def draw_health_bar(health, x, y):
    ratio = health / 100
    pygame.draw.rect(screen, WHITE, (x - 2, y - 2, 404, 34))
    pygame.draw.rect(screen, RED, (x, y, 400, 30))
    pygame.draw.rect(screen, YELLOW, (x, y, 400 * ratio, 30))


def gamestart(client: Client, round_over, intro_count, last_count_update, round_over_time):
    global run
    # create two instances of fighters
    username = ''
    password = ''
    un = False
    pw = False
    wrong = False
    taken = False
    exists = False
    usernames = []
    current_screen = 'LOGIN'
    while run:
        while current_screen == 'LOGIN':
            if wrong:
                draw_wrong()
            elif taken:
                draw_taken()
            elif exists:
                draw_exists()
            else:
                draw_login()
            draw_text(username, login_font, RED, 216, 190)
            draw_text(password, login_font, RED, 216, 390)
            pygame.display.update()
            data = client.recv_by_size()
            if data == 'Time Out':
                pass
            elif data == '':
                run = False
                break
            else:
                if data == 'CORRECT':
                    usernames.append(username)
                    current_screen = 'WAIT'
                    break
                if data == 'TAKEN':
                    taken = True
                    username = ''
                    password = ''
                if data == 'EXISTS':
                    exists = True
                    username = ''
                    password = ''
                if data == 'WRONG':
                    wrong = True
                    username = ''
                    password = ''
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    client.send_with_size('EXIT')
                    current_screen = 'NONE'
                    run = False
                    break
                elif event.type == pygame.KEYDOWN:
                    print("1")
                    if event.key == pygame.K_BACKSPACE:
                        if un and len(username) > 0:
                            username = username[:-1]
                        elif pw and len(password) > 0:
                            password = password[:-1]
                    elif event.unicode.isalpha() or event.unicode.isnumeric():
                        if un:
                            username += event.unicode
                            if len(username) > 22:
                                username = username[:-1]
                        elif pw:
                            password += event.unicode
                            if len(password) > 22:
                                password = password[:-1]
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    exists = False
                    taken = False
                    wrong = False
                    un = False
                    pw = False
                    x, y = pygame.mouse.get_pos()
                    if 216 <= x <= 764:
                        if 181 <= y <= 288:
                            un = True
                            pw = False
                        elif 380 <= y <= 487:
                            un = False
                            pw = True
                    if 548 <= x <= 705 and 509 <= y <= 579:
                        client.send_with_size(f'LOGIN~{username}~{password}')
                    if 248 <= x <= 441 and 508 <= y <= 579:
                        client.send_with_size(f'SIGNUP~{username}~{password}')

        while current_screen == 'WAIT':
            score = [0, 0]
            draw_wi()
            draw_text("Waiting For Player...", count_font, RED, SCREEN_WIDTH / 6, SCREEN_HEIGHT / 3)
            pygame.display.update()
            while run:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        client.send_with_size('EXIT')
                        current_screen = 'NONE'
                        run = False
                        break
                data = client.recv_by_size()
                if data == 'Time Out':
                    continue
                elif data == '':
                    run = False
                    break
                else:
                    data_fields = data.split('~')
                if data_fields[0] == 'START':
                    if data_fields[1] == '1':
                        player = Fighter(1, 200, 310, False, RED_DATA, red_sheet, RED_ANIMATION_STEPS, RED)
                        enemy = Fighter(2, 700, 310, True, BLUE_DATA, blue_sheet, BLUE_ANIMATION_STEPS, BLUE)
                        current_screen = 'GAME'
                        break
                    elif data_fields[1] == '2':
                        player = Fighter(2, 700, 310, True, BLUE_DATA, blue_sheet, BLUE_ANIMATION_STEPS, BLUE)
                        enemy = Fighter(1, 200, 310, False, RED_DATA, red_sheet, RED_ANIMATION_STEPS, RED)
                        current_screen = 'GAME'
                        break
                    else:
                        print('Error problem with one of the data fields')
                else:
                    print('Did not expected for that specific type of message')


            # game loop
            while current_screen == 'GAME':
                clock.tick(FPS)

                draw_bg()

                if player.player_num == 1:
                    draw_health_bar(player.health, 20, 20)
                    draw_health_bar(enemy.health, 580, 20)
                    draw_text("P1: " + str(score[0]), score_font, RED, 20, 60)
                    draw_text("P2: " + str(score[1]), score_font, RED, 580, 60)
                else:
                    draw_health_bar(enemy.health, 20, 20)
                    draw_health_bar(player.health, 580, 20)
                    draw_text("P1: " + str(score[0]), score_font, RED, 20, 60)
                    draw_text("P2: " + str(score[1]), score_font, RED, 580, 60)


                data = client.recv_by_size()
                data_fields = data.split('~')
                if data_fields[0] == 'WAIT':
                    current_screen = 'WAIT'
                    break
                elif data_fields[0] == 'ENEMY':
                    enemy.move_enemy(SCREEN_WIDTH, SCREEN_HEIGHT, player, round_over, data_fields[1:])
                if intro_count <= 0:
                    status = player.move_player(SCREEN_WIDTH, SCREEN_HEIGHT, enemy, round_over)
                    client.send_with_size(f'STATUS~{status}')
                else:
                    if player.player_num == 1:
                        draw_text(player_1_text, count_font, RED, SCREEN_WIDTH / 3, SCREEN_HEIGHT / 4)
                    else:
                        draw_text(player_2_text, count_font, BLUE, (SCREEN_WIDTH / 3) - 10, SCREEN_HEIGHT / 4)
                    draw_text(str(intro_count), count_font, RED, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3)
                    if (pygame.time.get_ticks() - last_count_update) >= 1000:
                        intro_count -= 1
                        last_count_update = pygame.time.get_ticks()

                player.update()
                enemy.update()

                player.draw(screen)
                enemy.draw(screen)

                if not round_over:
                    if not player.alive:
                        score[enemy.player_num - 1] += 1
                        round_over = True
                        round_over_time = pygame.time.get_ticks()
                    elif not enemy.alive:
                        score[player.player_num - 1] += 1
                        round_over = True
                        round_over_time = pygame.time.get_ticks()
                else:
                    if not enemy.alive:
                        draw_text("you win", count_font, player.color, 360, 150)
                    elif not player.alive:
                        draw_text("you lose", count_font, enemy.color, 360, 150)
                    if pygame.time.get_ticks() - round_over_time > ROUND_OVER_COOLDOWN:
                        round_over = False
                        intro_count = 3
                        if player.player_num == 1:
                            player = Fighter(1, 200, 310, False, RED_DATA, red_sheet, RED_ANIMATION_STEPS, RED)
                            enemy = Fighter(2, 700, 310, True, BLUE_DATA, blue_sheet, BLUE_ANIMATION_STEPS, BLUE)
                        elif player.player_num == 2:
                            player = Fighter(2, 700, 310, True, BLUE_DATA, blue_sheet, BLUE_ANIMATION_STEPS, BLUE)
                            enemy = Fighter(1, 200, 310, False, RED_DATA, red_sheet, RED_ANIMATION_STEPS, RED)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        client.send_with_size('EXIT')
                        run = False
                        current_screen = 'NONE'
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            client.send_with_size('BTL')
                            current_screen = 'LOGIN'
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        x, y = pygame.mouse.get_pos()
                        if 461 <= x <= 531 and 16 <= y <= 71:
                            client.send_with_size('BTL')
                            current_screen = 'LOGIN'


                pygame.display.update()



if __name__ == '__main__':
    client = Client(ADDRESS)
    gamestart(client, round_over, intro_count, last_count_update, round_over_time)
    client.sock.close()
# exit pygame
pygame.quit()

