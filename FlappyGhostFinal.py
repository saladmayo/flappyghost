
import pygame
from sys import exit
import random

pygame.init()
pygame.mixer.init()
clock = pygame.time.Clock()

# window size
win_height = 720
win_width = 551
window = pygame.display.set_mode((win_width, win_height))

# download images & other assets
ghost_images = [pygame.image.load("assets/up.png"),
                pygame.image.load("assets/mid.png"),
                pygame.image.load("assets/down.png")]
skyline_image = pygame.image.load("assets/background.png")
ground_image = pygame.image.load("assets/ground.png")
top_pipe_image = pygame.image.load("assets/pipe_top.png")
bottom_pipe_image = pygame.image.load("assets/pipe_bottom.png")
game_over_image = pygame.image.load("assets/game_over.png")
start_image = pygame.image.load("assets/start.png")
jump_sound = pygame.mixer.Sound("assets/sound/jump_2.mp3")
jump_sound.set_volume(0.025)
hit_sound = pygame.mixer.Sound("assets/sound/hit.mp3")
hit_sound.set_volume(0.3)
levelup_sound = pygame.mixer.Sound("assets/sound/levelup.mp3")
levelup_sound.set_volume(0.3)
# Initialize high score
high_score = 0

# Load the high score from a file if it exists
try:
    with open("highscore.txt", "r") as file:
        content = file.read().strip()
        if content:
            high_score = int(content)
        else:
            high_score = 0
except FileNotFoundError:
    high_score = 0


# game
# set how fast the game runs
# the higher the number, the faster speed from right side of the screen passing to the left
# the faster the ground is moving
scroll_speed = 2
# every how many level the speed go up
speed_increase_threshold = 10
# start position of ghost
ghost_start_position = (100, 250)
# count by using the bottom pipe
score = 0
font = pygame.font.SysFont('Segoe', 26)
game_stopped = True

