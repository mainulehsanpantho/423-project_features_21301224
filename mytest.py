from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math

# --------------------------
# Car properties
# --------------------------
car1_position = [250, 250, 35]
car2_position = [350, 350, 35]
car_angle1 = 0
car_angle2 = 0
car_color1 = [0.1, 0.6, 0.1]  # Green
car_color2 = [0.6, 0.1, 0.1]  # Red
car_size = 40  # Used for collision detection

# Wheel properties
wheel_offset = 20
wheel_radius = 10
wheel_height = 5

# Movement speed
movement_speed = 6
rotation_speed = 6

# --------------------------
# Arena and Goal properties
# --------------------------
arena_size = 500
goal_size = 40
goal_depth = 30
wall_height = 50

# --------------------------
# Camera properties
# --------------------------
camera_position = [500, 500, 350]
camera_angle = [0, 0]  # Horizontal and vertical angles
camera_speed = 10
camera_rotate_speed = 5

# --------------------------
# Ball properties
# --------------------------
ball_position = [0, 0, 15]  # Start in the center
ball_velocity = [0, 0]  # Velocity in X and Y
ball_radius = 15
ball_color = [1.0, 1.0, 0.0]  # Yellow
ball_friction = 0.95  # Simulate slowing down

# --------------------------
# Scoring
# --------------------------
score_car1 = 0
score_car2 = 0

# --------------------------
# Functions
# --------------------------
def render_car(x, y, z, angle, color):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(angle, 0, 0, 1)
    glColor3f(color[0], color[1], color[2])
    glutSolidCube(car_size)

    glColor3f(0.1, 0.1, 0.1)
    for dx in [-wheel_offset, wheel_offset]:
        for dy in [-wheel_offset, wheel_offset]:
            glPushMatrix()
            glTranslatef(dx, dy, -15)
            gluCylinder(gluNewQuadric(), wheel_radius, wheel_radius, wheel_height, 10, 10)
            glPopMatrix()

    glPopMatrix()

def render_ball():
    glPushMatrix()
    glTranslatef(ball_position[0], ball_position[1], ball_position[2])
    glColor3f(ball_color[0], ball_color[1], ball_color[2])
    glutSolidSphere(ball_radius, 30, 30)
    glPopMatrix()

def draw_text(x, y, text_string):
    glRasterPos2f(x, y)
    for c in text_string:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))

def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 1.25, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glRotatef(camera_angle[0], 0, 1, 0)
    glRotatef(camera_angle[1], 1, 0, 0)
    gluLookAt(camera_position[0], camera_position[1], camera_position[2],
              0, 0, 35,
              0, 0, 1)

def render_arena():
    glPushMatrix()
    glColor3f(0.2, 0.8, 0.2)
    glTranslatef(0, 0, -wall_height / 2)
    glScalef(arena_size, arena_size, wall_height)
    glutSolidCube(1)
    glPopMatrix()



def render_goal_post(x, y, width=goal_size, height=goal_depth):
    """
    Draws a 3-line goal post frame that matches arena coordinates.
    x, y: position of center of goal along X and Y
    width: distance between left and right posts
    height: vertical height of the goal
    """
    glColor3f(1.0, 0.0, 0.0)  # Red posts
    half_width = width / 2
    base_z = 0  # Ground
    top_z = height

    glLineWidth(5)  # Make the lines visible
    glBegin(GL_LINES)

    # Left vertical post
    glVertex3f(x, y - half_width, base_z)
    glVertex3f(x, y - half_width, top_z)

    # Right vertical post
    glVertex3f(x, y + half_width, base_z)
    glVertex3f(x, y + half_width, top_z)

    # Top horizontal crossbar
    glVertex3f(x, y - half_width, top_z)
    glVertex3f(x, y + half_width, top_z)

    glEnd()



def check_collision_car_ball(car_pos, car_size, ball_pos, ball_radius):
    dx = ball_pos[0] - car_pos[0]
    dy = ball_pos[1] - car_pos[1]
    distance = math.sqrt(dx**2 + dy**2)
    car_half_diag = math.sqrt(2*(car_size/2)**2)
    if distance < (car_half_diag + ball_radius):
        return True, dx, dy
    return False, 0, 0

