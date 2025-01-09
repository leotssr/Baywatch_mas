import pygame
from agents import Environment

class UserInterface:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 738))
        self.clock = pygame.time.Clock()
        self.running = True
        self.cursor = Cursor(self,[0.2, 0.5, 1, 10, 20], [10, 10])
        self.slider = Slider(self)
        self.environment = Environment(self, [2000, 720])
        self.camera_x = 0

    def process_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                break
            if pygame.mouse.get_pressed()[0]:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if self.mouse_on_cursor(mouse_x, mouse_y):
                    num_steps = len(self.cursor.speed_options)
                    step_height = self.cursor.height/(num_steps-1)
                    closest_step = round((mouse_y - self.cursor.position[1]) / step_height)
                    closest_step = max(0, min(num_steps - 1, closest_step))  # Limiter aux bornes
                    self.cursor.selected_option = closest_step
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.slider.handle.collidepoint(event.pos):
                    self.slider.dragging = True
            if event.type == pygame.MOUSEBUTTONUP:
                self.slider.dragging = False
            if event.type == pygame.MOUSEMOTION:
                if self.slider.dragging:
                    self.slider.handle.x = max(0, min(event.pos[0] - self.slider.handle_width // 2, self.screen.get_width() - self.slider.handle_width))
                    self.camera_x = self.slider.slider_to_camera(self.slider.handle.x)
    
    def update(self, dt):
        self.cursor.update()
        self.environment.update(dt, self.cursor.speed_factor)

    def render(self):
        self.environment.display(self.camera_x)
        self.cursor.display()
        self.slider.display()
        pygame.display.flip()

    def run(self):
        dt=0
        while self.running:
            self.process_input()
            self.update(dt)
            self.render()
            dt = self.clock.tick(60) / 1000

    def mouse_on_cursor(self, mouse_x, mouse_y):
        cursor_height = self.cursor.height
        cursor_width = self.cursor.width
        cursor_position = self.cursor.position
        if mouse_x > cursor_position[0] - 0.2*cursor_width and mouse_x < cursor_position[0]+1.2*cursor_width:
            if mouse_y > cursor_position[1] - 0.2*cursor_height and mouse_y < cursor_position[1]+1.2*cursor_height:
                return True
        return False

        

class Slider:
    def __init__(self, UI):
        self.UI = UI
        self.height = 20
        self.handle_width = 100
        self.dragging = False
        self.rect = pygame.Rect(0, self.UI.screen.get_height() - self.height, self.UI.screen.get_width(), self.height)
        self.handle = pygame.Rect(0, self.UI.screen.get_height() - self.height, self.handle_width, self.height)

    def slider_to_camera(self, slider_x):
        max_camera_x = self.UI.environment.size[0] - self.UI.screen.get_width()
        max_slider_x = self.UI.screen.get_width() - self.handle_width
        return (slider_x / max_slider_x) * max_camera_x

    def camera_to_slider(self, camera_x):
        max_camera_x = self.UI.environment.size[0] - self.UI.screen.get_width()
        max_slider_x = self.UI.screen.get_width() - self.handle_width
        return (camera_x / max_camera_x) * max_slider_x
    
    def display(self):
        pygame.draw.rect(self.UI.screen, (200, 200, 200), self.rect)  
        pygame.draw.rect(self.UI.screen, (100, 100, 100), self.handle)


class Cursor:
    def __init__(self, userrInterface, speed_options, position):
        self.screen = userrInterface.screen

        self.position = position
        self.height = 400
        self.width = 16

        self.speed_options = speed_options
        self.selected_option = 2
        self.speed_factor = speed_options[self.selected_option]
        

    def update(self):
        self.speed_factor = self.speed_options[self.selected_option]

    def display(self):
        step_height = self.height/(len(self.speed_options)-1)
        slider_rect = pygame.Rect(self.position[0], self.position[1], self.width, self.height)  # Barre verticale
        slider_knob = pygame.Rect(self.position[0]-4, self.position[1]+self.selected_option*step_height-2, 12, 4)  # Indicateur

        # Dessiner le curseur
        pygame.draw.rect(self.screen, "gray", slider_rect)  # Barre statique
        for i in range(len(self.speed_options)):
            position_y = self.position[1]+i*step_height
            pygame.draw.circle(self.screen, "black", (slider_rect.centerx, position_y), 5)  # Marques discrètes
            font = pygame.font.Font(None, 20)
            text = font.render(f"x{self.speed_options[i]}", True, "black")
            self.screen.blit(text, (slider_rect.right + 5, position_y-5))

        pygame.draw.rect(self.screen, "black", slider_knob)  # Indicateur mobile
