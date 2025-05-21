import pytmx
import physics_objects  # different import than usual, we will override the physics objects
import math
import pygame
from pygame.math import Vector2
import json

# This class implements properties you want to have in all objects
# The properties called out here in the constructor:
#   restitution, resolve, rebound, friction, name, and type
# can be used in Tiled and handled as properties here.
# Name and Class map to name and type.  
# The others, restitution, resolve, rebound, and friction, are specified under Custom Properties.
# You can also specify mass, avel, color, and width as Custom Properties.  
# Finally, you can set a pivot point by using pivot as a Custom Property
# of type object which points to a point type object.  
class CustomObject:
    def __init__(self, mass=math.inf, restitution=0.2, resolve=True, rebound=0, friction=1, name="", type="", **kwargs):
        self.restitution = restitution
        self.resolve = resolve
        self.name = name
        self.type = type
        self.rebound = rebound
        self.friction = friction
        super().__init__(mass=mass, **kwargs)  # default is now infinite mass


# These class definitions call CustomObject first in inheritance.
# They extend the definitions form physics_objects.py.
class Polygon(CustomObject, physics_objects.Polygon): pass
class Circle(CustomObject, physics_objects.Circle): pass
class Wall(CustomObject, physics_objects.Wall): pass


# Helper function to parse hex color data
def parse_color(c):
    a = int(c[1:3], 16)
    r = int(c[3:5], 16)
    g = int(c[5:7], 16)
    b = int(c[7:9], 16)
    return r,g,b,a

# Parse dictionary object from a tmj file into a PhysicsObject
def parse_object(o):
    # Additional properties will be stored in kwargs
    kwargs = dict()
    if "properties" in o:
        for property in o["properties"]:
            key = property["name"]
            value = property["value"]
            # color
            if property["type"] == "color":
                kwargs[key] = parse_color(value)
            elif property["type"] == "string":
                # list
                if "," in value:
                    alist = value.split(",")
                    for i, x in enumerate(alist):
                        try:
                            if float(x) == int(x):
                                alist[i] = int(x)
                            else:
                                alist[i] = float(x)
                        except:
                            pass
                    kwargs[key] = alist
                # string
                else: 
                    kwargs[key] = value
            else: # int, float, bool
                kwargs[key] = value

    # Polygon
    if "polygon" in o:
        pos = make_vector2(o)
        points = [make_vector2(p) for p in o["polygon"]]
        # handle pivot point that points to a point object in Tiled
        pivot = Vector2(0,0)
        if "pivot" in kwargs:
            for p in raw_objects:
                if p["id"] == kwargs["pivot"]:
                    pivot = make_vector2(p) - pos
                    del kwargs["pivot"]
                    break
        shape = Polygon(pos=pos, local_points=points, name=o["name"], type=o["type"], angle=o["rotation"], **kwargs)
        if pivot:
            for p in shape.local_points:
                p -= pivot.rotate(-shape.angle)
            shape.pos += pivot
            shape.update(0)
        return shape
        
    # Circle (squares are interpreted as circles)
    elif "ellipse" in o:
        if o["width"] == o["height"]:  
            center = (o["x"] + o["width"]/2, o["y"] + o["height"]/2)
            return Circle(pos=center, radius=o["width"]/2, name=o["name"], type=o["type"], angle=o["rotation"], **kwargs)
        else:
            print("Non-circular ellipses are not supported.  Make width and height exactly equal.")
    
    # Point (ignore, only used as markers for pivot points)
    elif "point" in o or ("ellipse" not in o and o["width"] == o["height"] == 0):
        pass

    # Rectangle (non-circular ellipses are interpreted as rectangles)
    else:
        points = [(0,0), (o["width"],0), (o["width"], o["height"]), (0, o["height"])]
        pos = make_vector2(o)
        # handle pivot point that points to a point object in Tiled
        pivot = Vector2(0,0)
        if "pivot" in kwargs:
            for p in raw_objects:
                if p["id"] == kwargs["pivot"]:
                    pivot = make_vector2(p) - pos
                    del kwargs["pivot"]
                    break
        shape = Polygon(pos=pos, local_points=points, name=o["name"], type=o["type"], angle=o["rotation"], **kwargs)
        if pivot:
            for p in shape.local_points:
                p -= pivot.rotate(-shape.angle)
            shape.pos += pivot
            shape.update(0)
        return shape

def make_vector2(o):
    return Vector2(o["x"], o["y"])

def load_tmj_to_objects(filename):
    # Load data from tmx file    
    global data
    with open(filename) as f:
        data = json.load(f)

    width = data["width"] * data["tilewidth"]
    height = data["height"] * data["tileheight"]
    global raw_objects
    raw_objects = []
    # # Parse data into objects
    for layer in data["layers"]:
        if "objects" in layer:
            for o in layer["objects"]:
                raw_objects.append(o)
    objects = []
    for o in raw_objects:
        obj = parse_object(o)
        if obj is not None:
            objects.append(obj)
    
    return objects, (width, height)
