import pygame
from settings import *
from support import import_folder
from timer import Timer
from sprites import Particles

class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, group, collision_sprites, sprites_of_trees, interaction, soil_layer, target):
        super().__init__(group)

        self.import_assets_enemy()
        self.frame_index = 0
        self.image = self.animations['enemy'][self.frame_index]


        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.copy().inflate((-46, -30))
        self.z = LAYERS['main']

        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 50

        self.sprites_collisions = collision_sprites
        self.sprites_of_trees = sprites_of_trees
        self.interaction = interaction
        self.soil_layer = soil_layer

        self.alived = True
        self.respawned = False

        self.timer = Timer(20000, self.respawn_enemy)
        self.target = target

    def import_assets_enemy(self):
        self.animations = {'enemy': []}
        for animation in self.animations.keys():
            full_path = 'graphics/' + animation
            self.animations[animation] = import_folder(full_path)

    def animate_enemy(self, dt):
        self.frame_index += 4*dt

        if self.frame_index >= len(self.animations['enemy']):
            self.frame_index = 0
        self.image = self.animations['enemy'][int(self.frame_index)]

    def move_enemy(self, dt):
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()

            # horizontal
            self.pos.x += self.direction.x * self.speed * dt
            self.hitbox.centerx = round(self.pos.x)
            self.rect.centerx = self.hitbox.centerx
            self.collision_enemy('horizontal')

            # vertical
            self.pos.y += self.direction.y * self.speed * dt
            self.hitbox.centery = round(self.pos.y)
            self.rect.centery = self.hitbox.centery
            self.collision_enemy('vertical')

    def action(self):
        self.direction = self.get_distance()[1]

    def collision_enemy(self, direction):
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

    def get_distance(self):
        distance = (self.target - self.pos).magnitude()

        if distance > 0:
            self.direction = (self.target - self.pos).normalize()
        else:
            self.direction = pygame.math.Vector2()

        return (distance, self.direction)

    def check_death(self):
        if not self.alived and not self.timer.active:
            self.timer.activate()

    def respawn_enemy(self):
        self.alived = True
        self.respawned = True

    def update_enemy(self,dt):
        self.move_enemy(dt)
        self.action()
        self.animate_enemy(dt)
        self.check_death()
        self.timer.update()



