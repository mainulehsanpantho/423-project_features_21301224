
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import sys
import time

# --------------------------
# Window
# --------------------------
WIN_W, WIN_H = 1000, 700

# --------------------------
# Game state (module-level globals)
# --------------------------
# Car properties
car1_position = [-200.0, 0.0, 35.0]
car2_position = [200.0, 0.0, 35.0]
car_angle1 = 0.0
car_angle2 = 180.0
car_color1 = [0.1, 0.6, 0.1]  # green
car_color2 = [0.6, 0.1, 0.1]  # red
car_size = 40.0
car1_health = 100
car2_health = 100
car1_moving = [False, False, False, False]  # forward, back, left-rot, right-rot
car2_moving = [False, False, False, False]

# Jump/vertical
car1_vz = 0.0
car2_vz = 0.0
car_jump_strength = 18.0

# Boost
car1_boost = 100.0
car2_boost = 100.0
boost_max = 100.0
boost_depletion_rate = 40.0
boost_recharge_rate = 12.0
boost_multiplier = 1.8
car1_boosting = False
car2_boosting = False

# Visual wheel params
wheel_offset = 20.0
wheel_radius = 8.0
wheel_height = 6.0

# Movement & rotation tuning
base_movement_speed = 3.0
rotation_speed = 2.0   

# Arena / goals
arena_size = 500.0
goal_size = 60.0
goal_depth = 30.0
wall_height = 50.0

# Camera
camera_distance = 380.0
camera_height = 220.0
camera_look_z = 35.0

# Ball
ball_position = [0.0, 0.0, 15.0]
ball_velocity = [0.0, 0.0, 0.0]
ball_radius = 15.0
ball_color = [1.0, 1.0, 0.0]
ball_friction = 0.995
air_friction = 0.995
ball_max_speed = 30.0



# Scoring & control
score_car1 = 0
score_car2 = 0
is_paused = False
is_resetting = False
last_collision_time = 0
collision_cooldown = 300  # ms

# Timing physics
FPS = 60
dt = 1.0 / FPS

rng = random.Random(1234)



# --------------------------
# Utility: Midpoint Line Algorithm
# --------------------------
def midpoint_line_2d(x0, y0, x1, y1):
    pts = []
    x0 = int(round(x0)); y0 = int(round(y0)); x1 = int(round(x1)); y1 = int(round(y1))
    dx = abs(x1 - x0); dy = abs(y1 - y0)
    sx = 1 if x1 >= x0 else -1
    sy = 1 if y1 >= y0 else -1
    x, y = x0, y0
    if dy <= dx:
        d = 2 * dy - dx
        for _ in range(dx + 1):
            pts.append((x, y))
            if d > 0:
                y += sy
                d -= 2 * dx
            x += sx
            d += 2 * dy
    else:
        d = 2 * dx - dy
        for _ in range(dy + 1):
            pts.append((x, y))
            if d > 0:
                x += sx
                d -= 2 * dy
            y += sy
            d += 2 * dx
    return pts

# --------------------------
# Obstacles init
# --------------------------
# def init_obstacles():
#     global obstacles
#     obstacles = []
#     for _ in range(5):
#         obs_x = rng.uniform(-arena_size / 2 + 60, arena_size / 2 - 60)
#         obs_y = rng.uniform(-arena_size / 2 + 60, arena_size / 2 - 60)
#         obs_z = 15.0
#         obs_width = rng.uniform(30.0, 60.0)
#         obs_height = 20.0
#         obs_depth = 30.0
#         obstacles.append([obs_x, obs_y, obs_z, obs_width, obs_height, obs_depth])

# --------------------------
# Rendering helpers (including a car shape with nose)
# --------------------------
def draw_text_screen(x, y, text):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

def setup_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, (0.5, 1.0, 1.0, 0.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.9, 0.9, 0.9, 1.0))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

