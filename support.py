from os import walk
import pygame

def import_folder(path):
    surface_list = []

    for _, __, image_files in walk(path):
        for image in image_files:
            full_path = path + '/' + image

            image_surface = pygame.image.load(full_path).convert_alpha()
            surface_list.append(image_surface)

    return surface_list

def import_folder_dictionary(path):
    surface_dictionary = {}

    for _, __, image_files in walk(path):
        for image in image_files:
            full_path = path + '/' + image
            image_surface = pygame.image.load(full_path).convert_alpha()

            surface_dictionary[image.split('.')[0]] = image_surface

    return surface_dictionary