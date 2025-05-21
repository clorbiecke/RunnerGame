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
from enum import Enum
from itertools import chain
import copy

import physics_objects, forces, contact
from physics_objects import *

from game_objects import *

from contact import Contact

import colors, fonts, effects, hud_components
from hud_components import *

# INITIALIZE
# initialize pygame and open window
pygame.init()
monitor = screeninfo.get_monitors()[0]
win_w, win_h = (monitor.width,monitor.height)
window = pygame.display.set_mode((win_w, win_h))

# set timing stuff
fps = 120
dt = 1/fps
clock = pygame.time.Clock()


# CONSTANTS
## Colors
bg_color = colors.black

# GLOBAL VARS
running = True

# OBJECTS
objects:list[PhysicsObject] = []

# Player
max_spd = 800
player = Player(50, pos=(win_h*0.9-50, 500), mass=10)
# player.mass = 10
# print(f"mass: {player.mass}")
player_max_avel = (360 * max_spd) / player.circum
class Blast(UniformCircle):
    # fires from cannon, then explodes, adding an impulse to objects it collides
    #   with proportional to their distance from the center of the explosion
    def __init__(self, blast_radius = 200, blast_color=colors.alpha(colors.cyan, 180), blast_outline_color=colors.alpha(colors.orange, 180), blast_outline_width=3, density=0.01, radius = 25, fill_color = colors.cyan, outline_color = colors.blue, outline_width=1, name="blast", **kwargs):
        super().__init__(density, radius, fill_color=fill_color, outline_color=outline_color, outline_width=outline_width, name=name, **kwargs)
        self.blast_radius = blast_radius
        self.blast_color = blast_color
        self.blast_outline_color = blast_outline_color
        self.blast_outline_width = blast_outline_width
        self.blast_size = 1.0
        self.blast_area = self.blast_radius**2 * math.pi
        self.blast_fade_time = 0.4
        self.exploding = False
        self.max_impulse = 8000
        
        global bullets
        bullets.append(self)

    def update(self, dt=0):
        # print("updating blast...")
        return super().update(dt)
    
    def draw(self, surface:Surface):
        # print("drawing...")
        if self.exploding:
            radius = self.blast_radius*self.blast_size
            s:Surface = Surface((abs(radius*2),abs(radius*2)), pygame.SRCALPHA)

            pygame.draw.circle(s, self.blast_color, (radius, radius), radius, 0)
            if self.blast_outline_width:
                pygame.draw.circle(s, self.blast_outline_color, (radius, radius), radius, self.blast_outline_width)
            window.blit(s, self.pos-Vector2(radius, radius))
        else:
            return super().draw(surface)
    
    def explode(self):
        if self.update_explosion not in self.on_update:
            # print("exploding!")
            self.exploding = True
            self.on_update.append(self.update_explosion)
            self.static = True
            self.fill_color = self.blast_color
            self.outline_color = self.blast_outline_color
            self.outline_width = self.blast_outline_width
            

    def update_explosion(self, dt=0):
        # print("updating explosion...")
        if self.blast_size < 1.0:
            # print("no more generating contacts")
            self.generate_contacts = False
        self.blast_size -= min(dt/self.blast_fade_time, self.blast_size)
        self.radius = self.blast_radius * (1-(1-self.blast_size))**2
        if self.blast_size <= 0:
            global bullets
            bullets.remove(self)




def fire_cannon():
    if player.cannon.cooldown > 0: return
    # print("firing cannon")
    player.cannon.cooldown = player.cannon.min_fire_interval

    dir = (player.cannon.barrel_end-player.pos).normalize()
    # print(f"firing dir: {dir}, cannon angle: {player.cannon.angle}")
    vel = dir * (2000 + max(0, player.vel*dir))
    pos = player.cannon.barrel_end
    bullet = Blast(density=0.01, radius=25*player.cannon.size, fill_color=colors.cyan, outline_color=colors.blue, name="bullet", pos=pos, vel=vel)
    # bullets.append(bullet)

def fire_laser():
    if player.laser.cooldown <= 0:
        player.laser.firing = True
        # print("firing laser")
        player.laser.width=50
        player.laser.cooldown = player.laser.recharge


# Ground
ground = Wall((win_w, win_h*0.9), (0, win_h*0.9), width=5)

# Obstacles
obstacles:list[UniformPolygon] = []
poly = UniformPolygon(0.001, [(0,0), (80,0), (80,400), (0,400)], (830, 800), 0)
# print(f"poly mass = {poly.mass}")
obstacles += [poly]



def add_obstacle(obj:UniformPolygon):
    obstacles.append(obj)