def render_car(x, y, z, angle, color, outline_color=(1,1,0)):
    """
    Render a car that is not just a box:
    - Main body: slightly flattened cuboid
    - Nose: a tapered triangular prism to show front/head clearly
    - Wheels: cylinders
    """
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(angle, 0, 0, 1)

    # Body (slightly flattened)
    glPushMatrix()
    glScalef(1.4, 0.9, 0.5)  # elongate in x to make car-like shape
    glColor3f(color[0], color[1], color[2])
    glutSolidCube(car_size)
    glPopMatrix()

    # Nose / front: triangular prism (drawn manually)
    # We'll create a triangular prism that sits in front (positive X local)
    nose_len = car_size * 0.6
    nose_w = car_size * 0.9
    nose_h = car_size * 0.4
    # vertices in local coordinates
    # base rectangle (back of nose)
    bx = car_size * 0.7  # back of nose relative to center
    front_x = bx + nose_len
    back_x = bx - nose_len * 0.2
    half_w = nose_w / 2.0
    half_h = nose_h / 2.0

    # We'll draw 4 triangles forming the prism
    glColor3f(color[0]*0.9 + 0.05, color[1]*0.9 + 0.05, color[2]*0.9 + 0.05)
    glBegin(GL_TRIANGLES)
    # top/front triangle
    glNormal3f(0,0,1)
    glVertex3f(front_x, 0.0, half_h)
    glVertex3f(back_x, -half_w, half_h)
    glVertex3f(back_x, half_w, half_h)
    # bottom/front triangle
    glNormal3f(0,0,-1)
    glVertex3f(front_x, 0.0, -half_h)
    glVertex3f(back_x, half_w, -half_h)
    glVertex3f(back_x, -half_w, -half_h)
    # left side
    glNormal3f(-1,0,0)
    glVertex3f(front_x, 0.0, half_h)
    glVertex3f(back_x, half_w, half_h)
    glVertex3f(back_x, half_w, -half_h)
    # right side
    glNormal3f(1,0,0)
    glVertex3f(front_x, 0.0, half_h)
    glVertex3f(back_x, -half_w, -half_h)
    glVertex3f(back_x, -half_w, half_h)
    glEnd()

    # Wheels
    glColor3f(0.05,0.05,0.05)
    for dx in [-wheel_offset, wheel_offset]:
        for dy in [-wheel_offset*0.6, wheel_offset*0.6]:
            glPushMatrix()
            glTranslatef(dx, dy, -car_size * 0.25)
            glRotatef(90, 0, 1, 0)
            quad = gluNewQuadric()
            gluCylinder(quad, wheel_radius, wheel_radius, wheel_height, 12, 4)
            glPopMatrix()

    # outline (wireframe) to emphasize shape
    glDisable(GL_LIGHTING)
    glColor3f(*outline_color)
    glPushMatrix()
    glScalef(1.4*1.01, 0.9*1.01, 0.5*1.01)
    glutWireCube(car_size)
    glPopMatrix()
    glEnable(GL_LIGHTING)

    glPopMatrix()

def render_obstacle(x, y, z, width, height, depth):
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(0.6, 0.6, 0.6)
    glScalef(width, height, depth)
    glutSolidCube(1.0)
    glPopMatrix()
    glDisable(GL_LIGHTING)
    glColor3f(0.5,0.5,0.5)
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(width*1.01, height*1.01, depth*1.01)
    glutWireCube(1.0)
    glPopMatrix()
    glEnable(GL_LIGHTING)

def render_ball():
    glPushMatrix()
    glTranslatef(ball_position[0], ball_position[1], ball_position[2])
    glColor3f(*ball_color)
    glutSolidSphere(ball_radius, 28, 28)
    glPopMatrix()

