import pygame
from pygame.locals import *
from pygame.math import Vector2

import physics_objects, forces, contact
from physics_objects import *
# \/ get objects from helper instead of physics_objects once it has been implemented
#from tiled_helper_json import *

import colors, fonts, effects, hud_components

from hud_components import *

#TODO: 
#   - add angular drag to player rotation
class Player(Circle):
    def __init__(self, radius=100, **kwargs):
        super().__init__(radius, **kwargs)
        self.hole_color = Color(colors.red)
        self.hole_outline_color = colors.darken(colors.red)
        self.num_holes = 3
        self.hole_radius = self.radius / 3.0
        self.circum = self.radius * 2*math.pi

        self.cannon = Cannon()
        self.cannon.size = self.radius/100

        self.laser = Laser()
        self.aiming_laser = False

        self.on_ground = False

    def update(self, dt=0):
        super().update(dt)
        self.cannon.pos = self.pos
        self.cannon.update(dt)
        self.laser.update(dt)


    def draw(self, surface:Surface):
        super().draw(surface)
        for i in range(3):
            # print("drawing little circles")
            pos = self.pos + Vector2(self.radius/2.0,0).rotate(self.angle + (i/self.num_holes)*360)
            pygame.draw.circle(surface, self.hole_color, pos, self.hole_radius, 0)
            pygame.draw.circle(surface, self.hole_outline_color, pos, self.hole_radius, self.outline_width)
        # print(f"aiming laser: {self.aiming_laser}, ")
        self.laser.visible = (self.aiming_laser or self.laser.firing)
        self.laser.draw(surface)
        self.cannon.draw(surface)


    # def fire_cannon(self):



class Cannon(PhysicsObject):
    def __init__(self, name="cannon", mass=1, pos=(0,0), vel=(0,0), momi=math.inf, angle=0, avel=0, static:bool=True, generate_contacts=False, on_update:lambda obj:() = lambda obj:()):
        super().__init__(name, mass, pos, vel, momi, angle, avel, static, generate_contacts, on_update)
        self.size = 1
        self.barrel_end_local = Vector2(100,0)
        self.barrel_locals = [(-20,-20), (100,-20), (100,20), (-20,20)]
        self.barrel_color = colors.Color(colors.blue) #= colors.lighten(colors.grey, 0.4)
        self.head_locals = [(-30,-30), (40,-30), (40,30), (-30,30)]
        self.head_color = colors.Color(colors.purple) #Ccolor(colors.grey)
        self.update_points()

        self.cooldown = 0
        self.min_fire_interval = 0.4

    def update(self, dt=0):
        super().update(dt)
        self.update_points()
        if self.cooldown > 0: self.cooldown -= dt

    def update_points(self):
        self.barrel_points = [Vector2(point).rotate(self.angle)*self.size + self.pos for point in self.barrel_locals]
        self.head_points = [Vector2(point).rotate(self.angle)*self.size + self.pos for point in self.head_locals]
        self.barrel_end = Vector2(self.barrel_end_local*self.size).rotate(self.angle) + self.pos
    
    def draw(self, surface:Surface):
        pygame.draw.polygon(surface, self.barrel_color, self.barrel_points)
        pygame.draw.polygon(surface, self.barrel_color, self.barrel_points, 2)

        pygame.draw.polygon(surface, self.head_color, self.head_points)
        pygame.draw.polygon(surface, self.head_color, self.head_points, 2)
    

class Laser:
    def __init__(self, origin:Vector2=(0,0), endpoint:Vector2=(0,0), idle_width=1, color=colors.red, visible=True):
        self.origin = origin
        self.endpoint = endpoint
        self.idle_width = idle_width
        self.width = idle_width
        self.color = color
        self.visible = visible
        
        self.cooldown = 0
        self.recharge = 0.5
        self.firing = False
    
    def update(self, dt=0):
        if self.cooldown > 0:
            self.cooldown -= dt
        if self.width > self.idle_width:
            self.width = int((self.width-self.idle_width)/2)-1
        if self.width < self.idle_width: self.width = self.idle_width


    def draw(self, surface):
        # print(f"drawing laser..., visible: {self.visible}")
        if self.visible:
            pygame.draw.line(surface, self.color, self.origin, self.endpoint, self.width)

def split_uniform_polygon(poly:UniformPolygon, origin:Vector2, direction:Vector2) -> list[UniformPolygon, UniformPolygon]:
    # print("splitting polygon")
    polys = []
    pts = []
    break_indexes = []
    for i in range(len(poly.points)):
        # check if edge intersects and add new point if it does
        rn = direction.rotate(90)
        p1 = (poly.points[i]-origin) * rn
        p2 = (poly.points[i-1]-origin) * rn
        if p1*p2 < 0:
            brk_pt = (poly.points[i-1]-poly.points[i])*(p1/(p1-p2))+poly.points[i]
            break_indexes.append(len(pts))
            pts.append(brk_pt)
            # print(f"adding breakpoint pos: {brk_pt}")
        pts.append(poly.points[i])
        # print(f"adding point pos: {poly.points[i]}")
    if len(break_indexes) == 1: raise ValueError("Whoops, somehow only one break was made on polygon...")
    elif len(break_indexes) == 0: return False
    # print(f"break indexes: {break_indexes}")
    # print(f"points: {pts}")
    for i in range(len(break_indexes)):
        num = ((break_indexes[(i+1)%len(break_indexes)]-break_indexes[i])%len(pts))%len(pts)+1
        new_pts = []
        for n in range(num):
            new_pts.append(pts[(break_indexes[i]+n)%len(pts)]-poly.pos)
        # print(f"new point: {new_pts}")
        new_poly = UniformPolygon(poly.density, new_pts, fill_color=poly.fill_color, outline_color=poly.outline_color, outline_width=poly.outline_width)
        new_poly.pos = poly.pos+(new_pts[0]-new_poly.local_points[0])
        new_poly.vel = poly.vel + math.radians(poly.avel)*Vector2(new_poly.pos-poly.pos).rotate(90)
        new_poly.avel = poly.avel

        polys.append(new_poly)
    return polys

