import pygame
from settings import *
from support import *
from timer import Timer

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, group, collision_sprites, sprites_of_trees, interaction, soil_layer, toggle_shop):
        super().__init__(group)
        self.import_assets()
        self.status = 'down_idle'
        self.frame_index = 0

        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(center = pos)
        self.hitbox = self.rect.copy().inflate((-126,-70))
        self.z = LAYERS['main']

        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 200

        self.target_position = (0,0)

        self.timers = {'tool use': Timer(400, self.use_tool),
                       'tool delay': Timer(200),
                       'seed use': Timer(400, self.use_seed),
                       'seed delay': Timer(200)
                       }

        self.tools = ['axe']
        self.tool_index = 0
        self.selected_tool = self.tools[self.tool_index]

        self.seeds = ['corn', 'tomato', 'raspbery']
        self.seeds_index = 0
        self.selected_seeds = self.seeds[self.seeds_index]

        self.sprites_collisions = collision_sprites

        self.sprites_of_trees = sprites_of_trees

        self.inventory = {
            'wood':   0,
            'apple':  0,
            'corn':   0,
            'tomato': 0,
            'raspbery': 0
        }
        self.seed_inventory = {
            'corn': 5,
            'tomato': 4,
            'raspbery': 2
        }
        self.special = {
            'autoharvest': 0,
            'hoe': 0,
            'water': 0
        }
        self.autoharvest = False

        self.money = 10

        self.interaction = interaction
        self.sleep = False

        self.soil_layer = soil_layer
        self.toggle_shop = toggle_shop
        self.attacking = False

    def use_tool(self):
        if self.selected_tool == 'hoe':
            self.soil_layer.get_hit(self.target_position)
            if not self.autoharvest:
                self.soil_layer.harvest(self.target_position, self.inventory)

        if self.selected_tool == 'axe':
            for tree in self.sprites_of_trees.sprites():
                if tree.rect.collidepoint(self.target_position):
                    tree.damage()
            self.attacking = True

        if self.selected_tool == 'water':
            self.soil_layer.water(self.target_position)

    def get_target_position(self):
        self.target_position = self.rect.center + PLAYER_TOOL_OFFSET[self.status.split('_')[0]]

    def use_seed(self):
        if self.seed_inventory[self.selected_seeds] > 0:
            if self.soil_layer.plant_seed(self.target_position, self.selected_seeds):
                self.seed_inventory[self.selected_seeds] -=1

    def import_assets(self):
        self.animations = {'up': [], 'down': [], 'left': [], 'right': [],
                           'up_idle': [], 'down_idle': [], 'left_idle': [], 'right_idle': [],
                           'up_hoe': [], 'down_hoe': [], 'left_hoe': [], 'right_hoe': [],
                           'up_axe': [], 'down_axe': [], 'left_axe': [], 'right_axe': [],
                           'up_water': [], 'down_water': [], 'left_water': [], 'right_water': []}
        for animation in self.animations.keys():

            full_path = 'graphics/character/' + animation

            self.animations[animation] = import_folder(full_path)

    def animate(self, dt):
        self.frame_index += 4*dt

        if self.frame_index >= len(self.animations[self.status]):
            self.frame_index = 0
        self.image = self.animations[self.status][int(self.frame_index)]

    def input(self):
        keys = pygame.key.get_pressed()
        self.attacking = False
        if not self.timers['tool use'].active and not self.sleep:
            #direction
            if keys[pygame.K_w]:
                self.direction.y = -1
                self.status = 'up'
            elif keys[pygame.K_s]:
                self.direction.y = 1
                self.status = 'down'
            else:
                self.direction.y = 0
            if keys[pygame.K_a]:
                self.direction.x = -1
                self.status = 'left'
            elif keys[pygame.K_d]:
                self.direction.x = 1
                self.status = 'right'
            else:
                self.direction.x = 0

            #using tools
            if keys[pygame.K_SPACE]:
                self.timers['tool use'].activate()
                self.direction = pygame.math.Vector2()
                self.frame_index = 0


            #change tool
            if keys[pygame.K_q] and not self.timers['tool delay'].active:
                self.timers['tool delay'].activate()
                self.tool_index += 1
                self.tool_index = self.tool_index if self.tool_index < len(self.tools) else 0
                self.selected_tool = self.tools[self.tool_index]


            #using seed
            if keys[pygame.K_LCTRL]:
                self.timers['seed use'].activate()
                self.direction = pygame.math.Vector2()
                self.frame_index = 0


            #change seed
            if keys[pygame.K_e] and not self.timers['seed delay'].active:
                self.timers['seed delay'].activate()
                self.seeds_index += 1
                self.seeds_index = self.seeds_index if self.seeds_index < len(self.seeds) else 0
                self.selected_seeds = self.seeds[self.seeds_index]

            if keys[pygame.K_RETURN]:
                collided_interaction_sprite = pygame.sprite.spritecollide(self, self.interaction, False)
                if collided_interaction_sprite:
                    if collided_interaction_sprite[0].name == 'Trader':
                        self.toggle_shop()
                    else:
                        self.status = 'left_idle'
                        self.sleep = True

    def get_status(self):
        #idle animation
        if self.direction.magnitude() == 0:
            self.status = self.status.split('_')[0] + '_idle'
        if self.timers['tool use'].active:
            self.status = self.status.split('_')[0] + '_' + self.selected_tool

    def update_timer(self):
        for timer in self.timers.values():
            timer.update()

    def collision(self, direction):
        for sprite in self.sprites_collisions.sprites():
            if hasattr(sprite, 'hitbox'):
                if sprite.hitbox.colliderect(self.hitbox):
                    if direction == 'horizontal':
                        if self.direction.x > 0:
                            self.hitbox.right = sprite.hitbox.left
                        if self.direction.x < 0:
                            self.hitbox.left = sprite.hitbox.right
                        self.rect.centerx = self.hitbox.centerx
                        self.pos.x = self.hitbox.centerx
                    if direction == 'vertical':
                        if self.direction.y > 0:
                            self.hitbox.bottom = sprite.hitbox.top
                        if self.direction.y < 0:
                            self.hitbox.top = sprite.hitbox.bottom
                        self.rect.centery = self.hitbox.centery
                        self.pos.y = self.hitbox.centery

    def move(self, dt):
        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()

        #horizontal
        self.pos.x += self.direction.x * self.speed * dt
        self.hitbox.centerx = round(self.pos.x)
        self.rect.centerx = self.hitbox.centerx
        self.collision('horizontal')

        #vertical
        self.pos.y += self.direction.y * self.speed * dt
        self.hitbox.centery = round(self.pos.y)
        self.rect.centery = self.hitbox.centery
        self.collision('vertical')

    def update(self, dt):
        self.input()
        self.get_status()
        self.update_timer()
        self.get_target_position()
        self.move(dt)
        self.animate(dt)