def render_arena():
    glPushMatrix()
    glColor3f(0.2, 0.8, 0.2)
    glTranslatef(0.0, 0.0, -wall_height / 2.0)
    glScalef(arena_size, arena_size, wall_height)
    glutSolidCube(1.0)
    glPopMatrix()

    # wireframe
    glDisable(GL_LIGHTING)
    glColor3f(1.0,1.0,1.0)
    glPushMatrix()
    glTranslatef(0.0, 0.0, -wall_height / 2.0)
    glScalef(arena_size * 1.002, arena_size * 1.002, wall_height * 1.002)
    glutWireCube(1.0)
    glPopMatrix()
    glEnable(GL_LIGHTING)

def render_goal_post(x, y, width=goal_size, height=goal_depth):
    glDisable(GL_LIGHTING)
    glLineWidth(4)
    glColor3f(1.0, 0.0, 0.0)
    half_w = width / 2.0
    base_z = 0.0
    top_z = height
    glBegin(GL_LINES)
    glVertex3f(x, y - half_w, base_z); glVertex3f(x, y - half_w, top_z)
    glVertex3f(x, y + half_w, base_z); glVertex3f(x, y + half_w, top_z)
    glVertex3f(x, y - half_w, top_z); glVertex3f(x, y + half_w, top_z)
    glEnd()
    glEnable(GL_LIGHTING)

# --------------------------
# Collision detection (AABB / closest-point)
# --------------------------
def aabb_collision_2d(center_a, half_a_x, half_a_y, center_b, half_b_x, half_b_y):
    return (abs(center_a[0] - center_b[0]) <= (half_a_x + half_b_x)) and \
           (abs(center_a[1] - center_b[1]) <= (half_a_y + half_b_y))

def check_collision_car_ball(car_pos, car_size_val, ball_pos, ball_r):
    car_half = car_size_val / 2.0
    closest_x = max(car_pos[0] - car_half, min(ball_pos[0], car_pos[0] + car_half))
    closest_y = max(car_pos[1] - car_half, min(ball_pos[1], car_pos[1] + car_half))
    dx = ball_pos[0] - closest_x
    dy = ball_pos[1] - closest_y
    dist2 = dx*dx + dy*dy
    return dist2 < (ball_r * ball_r), dx, dy

def check_collision_car_car(car1_pos_local, car2_pos_local, size_val):
    half = size_val / 2.0
    collided = aabb_collision_2d(car1_pos_local, half, half, car2_pos_local, half, half)
    dx = car1_pos_local[0] - car2_pos_local[0]
    dy = car1_pos_local[1] - car2_pos_local[1]
    return collided, dx, dy

def check_collision_car_obstacle(car_pos, car_size_val, obs):
    obs_pos = [obs[0], obs[1], obs[2]]
    obs_w, obs_h, obs_d = obs[3], obs[4], obs[5]
    car_half = car_size_val / 2.0
    obs_half_w = obs_w / 2.0
    obs_half_h = obs_h / 2.0
    obs_half_d = obs_d / 2.0
    overlap_xy = (car_pos[0] - car_half) < (obs_pos[0] + obs_half_w) and \
                 (car_pos[0] + car_half) > (obs_pos[0] - obs_half_w) and \
                 (car_pos[1] - car_half) < (obs_pos[1] + obs_half_h) and \
                 (car_pos[1] + car_half) > (obs_pos[1] - obs_half_h)
    overlap_z = (car_pos[2] - car_half / 2.0) < (obs_pos[2] + obs_half_d) and \
                (car_pos[2] + car_half / 2.0) > (obs_pos[2] - obs_half_d)
    if overlap_xy and overlap_z:
        dx = car_pos[0] - obs_pos[0]
        dy = car_pos[1] - obs_pos[1]
        return True, dx, dy
    return False, 0.0, 0.0

def check_collision_ball_obstacle(ball_pos, ball_r, obs):
    obs_pos = [obs[0], obs[1], obs[2]]
    obs_w, obs_h, obs_d = obs[3], obs[4], obs[5]
    closest_x = max(obs_pos[0] - obs_w/2.0, min(ball_pos[0], obs_pos[0] + obs_w/2.0))
    closest_y = max(obs_pos[1] - obs_h/2.0, min(ball_pos[1], obs_pos[1] + obs_h/2.0))
    dx = ball_pos[0] - closest_x
    dy = ball_pos[1] - closest_y
    dist2 = dx*dx + dy*dy
    return dist2 < (ball_r * ball_r), dx, dy

