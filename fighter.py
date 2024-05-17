import pygame
import socket

s = socket.socket()
class Fighter:
    def __init__(self, player_num, x, y, flip, data, sprite_sheet, animation_steps, color):
        self.player_num = player_num
        self.size = data[0]
        self.image_scale = data[1]
        self.offset = data[2]
        self.flip = flip
        self.animation_list = self.load_images(sprite_sheet, animation_steps)
        self.action = 0
        self.frame_index = 0
        self.image = self.animation_list[self.action][self.frame_index]
        self.update_time = pygame.time.get_ticks()
        self.rect = pygame.Rect((x, y, 80, 180))
        self.vel_y = 0
        self.jump = False
        self.attacking = False
        self.attack_cooldown = 0
        self.hit = False
        self.health = 100
        self.alive = True
        self.color = color
    def load_images(self, sprite_sheet, animation_steps):
        # extract images from spritesheet
        animation_list = []
        for y, animation in enumerate(animation_steps):
            temp_img_list = []
            for x in range(animation):
                temp_img = sprite_sheet.subsurface(x * self.size, y * self.size, self.size, self.size)
                temp_img_list.append(
                    pygame.transform.scale(temp_img, (self.size * self.image_scale, self.size * self.image_scale)))
            animation_list.append(temp_img_list)
        return animation_list

    def move_enemy(self, screen_width, screen_height, target, round_over, status):
        SPEED = 40
        GRAVITY = 2
        dx = 0
        dy = 0
        if not self.attacking and self.alive and not round_over:
            # check player 1 controls
            if self.player_num == 1:
                # jump
                if status[0] == 'JUMP':
                    self.vel_y = -30
                    self.jump = True
                # attack
                elif status[0] == 'ATTACK':
                    dx = SPEED
                    self.vel_y += 10
                    self.attacking = True
                    if status[1] == 'True':
                        target.health -= 100
                        target.hit = True
                elif status[0] == 'BACKDASH':
                    dx = -SPEED / 2

            if self.player_num == 2:
                # jump
                if status[0] == 'JUMP':
                    self.vel_y = -30
                    self.jump = True
                # attack
                elif status[0] == 'ATTACK':
                    dx = -SPEED
                    self.attacking = True
                    self.vel_y += 10
                    if status[1] == 'True':
                        target.health -= 100
                        target.hit = True

                elif status[0] == 'BACKDASH':
                    dx = SPEED / 2

        # apply gravity
        self.vel_y += GRAVITY
        dy += self.vel_y

        # ensure player stays on screen
        if self.rect.left + dx < 0:
            dx = -self.rect.left
        if self.rect.right + dx > screen_width:
            dx = screen_width - self.rect.right
        if self.rect.bottom + dy > screen_height - 110:
            self.vel_y = 0
            self.jump = False
            dy = screen_height - 110 - self.rect.bottom

        # apply attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # update player position
        self.rect.x += dx
        self.rect.y += dy

    def move_player(self, screen_width, screen_height, target, round_over):
        SPEED = 40
        GRAVITY = 2
        dx = 0
        dy = 0
        status = 'IDLE'
        # get key presses
        key = pygame.key.get_pressed()

        # can only perform other actions if not currently attacking
        if not self.attacking and self.alive and not round_over:
            # check player 1 controls
            if self.player_num == 1:
                # jump
                if (key[pygame.K_z] or key[pygame.K_DOWN]) and not self.jump:
                    self.vel_y = -30
                    self.jump = True
                    status = 'JUMP'
                # attack
                if (key[pygame.K_x] or key[pygame.K_RIGHT]) and self.jump:
                    dx = SPEED
                    self.vel_y += 10
                    status = 'ATTACK~' + str(self.attack(target))
                elif (key[pygame.K_x] or key[pygame.K_RIGHT]) and not self.jump:
                    dx = -SPEED / 2
                    status = 'BACKDASH'
            # check player 2 controls
            if self.player_num == 2:
                # jump
                if (key[pygame.K_DOWN] or key[pygame.K_z]) and not self.jump:
                    self.vel_y = -30
                    self.jump = True
                    status = 'JUMP'
                # attack
                if (key[pygame.K_RIGHT] or key[pygame.K_x]) and self.jump:
                    dx = -SPEED
                    self.vel_y += 10
                    status = 'ATTACK~' + str(self.attack(target))
                if (key[pygame.K_RIGHT] or key[pygame.K_x]) and not self.jump:
                    dx = SPEED / 2
                    status = 'BACKDASH'
        # apply gravity
        self.vel_y += GRAVITY
        dy += self.vel_y

        # ensure player stays on screen
        if self.rect.left + dx < 0:
            dx = -self.rect.left
        if self.rect.right + dx > screen_width:
            dx = screen_width - self.rect.right
        if self.rect.bottom + dy > screen_height - 110:
            self.vel_y = 0
            self.jump = False
            dy = screen_height - 110 - self.rect.bottom

        # apply attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # update player position
        self.rect.x += dx
        self.rect.y += dy

        return status

    # handle animation updates
    def update(self):
        # check what action the player is performing
        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.update_action(3)
        elif self.hit:
            self.update_action(3)
        elif self.attacking:
            self.update_action(2)
        elif self.jump:
            self.update_action(1)
        else:
            self.update_action(0)

        animation_cooldown = 50
        # update image
        self.image = self.animation_list[self.action][self.frame_index]
        # check if enough time has passed since the last update
        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()
        # check if the animation has finished
        if self.frame_index >= len(self.animation_list[self.action]):
            # if the player is dead then end the animation
            if not self.alive:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0
                # check if an attack was executed
                if self.action == 2:
                    self.attacking = False
                # check if damage was taken
                if self.action == 3:
                    self.hit = False
                    # if the player was in the middle of an attack, then the attack is stopped
                    self.attacking = False
                    self.attack_cooldown = 20

    def attack(self, target) -> bool:
        if self.attack_cooldown == 0:
            self.attacking = True
            attacking_rect = pygame.Rect(self.rect.centerx - (2 * self.rect.width * self.flip), self.rect.y,
                                         2 * self.rect.width, self.rect.height)
            if attacking_rect.colliderect(target.rect):
                target.health -= 100
                target.hit = True
        return target.hit

    def update_action(self, new_action):
        # check if the new action is different to the previous one
        if new_action != self.action:
            self.action = new_action
            # update the animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def draw(self, surface):
        img = pygame.transform.flip(self.image, self.flip, False)
        surface.blit(img, (self.rect.x - (self.offset[0] * self.image_scale), self.rect.y - (self.offset[1] * self.image_scale)))
