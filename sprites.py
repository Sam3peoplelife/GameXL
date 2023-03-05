import pygame
from settings import *
from random import randint, choice
from timer import Timer

class Generic(pygame.sprite.Sprite):
    def __init__(self, pos, surface, groups, z = LAYERS['main']):
        super().__init__(groups)
        self.image = surface
        self.rect = self.image.get_rect(topleft = pos)
        self.z = z
        self.hitbox = self.rect.copy().inflate(-self.rect.width*0.2, -self.rect.height*0.7)

class Interaction(Generic):
    def __init__(self, pos, size, groups, name):
        surface = pygame.Surface(size)
        super().__init__(pos, surface, groups)
        self.name = name

class Water(Generic):
    def __init__(self, pos, frames, groups):
        self.frames = frames
        self.frames_index = 0

        super().__init__(pos = pos,
                         surface = self.frames[self.frames_index],
                         groups = groups,
                         z = LAYERS['water'])

    def animate(self, dt):
        self.frames_index += 4 * dt

        if self.frames_index >= len(self.frames):
            self.frames_index = 0
        self.image = self.frames[int(self.frames_index)]

    def update(self, dt):
        self.animate(dt)

class WFlower(Generic):
    def __init__(self, pos, surface, groups):
        super().__init__(pos, surface, groups)
        self.hitbox = self.rect.copy().inflate(-20,-self.rect.height*0.9)

class Particles(Generic):
    def __init__(self, pos, surface, groups, z, duration = 200):
        super().__init__(pos, surface, groups, z)
        self.start_time = pygame.time.get_ticks()
        self.duration = duration

        mask_surface = pygame.mask.from_surface(self.image)
        new_surface = mask_surface.to_surface()
        new_surface.set_colorkey((0,0,0))
        self.image = new_surface

    def update(self, dt):
        cur_time = pygame.time.get_ticks()
        if cur_time - self.start_time > self.duration:
            self.kill()

class Tree(Generic):
    def __init__(self, pos, surface, groups, name, player_add):
        super().__init__(pos, surface, groups)

        self.apple_surface = pygame.image.load('graphics/fruit/apple.png')
        self.apple_pos = APPLE_POS[name]
        self.sprites_of_apple = pygame.sprite.Group()
        self.create_fruits()

        self.health = 5
        self.alive = True
        self.stump_surface = pygame.image.load(f'graphics/stumps/{"small" if name == "Small" else "large"}.png').convert_alpha()
        self.invul_timer = Timer(200)

        self.player_add = player_add


        self.axe_sound = pygame.mixer.Sound('audio/axe.mp3')

    def damage(self):
        self.health -= 1
        self.axe_sound.play()
        if len(self.sprites_of_apple.sprites()) > 0:
            random_apple = choice(self.sprites_of_apple.sprites())
            Particles(pos = random_apple.rect.topleft, surface = random_apple.image,
                      groups = self.groups()[0], z = LAYERS['fruit'])
            self.player_add('apple')
            random_apple.kill()

    def check_death(self):
        if self.health <= 0:
            Particles(pos=self.rect.topleft, surface=self.image,
                      groups=self.groups()[0], z=LAYERS['main'], duration=200)
            self.image = self.stump_surface
            self.rect = self.image.get_rect(midbottom = self.rect.midbottom)
            self.hitbox = self.rect.copy().inflate(-5, -self.rect.height*0.7)
            self.player_add('wood')
            self.alive = False

    def update(self, dt):
        if self.alive:
            self.check_death()

    def create_fruits(self):
        for pos in self.apple_pos:
            if randint(0,10) < 2:
                x = pos[0] + self.rect.left
                y = pos[1] + self.rect.top
                Generic(pos = (x,y),
                        surface = self.apple_surface,
                        groups = [self.sprites_of_apple, self.groups()[0]],
                        z = LAYERS['fruit'])