# --------------------------
# Collision response & physics
# --------------------------
def apply_car_ball_collision(car_pos, car_angle, car_moving, boosting, car_vz_local, movement_speed_local):
    """
    Apply impulse to global ball_velocity depending on car planar velocity (inputs),
    boost and vertical velocity (jump). Returns True if collision occurred.
    """
    global ball_velocity, ball_position
    collided, dx, dy = check_collision_car_ball(car_pos, car_size, ball_position, ball_radius)
    if not collided:
        return False

    ang_rad = math.radians(car_angle)
    forward = [math.cos(ang_rad), math.sin(ang_rad)]
    car_vx = 0.0
    car_vy = 0.0
    # forward/back keys
    if car_moving[0]:
        car_vx += movement_speed_local * forward[0]
        car_vy += movement_speed_local * forward[1]
    if car_moving[1]:
        car_vx -= movement_speed_local * 0.6 * forward[0]
        car_vy -= movement_speed_local * 0.6 * forward[1]
    # rotation strafe small
    if car_moving[2]:
        car_vx += -0.2 * movement_speed_local * forward[1]
        car_vy += 0.2 * movement_speed_local * forward[0]
    if car_moving[3]:
        car_vx += 0.2 * movement_speed_local * forward[1]
        car_vy += -0.2 * movement_speed_local * forward[0]

    if boosting:
        car_vx *= boost_multiplier
        car_vy *= boost_multiplier

    car_speed = math.sqrt(car_vx*car_vx + car_vy*car_vy)
    vz_impulse = 0.0
    if car_vz_local > 2.0:
        vz_impulse = car_vz_local * 0.8

    # If near-static, push by overlap direction mildly; else transfer momentum scaled
    if car_speed < 0.5:
        dir_len = math.sqrt(dx*dx + dy*dy)
        if dir_len < 1e-5:
            dir_len = 1.0
        nx = dx / dir_len
        ny = dy / dir_len
        ball_velocity[0] += nx * 3.0
        ball_velocity[1] += ny * 3.0
    else:
        transfer = 0.6 + min(0.8, car_speed / 20.0)
        ball_velocity[0] += car_vx * transfer * 0.15
        ball_velocity[1] += car_vy * transfer * 0.15

    ball_velocity[2] += vz_impulse * 0.5

    # cap planar speed
    sp = math.sqrt(ball_velocity[0]**2 + ball_velocity[1]**2)
    if sp > ball_max_speed:
        s = ball_max_speed / sp
        ball_velocity[0] *= s
        ball_velocity[1] *= s

    return True

