import pygame
from settings import *
from player import Player
from overlay import Overlay
from sprites import Generic, Water, WFlower, Tree, Interaction, Particles
from pytmx.util_pygame import load_pygame
from support import *
from transition import Transition
from soil import SoilLayer
from sky import Rain, Sky
from random import randint
from menu import Menu
from enemy import Enemy
import button
import sys

class Level:
    def __init__(self):
        # get the display surface
        self.display_surface = pygame.display.get_surface()

        #sprite groups
        self.all_sprites = CameraGroup()
        self.collision_sprites = pygame.sprite.Group()
        self.sprites_of_trees = pygame.sprite.Group()
        self.interaction_sprites = pygame.sprite.Group()

        self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites)

        self.setup()
        self.overlay = Overlay(self.player)
        self.transition = Transition(self.restart, self.player)

        self.rain = Rain(self.all_sprites)
        self.raining_weather = randint(0,10) > 4
        self.soil_layer.raining = self.raining_weather

        self.sky = Sky()

        self.shop_active = False
        self.menu = Menu(self.player, self.toggle_shop)


        self.spawn_area = []
        for x, y, _ in load_pygame('data/map.tmx').get_layer_by_name('Farmable').tiles():
            self.spawn_area.append((x * TILE_SIZE, y * TILE_SIZE))
        pos_enemy = self.spawn_enemy()
        self.enemy = Enemy(pos_enemy, self.all_sprites, self.collision_sprites, self.sprites_of_trees,
                           self.interaction_sprites, self.soil_layer, self.player.pos)

        self.pause = False
        self.start = False
        self.font = pygame.font.Font(None, 60)
        self.buttons()
        self.instruction = False


        self.succes = pygame.mixer.Sound('audio/success.wav')
        self.succes.set_volume(0.1)
        self.main_sound = pygame.mixer.Sound('audio/music.mp3')
        self.main_sound.play(loops = -1)
        self.main_sound.set_volume(0.05)

    def setup(self):
        data_tmx = load_pygame('data/map.tmx')

        for layer in ['HouseFloor', 'HouseFurnitureBottom']:
            for x,y,surface in data_tmx.get_layer_by_name(layer).tiles():
                Generic((x * TILE_SIZE,y * TILE_SIZE), surface, self.all_sprites, LAYERS['house bottom'])

        for layer in ['HouseWalls', 'HouseFurnitureTop']:
            for x,y,surface in data_tmx.get_layer_by_name(layer).tiles():
                Generic((x * TILE_SIZE,y * TILE_SIZE), surface, self.all_sprites, LAYERS['main'])

        for x, y, surface in data_tmx.get_layer_by_name('Fence').tiles():
            Generic((x * TILE_SIZE, y * TILE_SIZE), surface, [self.all_sprites, self.collision_sprites], LAYERS['main'])

        frames_of_water = import_folder('graphics/water')
        for x, y, surface in data_tmx.get_layer_by_name('Water').tiles():
            Water((x * TILE_SIZE, y * TILE_SIZE), frames_of_water, self.all_sprites)

        for obj in data_tmx.get_layer_by_name('Decoration'):
            WFlower((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites])

        for obj in data_tmx.get_layer_by_name('Trees'):
            Tree(pos = (obj.x, obj.y),
                 surface = obj.image,
                 groups = [self.all_sprites, self.collision_sprites, self.sprites_of_trees],
                 name = obj.name,
                 player_add = self.player_add)

        for x, y, surface in data_tmx.get_layer_by_name('Collision').tiles():
            Generic((x * TILE_SIZE, y * TILE_SIZE), pygame.Surface((TILE_SIZE, TILE_SIZE)), self.collision_sprites)

        for obj in data_tmx.get_layer_by_name('Player'):
            if obj.name == 'Start':
                self.start_pos = (obj.x, obj.y)
                self.player = Player((obj.x, obj.y),
                                     self.all_sprites,
                                     self.collision_sprites,
                                     self.sprites_of_trees,
                                     self.interaction_sprites,
                                     self.soil_layer,
                                     self.toggle_shop)

            if obj.name == 'Bed':
                Interaction((obj.x, obj.y), (obj.width, obj.height), self.interaction_sprites, obj.name)

            if obj.name == 'Trader':
                Interaction((obj.x, obj.y), (obj.width, obj.height), self.interaction_sprites, obj.name)
        Generic(pos = (0,0),
                surface = pygame.image.load('graphics/world/ground.png').convert_alpha(),
                groups = self.all_sprites,
                z = LAYERS['ground'])

    def player_add(self, item):
        self.player.inventory[item] += 1
        self.succes.play()

    def toggle_shop(self):
        self.shop_active = not self.shop_active

    def restart(self):
        self.soil_layer.update_plant()

        self.soil_layer.destroy_water()
        self.raining_weather = randint(0, 10) > 3
        self.soil_layer.raining = self.raining_weather


        for tree in self.sprites_of_trees.sprites():
            for apple in tree.sprites_of_apple.sprites():
                apple.kill()
            if tree.alive:
                tree.create_fruits()

        self.sky.start_color = [255, 255, 255]

    def plant_collision(self):
        if self.soil_layer.plants_sprites:
            for plant in self.soil_layer.plants_sprites.sprites():
                if plant.harvest and plant.rect.colliderect(self.player.hitbox) and self.player.autoharvest:
                    self.player_add(plant.typeof_plant)
                    plant.kill()
                    Particles(plant.rect.topleft, plant.image, self.all_sprites, LAYERS['main'])
                    self.soil_layer.grid[plant.rect.centery // TILE_SIZE][plant.rect.centerx // TILE_SIZE].remove('P')

    def spawn_enemy(self):
        pos_enemy = self.spawn_area[randint(0, len(self.spawn_area) - 1)]
        return pos_enemy

    def kill_enemy(self):
        if self.enemy.rect.collidepoint(self.player.target_position) and self.player.attacking:
            self.player.attacking = False
            self.player.money += 10
            self.enemy.alived = False
            self.enemy.pos.x = -300
            self.enemy.pos.y = -300
            self.succes.play()
            Particles(self.enemy.rect.topleft, self.enemy.image, self.all_sprites, LAYERS['main'])

        if self.enemy.alived and self.enemy.respawned:
            self.enemy.respawned = False
            enemy_pos = self.spawn_enemy()
            self.enemy.pos.x = enemy_pos[0]
            self.enemy.pos.y = enemy_pos[1]

    def destroy_plant(self):
        for plant in self.soil_layer.plants_sprites.sprites():
            if plant.harvest:
                if plant.rect.colliderect(self.enemy.rect):
                    plant.kill()
                    Particles(plant.rect.topleft, plant.image, self.all_sprites, LAYERS['main'])
                    self.soil_layer.grid[plant.rect.centery // TILE_SIZE][plant.rect.centerx // TILE_SIZE].remove('P')

    def buttons(self):
        pos = [self.display_surface.get_width() // 2 - 250,
                                       self.display_surface.get_height() // 2 - 30]

        image_pause = pygame.image.load('graphics/buttons/pause.png')
        image_pause1 = pygame.image.load('graphics/buttons/pause1.png')
        image_quit = pygame.image.load('graphics/buttons/quit.png')
        image_restart = pygame.image.load('graphics/buttons/restart.png')
        image_mute = pygame.image.load('graphics/buttons/mute.png')
        image_unmute = pygame.image.load('graphics/buttons/unmute.png')
        image_setting = pygame.image.load('graphics/buttons/inst.png')
        self.button_pause = button.Button(pos[0], pos[1], image_pause, 4)
        self.button_pause1 = button.Button(self.display_surface.get_width()//2 + 570, self.display_surface.get_height()//2 + 290, image_pause1, 4)
        self.button_quit = button.Button(pos[0] + 100, pos[1], image_quit, 4)
        self.button_restart = button.Button(pos[0] + 200, pos[1], image_restart, 4)
        self.button_mute = button.Button(pos[0] + 300, pos[1], image_mute, 4)
        self.button_unmute = button.Button(pos[0] + 400, pos[1], image_unmute, 4)
        self.button_inst = button.Button(self.display_surface.get_width()//2 + 570, self.display_surface.get_height()//2 + 220, image_setting, 4)

    def run(self, dt):
        self.display_surface.fill('black')
        self.all_sprites.customize_draw(self.player)
        self.main_surf = pygame.Rect((self.display_surface.get_width()//2 - 400,
                                     self.display_surface.get_height() // 2 - 220,
                                     self.display_surface.get_width()//2 + 150,
                                     self.display_surface.get_height() // 2 + 80))


        if self.start and not self.pause and not self.instruction:
            if self.shop_active:
                self.menu.update()
            else:
                if self.button_pause1.draw(self.display_surface):
                    self.pause = True
                if self.button_inst.draw(self.display_surface):
                    self.instruction = True
                self.all_sprites.update(dt)
                self.plant_collision()
                self.enemy.update_enemy(dt)
                self.kill_enemy()
                self.destroy_plant()

            self.overlay.display()

            if self.raining_weather and not self.shop_active:
                self.rain.update()

            self.sky.display(dt)

            if self.player.sleep:
                self.transition.play()
        elif self.pause:

            pygame.draw.rect(self.display_surface, [172, 223, 122], self.main_surf)
            pygame.draw.rect(self.display_surface, 'gold', self.main_surf, 4, 4)

            if self.button_pause.draw(self.display_surface):
                self.pause = False
            if self.button_restart.draw(self.display_surface):
                self.player.pos.x = self.start_pos[0]
                self.player.pos.y = self.start_pos[1]
                self.pause = False
            if self.button_quit.draw(self.display_surface):
                pygame.quit()
                sys.exit()
            if self.button_mute.draw(self.display_surface):
                pygame.mixer.pause()
            if self.button_unmute.draw(self.display_surface):
                pygame.mixer.unpause()
        elif not self.start:
            pygame.draw.rect(self.display_surface, [172, 223, 122], self.main_surf)
            pygame.draw.rect(self.display_surface, 'gold', self.main_surf, 4, 4)
            self.display_surface.blit(self.font.render('Peaceful world', False, 'white'),
                                      (self.display_surface.get_width() // 2 - 166, self.display_surface.get_height() // 2 - 165))

            if self.button_pause.draw(self.display_surface):
                self.start = True
            if self.button_restart.draw(self.display_surface):
                self.player.pos.x = self.start_pos[0]
                self.player.pos.y = self.start_pos[1]
                self.start = True
            if self.button_quit.draw(self.display_surface):
                pygame.quit()
                sys.exit()
            if self.button_mute.draw(self.display_surface):
                pygame.mixer.pause()
            if self.button_unmute.draw(self.display_surface):
                pygame.mixer.unpause()
        elif self.instruction:
            pygame.draw.rect(self.display_surface, [172, 223, 122], self.main_surf)
            pygame.draw.rect(self.display_surface, 'gold', self.main_surf, 4, 4)
            if self.button_inst.draw(self.display_surface):
                self.instruction = False
            self.display_surface.blit(self.font.render('Space/Ctrl - use tool/seed', False, 'white'),
                                      (self.display_surface.get_width() // 2 - 270,
                                       self.display_surface.get_height() // 2 - 200))
            self.display_surface.blit(self.font.render('Enter - Sleep/Market', False, 'white'),
                                      (self.display_surface.get_width() // 2 - 220,
                                       self.display_surface.get_height() // 2 - 140))
            self.display_surface.blit(self.font.render('Q/E - change tool/seed', False, 'white'),
                                      (self.display_surface.get_width() // 2 - 235,
                                       self.display_surface.get_height() // 2 - 80))
            self.display_surface.blit(self.font.render('Escape - leave market', False, 'white'),
                                      (self.display_surface.get_width() // 2 - 220,
                                       self.display_surface.get_height() // 2 - 20))
            self.display_surface.blit(self.font.render('The seeds grow up', False, 'white'),
                                      (self.display_surface.get_width() // 2 - 200,
                                       self.display_surface.get_height() // 2 + 40))
            self.display_surface.blit(self.font.render('while you sleep', False, 'white'),
                                      (self.display_surface.get_width() // 2 - 160,
                                       self.display_surface.get_height() // 2 + 100))
            self.display_surface.blit(self.font.render('Protect seeds from slime with axe', False, 'white'),
                                      (self.display_surface.get_width() // 2 - 340,
                                       self.display_surface.get_height() // 2 + 160))

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.math.Vector2()

    def customize_draw(self, player):
        self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2
        self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2

        for layer in LAYERS.values():
            for sprite in sorted(self.sprites(), key = lambda sprite: sprite.rect.centery):
                if sprite.z == layer:
                    offset_rect = sprite.rect.copy()
                    offset_rect.center -= self.offset
                    self.display_surface.blit(sprite.image, offset_rect)
