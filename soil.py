import pygame
from settings import *
from pytmx.util_pygame import load_pygame
from support import *
from random import choice, randint

class SoilTile(pygame.sprite.Sprite):
    def __init__(self, pos, surface, groups):
        super().__init__(groups)
        self.image = surface
        self.rect = self.image.get_rect(topleft = pos)
        self.z = LAYERS['soil']

class WaterTile(pygame.sprite.Sprite):
    def __init__(self, pos, surface, groups):
        super().__init__(groups)
        self.image = surface
        self.rect = self.image.get_rect(topleft = pos)
        self.z = LAYERS['soil water']

class Plant(pygame.sprite.Sprite):
    def __init__(self, typeof_plant, groups, soil, check_water):
        super().__init__(groups)
        self.typeof_plant = typeof_plant
        self.frames = import_folder(f'graphics/fruit/{typeof_plant}')
        print(self.frames)
        self.soil = soil
        self.check_water = check_water
        self.harvest = False

        self.age = 0
        self.max_age = len(self.frames) - 1
        self.grow_speed = GROW_SPEED[typeof_plant]
        print(self.age)
        self.image = self.frames[self.age]
        self.y_offset = -16 if typeof_plant == 'corn' else -8
        self.rect = self.image.get_rect(midbottom = soil.rect.midbottom + pygame.math.Vector2(0,self.y_offset))
        self.z = LAYERS['ground plant']

    def grow_seeds(self):
        if self.check_water(self.rect.center):
            self.age += self.grow_speed
            if int(self.age) > 0:
                self.z = LAYERS['main']
                self.hitbox = self.rect.copy().inflate(-26, -self.rect.height * 0.4)
            if self.age >= self.max_age:
                self.age = self.max_age
                self.harvest = True

            self.image = self.frames[int(self.age)]
            self.rect = self.image.get_rect(midbottom = self.soil.rect.midbottom + pygame.math.Vector2(0,self.y_offset))

class SoilLayer:
    def __init__(self, all_sprites, collision_sprites):
        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites
        self.soil_sprites = pygame.sprite.Group()
        self.soil_water_sprites = pygame.sprite.Group()

        self.soil_surfaces = import_folder_dictionary('graphics/soil/')
        self.soil_water_surface = import_folder('graphics/soil_water/')

        self.create_soil_grid()
        self.create_hit_rects()

        self.plants_sprites = pygame.sprite.Group()


        self.hoe = pygame.mixer.Sound('audio/hoe.wav')
        self.hoe.set_volume(0.1)
        self.water_sound = pygame.mixer.Sound('audio/water.mp3')
        self.water_sound.set_volume(0.1)
        self.plant_sound = pygame.mixer.Sound('audio/plant.wav')
        self.plant_sound.set_volume(0.1)

    def create_soil_grid(self):
        ground = pygame.image.load('graphics/world/ground.png')
        h_tiles = ground.get_width() // TILE_SIZE
        v_tiles = ground.get_height() // TILE_SIZE

        self.grid = [[[] for col in range(h_tiles)] for row in range(v_tiles)]
        for x, y, _ in load_pygame('data/map.tmx').get_layer_by_name('Farmable').tiles():
            self.grid[y][x].append('F')

    def create_hit_rects(self):
        self.hit_rects = []
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'F' in cell:
                    x = index_col * TILE_SIZE
                    y = index_row * TILE_SIZE
                    rect = pygame.Rect(x,y, TILE_SIZE, TILE_SIZE)
                    self.hit_rects.append(rect)

    def get_hit(self, point):
        for rect in self.hit_rects:
            if rect.collidepoint(point):

                self.hoe.play()
                x = rect.x // TILE_SIZE
                y = rect.y // TILE_SIZE

                if 'F' in self.grid[y][x]:
                    self.grid[y][x].append('X')
                    self.create_soil_tiles()

                    if self.raining:
                        self.raining_water_all()

    def water(self, target):
        for soil in self.soil_sprites.sprites():
            if soil.rect.collidepoint(target):

                self.water_sound.play()
                x = soil.rect.x // TILE_SIZE
                y = soil.rect.y // TILE_SIZE
                self.grid[y][x].append('W')

                image_soil_water = choice(self.soil_water_surface)
                WaterTile(soil.rect.topleft, image_soil_water, [self.all_sprites, self.soil_water_sprites])

    def harvest(self, target, inventory):
        for plant in self.plants_sprites.sprites():
            if plant.rect.collidepoint(target) and plant.age == plant.max_age:
                self.grid[plant.rect.centery // TILE_SIZE][plant.rect.centerx // TILE_SIZE].remove('P')
                inventory[plant.typeof_plant] += 1
                plant.kill()

    def raining_water_all(self):
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell and 'W' not in cell:
                    if randint(0, 10) > 3:
                        cell.append('W')
                        x = index_col * TILE_SIZE
                        y = index_row * TILE_SIZE
                        WaterTile((x,y), choice(self.soil_water_surface), [self.all_sprites, self.soil_water_sprites])

    def destroy_water(self):
        for sprite in self.soil_water_sprites.sprites():
            sprite.kill()

        for row in self.grid:
            for cell in row:
                if 'W' in cell:
                    cell.remove('W')

    def check_water(self, pos):
        x = pos[0] // TILE_SIZE
        y = pos[1] // TILE_SIZE
        cell = self.grid[y][x]
        is_water = 'W' in cell
        return is_water

    def plant_seed(self, target, seed):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target):
                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE
                if 'X' in self.grid[y][x]:
                    if 'P' not in self.grid[y][x]:
                        self.plant_sound.play()
                        self.grid[y][x].append('P')
                        Plant(seed, [self.all_sprites, self.plants_sprites, self.collision_sprites] , soil_sprite, self.check_water)
                        return True

    def create_soil_tiles(self):
        self.soil_sprites.empty()
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell:
                    t = 'X' in self.grid[index_row - 1][index_col]
                    b = 'X' in self.grid[index_row + 1][index_col]
                    r = 'X' in row[index_col + 1]
                    l = 'X' in row[index_col - 1]

                    tile_type = 'o'

                    if all((l, r, b, t)): tile_type = 'x'
                    if l and not any((t,r,b)): tile_type = 'r'
                    if r and not any((t,l,b)): tile_type = 'l'
                    if l and r and not any((t,b)): tile_type = 'lr'

                    if t and not any((r,l,b)): tile_type = 'b'
                    if b and not any((r,l,t)): tile_type = 't'
                    if t and b and not any((r,l)): tile_type = 'tb'

                    if l and b and not any((t,r)): tile_type = 'tr'
                    if r and b and not any((t,l)): tile_type = 'tl'
                    if l and t and not any((b,r)): tile_type = 'br'
                    if r and t and not any((b,l)): tile_type = 'bl'

                    if all((t, b, r)) and not l: tile_type = 'tbr'
                    if all((t, b, l)) and not r: tile_type = 'tbl'
                    if all((t, r, l)) and not b: tile_type = 'lrb'
                    if all((b, r, l)) and not t: tile_type = 'lrt'

                    SoilTile(pos = (index_col * TILE_SIZE, index_row * TILE_SIZE),
                             surface = self.soil_surfaces[tile_type],
                             groups = [self.all_sprites, self.soil_sprites])

    def update_plant(self):
        for plant in self.plants_sprites.sprites():
            plant.grow_seeds()