def update_physics():
    global ball_position, ball_velocity, car1_health, car2_health, score_car1, score_car2, last_collision_time, car1_boost, car2_boost, car1_vz, car2_vz, is_resetting

    if is_paused or is_resetting:
        return

    current_time_ms = glutGet(GLUT_ELAPSED_TIME)

    # Boost meters
    global_dt = dt
    if car1_boosting and car1_boost > 0.0:
        car1_boost = max(0.0, car1_boost - boost_depletion_rate * global_dt)
    else:
        car1_boost = min(boost_max, car1_boost + boost_recharge_rate * global_dt)
    if car2_boosting and car2_boost > 0.0:
        car2_boost = max(0.0, car2_boost - boost_depletion_rate * global_dt)
    else:
        car2_boost = min(boost_max, car2_boost + boost_recharge_rate * global_dt)

    # Movement speeds include boost if active
    speed1 = base_movement_speed * (boost_multiplier if car1_boosting and car1_boost > 0.0 else 1.0)
    speed2 = base_movement_speed * (boost_multiplier if car2_boosting and car2_boost > 0.0 else 1.0)

    # Car vertical physics (simple)
    car1_vz += -9.8 * global_dt * 1.5  # tuned gravity for feel
    car1_position[2] += car1_vz * global_dt
    if car1_position[2] < 35.0:
        car1_position[2] = 35.0
        car1_vz = 0.0

    car2_vz += -9.8 * global_dt * 1.5
    car2_position[2] += car2_vz * global_dt
    if car2_position[2] < 35.0:
        car2_position[2] = 35.0
        car2_vz = 0.0

    # Update planar movement
    update_movement(speed1, speed2)

    # Car-ball collisions (apply impulses)
    if apply_car_ball_collision(car1_position, car_angle1, car1_moving, car1_boosting, car1_vz, speed1):
        last_collision_time = current_time_ms
    if apply_car_ball_collision(car2_position, car_angle2, car2_moving, car2_boosting, car2_vz, speed2):
        last_collision_time = current_time_ms

    # Car-obstacle and ball-obstacle collisions

    # Car-car collision
    colcc, dxcc, dycc = check_collision_car_car(car1_position, car2_position, car_size)
    if colcc:
        car1_health -= 20
        car2_health -= 20
        car1_position[0] += dxcc * 0.02
        car1_position[1] += dycc * 0.02
        car2_position[0] -= dxcc * 0.02
        car2_position[1] -= dycc * 0.02
        last_collision_time = current_time_ms
        if car1_health <= 0:
            score_car2 += 1
            reset_game()
        if car2_health <= 0:
            score_car1 += 1
            reset_game()

    # Ball physics integration
    ball_velocity[2] += -9.8 * global_dt * 1.5
    ball_position[0] += ball_velocity[0] * global_dt * 30.0
    ball_position[1] += ball_velocity[1] * global_dt * 30.0
    ball_position[2] += ball_velocity[2] * global_dt * 30.0

    # ground collision for ball
    if ball_position[2] - ball_radius <= 0.0:
        ball_position[2] = ball_radius
        if abs(ball_velocity[2]) > 1.0:
            ball_velocity[2] = -ball_velocity[2] * 0.4
            ball_velocity[0] *= 0.98
            ball_velocity[1] *= 0.98
        else:
            ball_velocity[2] = 0.0
            ball_velocity[0] *= ball_friction
            ball_velocity[1] *= ball_friction
    else:
        ball_velocity[0] *= air_friction
        ball_velocity[1] *= air_friction

    # Bound ball in arena
    half = arena_size / 2.0
    max_x = half - ball_radius; max_y = half - ball_radius
    ball_position[0] = max(-max_x, min(max_x, ball_position[0]))
    ball_position[1] = max(-max_y, min(max_y, ball_position[1]))

    # Goal detection (tuned): when ball crosses near edge and near ground and y velocity negative enough
    if ball_position[0] > (half - 30):
        if (ball_position[1] + ball_velocity[1] * global_dt * 30.0) <= -160.0 and ball_position[2] <= ball_radius + 2.0:
            score_car1 += 1
            reset_game()
    if ball_position[0] < -(half - 30):
        if (ball_position[1] + ball_velocity[1] * global_dt * 30.0) <= -160.0 and ball_position[2] <= ball_radius + 2.0:
            score_car2 += 1
            reset_game()

