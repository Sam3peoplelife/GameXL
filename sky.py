import pygame
from settings import *
from support import *
from sprites import Generic
from random import randint, choice

class Sky:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.full_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.start_color = [255,255,255]
        self.end_color = (38, 101, 185)

    def display(self, dt):
        for index, value in enumerate(self.end_color):
            if self.start_color[index] > value:
                self.start_color[index] -= 1.5 * dt
        self.full_surface.fill(self.start_color)
        self.display_surface.blit(self.full_surface, (0,0), special_flags=pygame.BLEND_RGBA_MULT)


class Drop(Generic):
    def __init__(self, pos, surface, moving, groups, z):
        super().__init__(pos,surface, groups, z)
        self.lifetime = randint(400, 500)
        self.start_time = pygame.time.get_ticks()

        self.moving = moving
        if self.moving:
            self.pos = pygame.math.Vector2(self.rect.topleft)
            self.direction = pygame.math.Vector2(-3,5)
            self.speed = randint(200, 300)

    def update(self, dt):
        if self.moving:
            self.pos += self.direction * self.speed * dt
            self.rect.topleft = (round(self.pos.x), round(self.pos.y))

        if self.lifetime <= pygame.time.get_ticks() - self.start_time:
            self.kill()

class Rain:
    def __init__(self, all_sprites):
        self.all_sprites = all_sprites
        self.drop_of_rain = import_folder('graphics/rain/drops/')
        self.rain_floor = import_folder('graphics/rain/floor/')
        self.size_w, self.size_h = pygame.image.load('graphics/world/ground.png').get_size()

    def create_floor(self):
        Drop(pos = (randint(0,self.size_w), randint(0, self.size_h)),
             surface = choice(self.rain_floor),
             moving = False,
             groups = self.all_sprites,
             z = LAYERS['rain floor'])

    def create_drops(self):
        Drop(pos=(randint(0, self.size_w), randint(0, self.size_h)),
             surface=choice(self.drop_of_rain),
             moving=True,
             groups=self.all_sprites,
             z=LAYERS['rain drops'])

    def update(self):
        self.create_drops()
        self.create_floor()