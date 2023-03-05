import pygame
from settings import *
from timer import Timer

class Menu:
    def __init__(self, player, toggle_menu):
        self.player = player
        self.toggle_menu = toggle_menu
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font(None, 30)

        self.width = 400
        self.space = 10
        self.padding = 8

        self.color = [172, 223, 122]

        self.options = list(self.player.inventory.keys()) + list(self.player.seed_inventory.keys()) + list(self.player.special.keys())
        self.sell_border = len(self.player.inventory) - 1
        self.setup()

        self.shop_index = 0

        self.timer = Timer(250)

    def display_money(self):
        text_surface = self.font.render(f'${self.player.money}', False, 'white')
        text_rect = text_surface.get_rect(midbottom = (SCREEN_WIDTH/2, SCREEN_HEIGHT - 20))

        pygame.draw.rect(self.display_surface, self.color, text_rect.inflate(10,10), 0, 6)
        self.display_surface.blit(text_surface, text_rect)

    def setup(self):
        self.text_surfaces = []
        self.height = 0
        for item in self.options:
            text_surface = self.font.render(item, False, 'white')
            self.text_surfaces.append(text_surface)
            self.height += text_surface.get_height() + self.padding*2


        self.height += (len(self.text_surfaces) - 1) * self.space
        self.main_rect = pygame.Rect(SCREEN_WIDTH / 2 - self.width / 2, SCREEN_HEIGHT / 2 - self.height / 2, self.width, self.height)
        self.text = self.font.render('text', False, 'white')

    def input(self):
        keys = pygame.key.get_pressed()
        self.timer.update()

        if keys[pygame.K_ESCAPE]:
            self.toggle_menu()
        if not self.timer.active:
            if keys[pygame.K_UP]:
                self.shop_index -= 1
                self.timer.activate()
            if keys[pygame.K_DOWN]:
                self.shop_index += 1
                self.timer.activate()
            if keys[pygame.K_SPACE]:
                self.timer.activate()
                current_item = self.options[self.shop_index]
                if self.shop_index <= self.sell_border:
                    if self.player.inventory[current_item] > 0:
                        self.player.inventory[current_item] -= 1
                        self.player.money += SALE_PRICES[current_item]
                else:
                    if self.player.money >= PURCHASE_PRICES[current_item]:
                        if self.shop_index <= self.sell_border + 3:
                            self.player.money -= PURCHASE_PRICES[current_item]
                            self.player.seed_inventory[current_item] += 1
                        else:
                            if self.player.special[current_item] == 0:
                                self.player.money -= PURCHASE_PRICES[current_item]
                                self.player.special[current_item] += 1
                                if current_item == 'autoharvest':
                                    self.player.autoharvest = True
                                else:
                                    self.player.tools.append(current_item)



        if self.shop_index < 0:
            self.shop_index = len(self.options) - 1
        if self.shop_index > len(self.options) - 1:
            self.shop_index = 0

    def entry(self, text_surface, amount, top, selected):
        background_rect = pygame.Rect(self.main_rect.left, top, self.width, text_surface.get_height() + self.padding*2)
        pygame.draw.rect(self.display_surface, self.color, background_rect, 0, 4)

        text_rect = text_surface.get_rect(midleft = (self.main_rect.left + 20, background_rect.centery))
        self.display_surface.blit(text_surface, text_rect)

        amount_surface = self.font.render(str(amount), False, 'white')
        amount_rect = amount_surface.get_rect(midright = (self.main_rect.right - 20, background_rect.centery))
        self.display_surface.blit(amount_surface, amount_rect)

        if selected:
            pygame.draw.rect(self.display_surface, 'gold', background_rect, 4, 4)
            pos = self.text.get_rect(midleft = (self.main_rect.left + 150, background_rect.centery))
            if self.shop_index <= self.sell_border:
                self.display_surface.blit(self.font.render(f'sell: ${SALE_PRICES[self.options[self.shop_index]]}', False, 'white'), pos)
            else:
                self.display_surface.blit(self.font.render(f'buy: ${PURCHASE_PRICES[self.options[self.shop_index]]}', False, 'white'), pos)

    def update(self):
        self.input()
        self.display_money()
        pygame.draw.rect(self.display_surface, self.color, self.main_rect)
        for index, text_surface in enumerate(self.text_surfaces):
            top = self.main_rect.top + index * (text_surface.get_height() + self.padding*2 + self.space)
            amount_list = list(self.player.inventory.values()) + list(self.player.seed_inventory.values()) + list(self.player.special.values())

            self.entry(text_surface, amount_list[index], top, self.shop_index == index)