# --------------------------
# Movement update (rotation & planar movement)
# --------------------------
def update_movement(speed1, speed2):
    global car_angle1, car_angle2, car1_position, car2_position
    a1 = math.radians(car_angle1)
    a2 = math.radians(car_angle2)

    # Car1 forward/back
    if car1_moving[0]:
        car1_position[0] += speed1 * math.cos(a1)
        car1_position[1] += speed1 * math.sin(a1)
    if car1_moving[1]:
        car1_position[0] -= speed1 * 0.6 * math.cos(a1)
        car1_position[1] -= speed1 * 0.6 * math.sin(a1)
    if car1_moving[2]:
        car_angle1 += rotation_speed
    if car1_moving[3]:
        car_angle1 -= rotation_speed

    # Car2
    if car2_moving[0]:
        car2_position[0] += speed2 * math.cos(a2)
        car2_position[1] += speed2 * math.sin(a2)
    if car2_moving[1]:
        car2_position[0] -= speed2 * 0.6 * math.cos(a2)
        car2_position[1] -= speed2 * 0.6 * math.sin(a2)
    if car2_moving[2]:
        car_angle2 += rotation_speed
    if car2_moving[3]:
        car_angle2 -= rotation_speed

    # keep inside arena
    half_arena = arena_size / 2.0
    for pos in (car1_position, car2_position):
        pos[0] = max(-half_arena + car_size/2.0, min(half_arena - car_size/2.0, pos[0]))
        pos[1] = max(-half_arena + car_size/2.0, min(half_arena - car_size/2.0, pos[1]))

# --------------------------
# Reset game
# --------------------------
def reset_game():
    global car1_position, car2_position, ball_position, ball_velocity, car1_health, car2_health, car1_boost, car2_boost, car1_vz, car2_vz, is_resetting
    car1_position = [-200.0, 0.0, 35.0]
    car2_position = [200.0, 0.0, 35.0]
    ball_position = [0.0, 0.0, 15.0]
    ball_velocity = [0.0, 0.0, 0.0]
    car1_health = 100
    car2_health = 100
    car1_boost = boost_max
    car2_boost = boost_max
    car1_vz = 0.0
    car2_vz = 0.0
    
    is_resetting = False