# Array of ghost: index[0, 1, 2]
# different wing position - image_index: 0 = down.png, 1 = mid.png, 2 = up.png
# animate image sequentially: loop through the array(increases number in array then resets again)
# increment image_index every time the function is called
# image changing every 10 increments -> image_index: 0 = 0-9, 1 = 10-19, 2 = 20-29
# reset image_index to 0 when reaches 30
# floor image_index by 10: e.g. 0-9 = 0 (down.png)
class Ghost(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = ghost_images[0]
        self.rect = self.image.get_rect()
        # center of the rectangle is equal to the start position
        self.rect.center = ghost_start_position
        self.image_index = 0

        # adding y-coordinate: y + velocity -> velocity + 0.5 (decelerate due to gravity)
        # e.g. vel = -7 (0 loops) -> vel = -3 (8 loops; +0.5 8 times) -> vel = 0 (14 loops; +0.5 14 times)
        # velocity negative = ghost goes up, positive = ghost goes down
        # jump aka flap
        self.vel = 0
        self.jump = False
        # for scoring, set to False when the ghost dies
        self.alive = True

    # update +1 when the function is called
    # user_input = check whenever the user press the space bar (execute the jump)
    def update(self, user_input):
        # animate ghost
        if self.alive:
            self.image_index += 1
        if self.image_index >= 30:
            self.image_index = 0
        self.image = ghost_images[self.image_index // 10]

        # gravity and jump
        self.vel += 0.5     # every time the update function is called
                            # (every iteration of the main loop)
        # prevent the ghost moving down the screen faster than 7 pixels every while loop iteration
        # specify how fast the ghost will fall after press key to jump
        if self.vel > 5:
            self.vel = 5
        # prevent the ghost falling below the ground level
        # add velocity to the y-coordinate
        if self.rect.y < 500:
            self.rect.y += int(self.vel)
        # velocity = 0: highest point of the jump
        # the user can't execute another jump before the highest point is reached
        if self.vel == 0:
            self.jump = False

        # rotate ghost
        self.image = pygame.transform.rotate(self.image, self.vel * -7)

        # user input
        # self.jump has to be false
        # self.rect.y: the y position of the ghost needs to be the top of the window
        # jump height
        if user_input[pygame.K_SPACE] and not self.jump and self.rect.y > 0 and self.alive:
            self.jump = True
            self.vel = -7
            jump_sound.play() # Play jump sound


class Pipe(pygame.sprite.Sprite):
    # takes the arguments x and y, which are coordinate of the pipe
    def __init__(self, x, y, image, pipe_type):
        # initialize the parent class
        pygame.sprite.Sprite.__init__(self)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        # for scoring, uses the pipes to count score
        # left-handed side of the pipe = enter
        # right-handed side of the pipe = exit
        # when passes each pipe: enter & exit = True -> passed = True -> score +1
        self.enter, self.exit, self.passed = False, False, False
        self.pipe_type = pipe_type

    # move pipe
    def update(self):
        self.rect.x -= scroll_speed
        if self.rect.x <= -win_width:
            self.kill()

        # score
        global score
        if self.pipe_type == 'bottom':
            if ghost_start_position[0] > self.rect.topleft[0] and not self.passed:
                self.enter = True
            if ghost_start_position[0] > self.rect.topright[0] and not self.passed:
                self.exit = True
            if self.enter and self.exit and not self.passed:
                self.passed = True
                score += 1
                update_high_score()


class Ground(pygame.sprite.Sprite):
    # x,y : coordinate of ground piece moving
    def __init__(self, x, y):
        # initialize the base class
        pygame.sprite.Sprite.__init__(self)
        self.image = ground_image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y

    def update(self):
        self.rect.x -= scroll_speed
        if self.rect.right <= 0:
            self.kill()

def quit_game():
    # exit game
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()


def display_high_score():
    # Display high score on the screen in the top right corner
    high_score_text = font.render('High Score: ' + str(high_score), True, pygame.Color(255, 255, 255))
    text_rect = high_score_text.get_rect()
    text_rect.topleft = (win_width - text_rect.width - 20, 20)  # Adjust the coordinates for the top right corner
    window.blit(high_score_text, text_rect)

def update_high_score():
    global high_score
    if score > high_score:
        high_score = score
        save_high_score()

def save_high_score():
    global high_score
    # Save the high score to a file
    with open("highscore.txt", "w") as file:
        file.write(str(high_score))

def game_over():
    global game_stopped, score

    if score > high_score:
        update_high_score()

# game main method
def main():
    global score, scroll_speed, speed_increase_threshold, pipe_timer, game_stopped

    # instantiate ghost
    ghost = pygame.sprite.GroupSingle()
    # created an instance of the class ghost then added to group single
    ghost.add(Ghost())
    # Constant for hit detect sound
    hit_sound_played = False

    # Play the background music in an infinite loop.
    pygame.mixer.music.load("assets/sound/bgm.mp3")
    pygame.mixer.music.set_volume(0.1)
    pygame.mixer.music.play(-1)

    # set up the pipes
    pipe_timer = 0
    pipes = pygame.sprite.Group()

    # instantiate initial ground
    # initialize ground element at the beginning of the game
    x_pos_ground, y_pos_ground = 0, 505
    ground = pygame.sprite.Group()
    ground.add(Ground(x_pos_ground, y_pos_ground))

    run = True
    while run:
        # quit
        quit_game()

        # reset Frame: set frame window to black
        window.fill((0, 0, 0))

        # user input
        user_input = pygame.key.get_pressed()

        # draw background
        # blit takes two arguments: image, position coordinate
        window.blit(skyline_image, (0, 0))

        # spawn ground
        if len(ground) <= 2:
             ground.add(Ground(win_width, y_pos_ground))

        # draw - pipes, ground, and bird
        pipes.draw(window)
        ground.draw(window)
        ghost.draw(window)

        # show score
        score_text = font.render('Score: ' + str(score), True, pygame.Color(255, 255, 255))
        window.blit(score_text, (20, 20))

        # update - pipes, ground, and bird
        if ghost.sprite.alive:
            pipes.update()
            ground.update()

        # Speed up when it reach every 10 score until 30
        if score >= speed_increase_threshold and score <= 30:
            scroll_speed += 1
            levelup_sound.play()
            speed_increase_threshold += 10

        ghost.update(user_input)

        # collision detection
        # spritecollide: find sprites in a group that intersect another sprite
        collision_pipes = pygame.sprite.spritecollide(ghost.sprites()[0], pipes, False)
        collision_ground = pygame.sprite.spritecollide(ghost.sprites()[0], ground, False)
        if collision_ground or collision_pipes:
            # Play hit sound once.
            if not hit_sound_played:
                if collision_pipes or collision_ground:
                    hit_sound.play()  # Play the collision sound.
                    hit_sound_played = True  # Mark the sound as played.
                    ghost.sprite.alive = False  # Handle the rest of the game over logic.
            ghost.sprite.alive = False
            pygame.mixer.music.stop()  # Stop the background music.
            if collision_ground:
                window.blit(game_over_image, (win_width // 2 - game_over_image.get_width() // 2,
                                              win_height // 2 - game_over_image.get_height() // 2))
                if user_input[pygame.K_SPACE]:
                    score = 0
                    scroll_speed = 2
                    speed_increase_threshold = 10
                    break

        # game over score update
        if not ghost.sprite.alive and not game_stopped:
            game_stopped = True
            game_over()

        # spawn pipes
        if pipe_timer <= 0 and ghost.sprite.alive:
            x_top, x_bottom = 550, 550
            y_top = random.randint(-600, -480)
            # make a gap between top and bottom pipe
            y_bottom = y_top + random.randint(90, 130) + bottom_pipe_image.get_height()
            pipes.add(Pipe(x_top, y_top, top_pipe_image, 'top'))
            # adding attributes to the pipes: top & bottom
            # uses for counting score
            pipes.add(Pipe(x_bottom, y_bottom, bottom_pipe_image, 'bottom'))
            pipe_timer = random.randint(180, 250)
        pipe_timer -= scroll_speed

        display_high_score()

        # limit fps to 60
        clock.tick(60)
        pygame.display.update()


# menu
def menu():
    global game_stopped

    # Load high score from file
    update_high_score()

    # make the menu run when the game stop
    while game_stopped:
        quit_game()

        # draw menu
        window.fill((0, 0, 0))
        window.blit(skyline_image, (0, 0))
        window.blit(ground_image, Ground(0, 505))
        window.blit(ghost_images[0], (100, 250))
        window.blit(start_image, (win_width // 2 - start_image.get_width() // 2,
                                  win_height // 2 - start_image.get_height() // 2))

        # user input
        user_input = pygame.key.get_pressed()
        # if user input is the space key it will run the main function
        if user_input[pygame.K_SPACE]:
            main()

        display_high_score()

        pygame.display.update()

menu()