# TEMP
shapes:list[UniformPolygon] = []
shape_density = 0.001
shape_color = colors.grey
shape_outline = colors.contrast_lighten_darken(shape_color)
shape_spawn_base_cooldown = 2
shape_spawn_cooldown = shape_spawn_base_cooldown

shape_options:list[UniformPolygon] = [
    UniformPolygon(shape_density, [(x*3,y*3) for x,y in [(30,0), (0,52), (-30,0)]], fill_color=shape_color, outline_color=shape_outline, name="shape_triangle"),
    UniformPolygon(shape_density, [(x*3,y*3) for x,y in [(30,30), (-30,30), (-30,-30), (30,-30)]], fill_color=shape_color, outline_color=shape_outline, name="shape_square"),
    UniformPolygon(shape_density, [(x*3,y*3) for x,y in [(30,0), (0,52), (-30,0), (0, -52)]], fill_color=shape_color, outline_color=shape_outline, name="shape_rhombus"),
    UniformPolygon(shape_density, [(x*3,y*3) for x,y in [(0, 30), (26, 15), (26,-15), (0,-30), (-26, -15), (-26, 15)]], fill_color=shape_color, outline_color=shape_outline, name="shape_hexagon"),
    UniformPolygon(shape_density, [(x*3,y*3) for x,y in [(40,20), (50, -20), (0, -30), (-50, -20), (-40,20)]], fill_color=shape_color, outline_color=shape_outline, name="shape_pentagon")
]
def rand_spawn_pos() -> Vector2:
    return Vector2(random.uniform(win_w*0.1, win_w*0.9), -100)

def rand_spawn_vel() -> Vector2:
    spd = random.randrange(100,200)
    angle = random.uniform(60.0,120.0)
    return Vector2(1,0).rotate(angle) * spd

# num of objects to spawn per frame
def get_spawn_rate() -> float:
    # 1 per 2 sec, * 1.1^gamestage
    return (1.1)/(2*fps)
def get_spawn_interval() -> float:
    return 2/(1.1)

# reduce cooldown and spawn objects
def tick_spawn(dt=1/60):
    global shape_spawn_cooldown, fps
    shape_spawn_cooldown -= dt
    while shape_spawn_cooldown <= 0:
        spawn_shape(False)
        add_cool = get_spawn_interval() * 1.0#random.uniform(0.5, 1.0)
        shape_spawn_cooldown += add_cool
        # print(f"Spawn Interval: {get_spawn_interval()}, Cooldown: {shape_spawn_cooldown}, add_cool: {add_cool}")

def spawn_shape(reset_cooldown = True):
    # reset cooldown if asked
    if reset_cooldown:
        global shape_spawn_cooldown
        shape_spawn_cooldown = get_spawn_interval()
    # randomly determine which shape to spawn
    n = len(shape_options)
    if n == 0: return False
    index = random.randint(0, n-1)
    shape:UniformPolygon = copy.copy(shape_options[index])
    # set value; rand spawn pos, vel, and angle; and name
    shape.pos = rand_spawn_pos()
    shape.vel = rand_spawn_vel()
    shape.angle = random.uniform(0.0,360.0)
    # print(f"spawned shape. vel: {shape.vel}, pos: {shape.pos}")
    # add to shapes and increment count
    obstacles.append(shape)
    return shape
# END TEMP


# Bullets
bullets:list[Blast|Circle] = []

# Functions
def process_collisions():
    global bullets, obstacles, player
    for bullet in bullets:
        for obj in get_physics_objects([[player], bullets]):
            if obj is bullet: continue
            c:Contact = contact.generate(bullet, obj)
            if c is not None and c.bool:
                # print(f"Exploding = {bullet.exploding}")
                if bullet.exploding == False:
                    c.resolve()
                    bullet.explode()
                else:
                    # print(f"mass: {obj.mass}")
                    r = c.overlap/bullet.blast_radius
                    n = (obj.pos-bullet.pos).normalize()
                    v = bullet.vel-obj.vel
                    Jn = -2*v*n + r*bullet.max_impulse
                    impulse = Jn*n
                    ovel = Vector2(obj.vel)
                    # print(f"Exploding.  obj.vel: {obj.vel} bullet.vel: {bullet.vel}, adding impulse: {impulse}, r: {r}, impulse mag: {impulse.magnitude()}")
                    obj.add_impulse(impulse)
                    # print(f"obj new vel: {obj.vel}, delta vel mag = {(obj.vel-ovel).magnitude()}")

    obs_plr = obstacles+[player]
    for obj in obs_plr:
        c:Contact = contact.generate(obj, ground)
        if c.bool:
            restitution = 0.1
            rebound = 700 if (jumping and obj is player) else 0
            friction = 0.8 #if obj is player else 0.4
            c.resolve(restitution, rebound, friction)
    
    for i in range(len(obs_plr)):
        for j in range(i):
            c:Contact = contact.generate(obs_plr[i], obs_plr[j])
            if c.bool:
                restitution = 0.2
                friction = 0.6
                c.resolve(restitution, None, friction)      

    if player.laser.visible:
        laser_hit = None
        dist = math.inf
        origin = player.cannon.barrel_end
        direction = (player.cannon.barrel_end-player.pos).normalize()
        magnitude = 5000
        for obs in get_collision_objects():
            rc:contact.RayCast = contact.raycast(obs, origin, direction, magnitude)
            if rc.hit is not None:
                mag = rc.hit.to_hit.magnitude()
                if mag < dist: 
                    dist = mag
                    laser_hit = rc.hit
        player.laser.origin = origin
        player.laser.endpoint = laser_hit.hit_pos if laser_hit is not None else origin+(direction*magnitude)
        if player.laser.firing:
            player.laser.firing = False
            if laser_hit is not None and isinstance(laser_hit.object, UniformPolygon):
                obstacles += [poly for poly in split_uniform_polygon(laser_hit.object, origin, direction)]
                obstacles.remove(laser_hit.object)