# --------------------------
# HUD
# --------------------------
def render_hud():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Scores
    glColor3f(1,1,1)
    draw_text_screen(30, WIN_H - 30, f"Green Car Score: {score_car1}")
    draw_text_screen(WIN_W - 220, WIN_H - 30, f"Red Car Score: {score_car2}")

    # Health bars
    if car1_health > 50:
        glColor3f(0.0, 1.0, 0.0)
    else:
        glColor3f(1.0, 0.0, 0.0)
    glBegin(GL_QUADS)
    glVertex2f(30, WIN_H - 60)
    glVertex2f(30 + car1_health * 1.5, WIN_H - 60)
    glVertex2f(30 + car1_health * 1.5, WIN_H - 70)
    glVertex2f(30, WIN_H - 70)
    glEnd()
    draw_text_screen(30, WIN_H - 80, "Green Health")

    if car2_health > 50:
        glColor3f(0.0, 1.0, 0.0)
    else:
        glColor3f(1.0, 0.0, 0.0)
    glBegin(GL_QUADS)
    glVertex2f(WIN_W - 250, WIN_H - 60)
    glVertex2f(WIN_W - 250 + car2_health * 1.5, WIN_H - 60)
    glVertex2f(WIN_W - 250 + car2_health * 1.5, WIN_H - 70)
    glVertex2f(WIN_W - 250, WIN_H - 70)
    glEnd()
    draw_text_screen(WIN_W - 250, WIN_H - 80, "Red Health")

    # Boost meters using midpoint algorithm outlines
    meter_x = 30; meter_y = 40; meter_w = 200; meter_h = 14
    glColor3f(1.0,1.0,1.0)
    pts = midpoint_line_2d(meter_x, meter_y, meter_x + meter_w, meter_y)
    glBegin(GL_POINTS)
    for px, py in pts: glVertex2i(px, py)
    pts = midpoint_line_2d(meter_x + meter_w, meter_y, meter_x + meter_w, meter_y + meter_h)
    for px, py in pts: glVertex2i(px, py)
    pts = midpoint_line_2d(meter_x + meter_w, meter_y + meter_h, meter_x, meter_y + meter_h)
    for px, py in pts: glVertex2i(px, py)
    pts = midpoint_line_2d(meter_x, meter_y + meter_h, meter_x, meter_y)
    for px, py in pts: glVertex2i(px, py)
    glEnd()
    fill_w = int((car1_boost / boost_max) * (meter_w - 2))
    glColor3f(0.2, 0.6, 1.0)
    glBegin(GL_QUADS)
    glVertex2f(meter_x + 1, meter_y + 1)
    glVertex2f(meter_x + 1 + fill_w, meter_y + 1)
    glVertex2f(meter_x + 1 + fill_w, meter_y + meter_h - 1)
    glVertex2f(meter_x + 1, meter_y + meter_h - 1)
    glEnd()
    draw_text_screen(meter_x, meter_y + meter_h + 6, "Green Boost")

    meter_x2 = WIN_W - 250; meter_y2 = 40
    glColor3f(1.0,1.0,1.0)
    pts = midpoint_line_2d(meter_x2, meter_y2, meter_x2 + meter_w, meter_y2)
    glBegin(GL_POINTS)
    for px, py in pts: glVertex2i(px, py)
    pts = midpoint_line_2d(meter_x2 + meter_w, meter_y2, meter_x2 + meter_w, meter_y2 + meter_h)
    for px, py in pts: glVertex2i(px, py)
    pts = midpoint_line_2d(meter_x2 + meter_w, meter_y2 + meter_h, meter_x2, meter_y2 + meter_h)
    for px, py in pts: glVertex2i(px, py)
    pts = midpoint_line_2d(meter_x2, meter_y2 + meter_h, meter_x2, meter_y2)
    for px, py in pts: glVertex2i(px, py)
    glEnd()
    fill_w2 = int((car2_boost / boost_max) * (meter_w - 2))
    glColor3f(0.2, 0.6, 1.0)
    glBegin(GL_QUADS)
    glVertex2f(meter_x2 + 1, meter_y2 + 1)
    glVertex2f(meter_x2 + 1 + fill_w2, meter_y2 + 1)
    glVertex2f(meter_x2 + 1 + fill_w2, meter_y2 + meter_h - 1)
    glVertex2f(meter_x2 + 1, meter_y2 + meter_h - 1)
    glEnd()
    draw_text_screen(meter_x2, meter_y2 + meter_h + 6, "Red Boost")

    if is_paused:
        draw_text_screen(WIN_W/2 - 80, WIN_H/2 + 40, "PAUSED")
        draw_text_screen(WIN_W/2 - 120, WIN_H/2 + 10, "Press 'r' to restart, 'q' to quit, click middle to resume")

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# --------------------------
# Camera & main render
# --------------------------
def setup_camera():
    mid_x = (car1_position[0] + car2_position[0]) / 2.0
    mid_y = (car1_position[1] + car2_position[1]) / 2.0
    eye_x = mid_x
    eye_y = mid_y - camera_distance
    eye_z = camera_height
    gluLookAt(eye_x, eye_y, eye_z, mid_x, mid_y, camera_look_z, 0, 0, 1)

def render_scene():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, float(WIN_W) / float(WIN_H), 0.1, 4000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    setup_lighting()
    setup_camera()

    render_arena()
    render_goal_post(-arena_size / 2.0, 0.0, width=goal_size, height=goal_depth)
    render_goal_post(arena_size / 2.0, 0.0, width=goal_size, height=goal_depth)

    

    render_car(car1_position[0], car1_position[1], car1_position[2], car_angle1, car_color1, outline_color=(1,1,0))
    render_car(car2_position[0], car2_position[1], car2_position[2], car_angle2, car_color2, outline_color=(1,0.5,0.5))

    render_ball()

    # step physics then HUD (physics runs independently in timer too)
    update_physics()
    render_hud()

    glutSwapBuffers()

# --------------------------
# Input handlers
# --------------------------
def handle_special_keys(key, x, y):
    global camera_distance, camera_height
    if key == GLUT_KEY_LEFT:
        camera_distance += 10.0
    elif key == GLUT_KEY_RIGHT:
        camera_distance -= 10.0
    elif key == GLUT_KEY_UP:
        camera_height += 10.0
    elif key == GLUT_KEY_DOWN:
        camera_height -= 10.0
    glutPostRedisplay()