def update_ball():
    global ball_position, ball_velocity, score_car1, score_car2

    # Collision with cars
    for car_pos in [car1_position, car2_position]:
        collision, dx, dy = check_collision_car_ball(car_pos, car_size, ball_position, ball_radius)
        if collision:
            ball_velocity[0] = dx * 0.3
            ball_velocity[1] = dy * 0.3

    # Update ball position
    ball_position[0] += ball_velocity[0]
    ball_position[1] += ball_velocity[1]
    ball_velocity[0] *= ball_friction
    ball_velocity[1] *= ball_friction

    # Check for goals
    half_arena = arena_size / 2
    if abs(ball_position[1]) < goal_size/2:
        if ball_position[0] > half_arena - goal_size/2:  # Goal for car1
            score_car1 += 1
            reset_ball()
        elif ball_position[0] < -half_arena + goal_size/2:  # Goal for car2
            score_car2 += 1
            reset_ball()

    # Keep ball inside arena bounds (except goal area)
    max_x = half_arena - ball_radius
    max_y = half_arena - ball_radius
    ball_position[0] = max(-max_x, min(max_x, ball_position[0]))
    ball_position[1] = max(-max_y, min(max_y, ball_position[1]))

def reset_ball():
    global ball_position, ball_velocity
    ball_position = [0, 0, 15]  # Center
    ball_velocity = [0, 0]

def render_scores():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 800, 0, 600)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1, 1, 1)
    draw_text(50, 550, f"Green Car Score: {score_car1}")
    draw_text(550, 550, f"Red Car Score: {score_car2}")
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def render_scene():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    setup_camera()
    render_arena()
    render_car(car1_position[0], car1_position[1], car1_position[2], car_angle1, car_color1)
    render_car(car2_position[0], car2_position[1], car2_position[2], car_angle2, car_color2)
    update_ball()
    render_ball()
    
    render_goal_post(-arena_size / 2, 0, width=goal_size, height=goal_depth)  # Left goal
    render_goal_post(arena_size / 2, 0, width=goal_size, height=goal_depth)   # Right goal


    render_scores()
    glutSwapBuffers()

def handle_special_keys(key, x, y):
    global camera_position
    if key == GLUT_KEY_LEFT: camera_position[0] -= 3
    elif key == GLUT_KEY_RIGHT: camera_position[0] += 3
    elif key == GLUT_KEY_UP: camera_position[1] += 3
    elif key == GLUT_KEY_DOWN: camera_position[1] -= 3

def handle_keyboard(key, x, y):
    global car_angle1, car_angle2, car1_position, car2_position
    angle_radians1 = math.radians(car_angle1)
    angle_radians2 = math.radians(car_angle2)

    if key == b'a': car_angle1 += rotation_speed
    elif key == b'd': car_angle1 -= rotation_speed
    elif key == b'w':
        car1_position[0] += movement_speed * math.cos(angle_radians1)
        car1_position[1] += movement_speed * math.sin(angle_radians1)
    elif key == b's':
        car1_position[0] -= movement_speed * math.cos(angle_radians1)
        car1_position[1] -= movement_speed * math.sin(angle_radians1)
    elif key == b'j': car_angle2 += rotation_speed
    elif key == b'l': car_angle2 -= rotation_speed
    elif key == b'i':
        car2_position[0] += movement_speed * math.cos(angle_radians2)
        car2_position[1] += movement_speed * math.sin(angle_radians2)
    elif key == b'k':  # Move car 2 backward
        car2_position[0] -= movement_speed * math.cos(angle_radians2)
        car2_position[1] -= movement_speed * math.sin(angle_radians2)

    glutPostRedisplay()  # Redraw the scene after any key press

def main():
    # Initialize OpenGL
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"3D Car Soccer Game")

    glEnable(GL_DEPTH_TEST)  # Enable depth testing
    glClearColor(0.2, 0.2, 0.2, 1)  # Background color

    # Register callback functions
    glutDisplayFunc(render_scene)
    glutKeyboardFunc(handle_keyboard)
    glutSpecialFunc(handle_special_keys)
    glutIdleFunc(render_scene)  # Continuously update scene

    glutMainLoop()  # Start the main loop

if __name__ == "__main__":
    main()