def get_physics_objects(exclude:list[list] = []) -> chain[PhysicsObject]:
    object_lists = [[player], obstacles, bullets, [ground]]

    return chain(*[item for item in object_lists if item not in exclude])

def update_all(dt=0):
    # print("updating all")
    for obj in get_physics_objects():
        # if obj in shapes: print("updating a shape!")
        obj.update(dt)
    # player.update(dt)
    # ground.update(dt)
    # for bullet in bullets:
    #     bullet.update(dt)
    # for obs in obstacles:
    #     obs.update(dt)


def get_collision_objects():
    return [ground]+obstacles

# FORCES
def get_gravobjects() -> chain[PhysicsObject]:
    return chain(obstacles)
spawning=False
gravity = forces.Gravity((0, 1000), lambda: get_gravobjects())
playergravity = forces.Gravity((0, 1000), [player])


# INPUT
class UserInput:
    roll_right:list = [K_d, K_RIGHT]
    roll_left:list = [K_a, K_LEFT]
    jump:list = [K_SPACE]
    cannon = [1]
    laser = [1]

def process_input():
    global jumping, running, paused, aiming_laser
    key = pygame.key.get_pressed()
    mpos = mouse.get_pos()
    player.aiming_laser = mouse.get_pressed()[2]
    aiming_laser = player.aiming_laser

    while event := pygame.event.poll():
        # Quitting game
        if (event.type == pygame.QUIT 
            or (event.type == pygame.KEYDOWN
                and event.key == pygame.K_ESCAPE)):
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            paused = not paused
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in UserInput.cannon:
            if aiming_laser:
                fire_laser()
            else: fire_cannon()
        if event.type == pygame.KEYDOWN and event.key == K_RETURN:
            global spawning
            spawning = not spawning
            gravity.gravity = Vector2(0,1000) if not spawning else Vector2(0,25)
    player_avel = 0
    if any(key[k] for k in UserInput.roll_right):
        player_avel += player_max_avel
        pass
    if any(key[k] for k in UserInput.roll_left):
        player_avel -= player_max_avel
        pass
    player.avel = player_avel

    jumping = any(key[k] for k in UserInput.jump)

    player.cannon.angle = Vector2(1,0).angle_to(mpos-player.pos)
    

# DISPLAY
def draw_all(surface:Surface):
    for obs in obstacles: obs.draw(surface)
    player.draw(surface)
    for bullet in bullets: bullet.draw(surface)

    # player.laser.draw(surface)
    ground.draw(surface)


# DEBUGGING
# END DEBUGGING


# GAME LOOP
while running:
    # update the display
    pygame.display.update()
    clock.tick(fps)

    # Events and \/
    # Input
    process_input()

    # Update

    # add forces
    gravity.apply()
    playergravity.apply()
    # update
    update_all(dt)

    if abs(player.avel) > player_max_avel:
        player.avel = player_max_avel if player.avel > 0 else -player_max_avel
    
    # Resolve Collisions
    process_collisions()

    # TEMP
    if spawning:
        tick_spawn(dt)
    # END TEMP

    # clear forces
    clear_forces(get_physics_objects())
    # player.clear_force()
    # poly.clear_force() 
    # for bullet in bullets: 
    #     bullet.clear_force()
    

    # Graphics
    window.fill((10,0,0,0) if aiming_laser else bg_color)
    draw_all(window)
    

