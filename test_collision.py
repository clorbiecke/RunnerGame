# import sys, os
# # Add the helpful files directory to the system path
# directory_path = os.path.abspath('C:/000-helpful-python-files')
# if directory_path not in sys.path:
#     sys.path.append(directory_path)

# IMPORTS
import pygame
from pygame.locals import *
from pygame.math import Vector2
from screeninfo import screeninfo

import physics_objects, forces, contact
from physics_objects import *

import colors, fonts, effects, hud_components
from hud_components import *

# INITIALIZE
# initialize pygame and open window
pygame.init()
monitor = screeninfo.get_monitors()[0]
win_w, win_h = (monitor.width,monitor.height)
window = pygame.display.set_mode((win_w, win_h))

# set timing stuff
fps = 60
dt = 1/fps
clock = pygame.time.Clock()


# CONSTANTS
## Colors
bg_color = colors.black

# GLOBAL VARS
running = True

# Objects
cir = UniformCircle(density=0.01, radius=100, pos=(000,500), vel=(500, 0), avel=6000, momi=1)
# cir = Circle(radius=100, pos=(000,500), vel=(500, 0), avel=6000, momi=1, mass=100)

print(f"cir momi: {cir.momi}")
rect = UniformPolygon(density=0.01, local_points=[(0,600), (100,600), (100,0), (0,0)], pos=(1000, 300), static=True)
objects:PhysicsObject = [cir, rect]

#Hud
a_txt = Text_Box(lambda obj=cir: f"cir vel: {round(obj.vel, 1)}", (0,0), 300, 200, colors.white, colors.black, colors.black)
b_txt = Text_Box(lambda obj=rect: f"rect vel: {round(obj.vel, 1)}", (300,0), 300, 200, colors.white, colors.black, colors.black)
hud_elements = [a_txt, b_txt]

# GAME LOOP
while running:
    pygame.display.update()
    clock.tick(fps)

    # Events
    while event := pygame.event.poll():
        # Quitting game
        if (event.type == pygame.QUIT 
            or (event.type == pygame.KEYDOWN
                and event.key == pygame.K_ESCAPE)):
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            paused = not paused

    for obj in objects:
        obj.clear_force()    
    
    for obj in objects:
        obj.update(dt)

    for i in range(len(objects)):
        for j in range(i):
            friction = 1
            restitution = 1
            c:contact.Contact = contact.generate(objects[i], objects[j], restitution=restitution, friction=friction)
            if c is not None and c.bool:
                c.resolve()

    # Graphics
    window.fill(bg_color)
    for obj in objects:
        obj.draw(window)
    for el in hud_elements:
        el.draw(window)
    

