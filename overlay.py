import pygame
from settings import *

class Overlay:
    def __init__(self, player):
        self.display_surface = pygame.display.get_surface()
        self.player = player


        self.path = 'graphics/overlay/'

        self.seeds_surface = {seed:pygame.image.load(f'{self.path}{seed}.png').convert_alpha() for seed in player.seeds}

    def display(self):
        self.get_tool()

        tool_surface = self.tools_surface[self.player.selected_tool]
        tool_rect = tool_surface.get_rect(midbottom = OVERLAY_POSITIONS['tool'])
        self.display_surface.blit(tool_surface, tool_rect)

        seeds_surface = self.seeds_surface[self.player.selected_seeds]
        seeds_rect = seeds_surface.get_rect(midbottom=OVERLAY_POSITIONS['seed'])
        self.display_surface.blit(seeds_surface, seeds_rect)

    def get_tool(self):
        self.tools_surface = {tool: pygame.image.load(f'{self.path}{tool}.png').convert_alpha() for tool in self.player.tools}