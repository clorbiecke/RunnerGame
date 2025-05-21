# RunnerGame

GAME DESCRIPTION
Objective is to achieve highest score.
Platforms and obstacles will spawn from the right and top of the screen, the player must navigate by rolling and jumping to avoid falling off the screen. Obstacles can be avoided, blasted with the cannon to knock them back, or split with the laser.
The game starts on a static platform, then a laser wall creeps from the left to force the player to go right, and eventually off the static platform into the space where objects start spawning. Score is based on distance travelled to the right.

CONTROLS
- Move right/left with A/D or right/left arrows
- Jump with 'space'
- fire cannon/laser with left mouse
    - aim laser with right mouse
    - if aiming, left mouse fires laser, otherwise fires cannon
- pause with 'tab'
*for beta*
- press 'return' to toggle between...
    - high grav, shape spawning off
    - low grav, shape spawning on




TODO LIST
* Create prototype player: a uniform circle (or normal circle)
    * moves by rolling
    - cannon locked in center, aiming in move direction (by key, not vel)
    - laser that slices polys
    - jump by adding impulse, can be held for higher jump
* Test with seesaw, can i roll over seesaw with friction, and have it tip over?
- Add friction property to PhysicsObject
- Figure out raycasting to make sure bullets don't pass through objects
- Figure out Tiled