def handle_keyboard(key, x, y):
    global car1_moving, car2_moving, car1_vz, car2_vz, car1_boosting, car2_boosting, car_color1, car_color2, is_paused
    k = key.decode('utf-8') if isinstance(key, bytes) else key
    k = k.lower()
    # Car1 controls: W/S forward/back, A/D rotate, Space jump, E boost, B color
    if k == 'a':
        car1_moving[2] = True
    elif k == 'd':
        car1_moving[3] = True
    elif k == 'w':
        car1_moving[0] = True
    elif k == 's':
        car1_moving[1] = True
    elif k == ' ':
        # space = car1 jump
        if car1_position[2] <= 35.01:
            car1_vz = car_jump_strength * (1.2 if car1_boosting and car1_boost > 0 else 1.0)
    elif k == 'e':
        car1_boosting = True
    elif k == 'b':
        car_color1[0], car_color1[1], car_color1[2] = rng.random(), rng.random(), rng.random()

    # Car2 controls: I/K forward/back, J/L rotate, U jump (chosen due to GLUT limitations), O boost, N color
    elif k == 'j':
        car2_moving[2] = True
    elif k == 'l':
        car2_moving[3] = True
    elif k == 'i':
        car2_moving[0] = True
    elif k == 'k':
        car2_moving[1] = True
    elif k == 'u':  # car2 jump (use 'u' key as Right-Shift is unreliable in GLUT)
        if car2_position[2] <= 35.01:
            car2_vz = car_jump_strength * (1.2 if car2_boosting and car2_boost > 0 else 1.0)
    elif k == 'o':
        car2_boosting = True
    elif k == 'n':
        car_color2[0], car_color2[1], car_color2[2] = rng.random(), rng.random(), rng.random()

    # General controls
    elif k == 'p':
        toggle_pause()
    elif k == 'r':
        reset_game()
    elif k == 'q':
        sys.exit(0)
    glutPostRedisplay()

def handle_keyboard_up(key, x, y):
    global car1_moving, car2_moving, car1_boosting, car2_boosting
    k = key.decode('utf-8') if isinstance(key, bytes) else key
    k = k.lower()
    if k == 'a':
        car1_moving[2] = False
    elif k == 'd':
        car1_moving[3] = False
    elif k == 'w':
        car1_moving[0] = False
    elif k == 's':
        car1_moving[1] = False
    elif k == 'e':
        car1_boosting = False
    elif k == 'j':
        car2_moving[2] = False
    elif k == 'l':
        car2_moving[3] = False
    elif k == 'i':
        car2_moving[0] = False
    elif k == 'k':
        car2_moving[1] = False
    elif k == 'o':
        car2_boosting = False
    glutPostRedisplay()

def mouse_click(button, state, x, y):
    global is_paused
    if button == GLUT_MIDDLE_BUTTON and state == GLUT_DOWN:
        toggle_pause()
    glutPostRedisplay()

def toggle_pause():
    global is_paused
    is_paused = not is_paused

# --------------------------
# Timer & main init
# --------------------------
def idle_func():
    glutPostRedisplay()

def timer_func(val):
    # Timer drives steady physics stepping too
    if not is_paused:
        update_physics()
    glutPostRedisplay()
    glutTimerFunc(int(dt * 1000), timer_func, 0)

def init_glut():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutCreateWindow(b"Rocket League 3D - Improved Cars & Controls")
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.15,0.15,0.15,1.0)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_NORMALIZE)
    setup_lighting()
    glutDisplayFunc(render_scene)
    glutKeyboardFunc(handle_keyboard)
    glutKeyboardUpFunc(handle_keyboard_up)
    glutSpecialFunc(handle_special_keys)
    glutMouseFunc(mouse_click)
    glutIdleFunc(idle_func)
    glutTimerFunc(int(dt*1000), timer_func, 0)

if __name__ == "__main__":
    init_glut()
    glutMainLoop()
