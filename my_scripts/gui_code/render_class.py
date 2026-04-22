import pygame
import cv2
import numpy as np
from multiprocessing.synchronize import Event as EventClass
from .helper_functions import *
from .robo_visualization import show_info_robo

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
LIGHT_GREY = (200, 200, 200)
DARK_GREY = (150, 150, 150)
GREEN = (0, 200, 0)
LIGHT_RED = (218,27,38)

BACKGROUND = (235,249,255)
LIGHT_BLUE = (164,212,233)
DARK_BLUE = (0,159,227)

class GuiHandler:
    def __init__(self, width: int, height: int):
        # general
        self.running = True
        self.x_pixel = width
        self.y_pixel = height
        self.current_time = 0        
        # input text field
        self.user_text = "Provide Task"
        self.user_task = None
        self.INPUT_BOX_X = 1200
        self.INPUT_BOX_Y = 200
        self.INPUT_BOX_WIDTH = 600
        self.MIN_INPUT_BOX_HEIGHT = 40
        self.LINE_SPACING = 5
        self.HISTORY_SPACING = 100     
        self.input_box_rect = pygame.Rect(self.INPUT_BOX_X,
                                          self.INPUT_BOX_Y,
                                          self.INPUT_BOX_WIDTH,
                                          self.MIN_INPUT_BOX_HEIGHT)
        self.text_display_width = self.input_box_rect.width - 10
        self.typing_active = False
        self.font_big = pygame.font.SysFont("cooperhewitt", 30)
        self.font_small = pygame.font.SysFont("cooperhewitt", 25)
        self.cursor_visible = True
        self.cursor_blink_interval = 500
        self.cursor_timer = pygame.time.get_ticks()
        # Recording box
        self.record_button_text = "Record Task"
        self.record_BOX_WIDTH = 150
        self.record_BOX_X = 1200 - int(self.record_BOX_WIDTH/2) + int(self.INPUT_BOX_WIDTH/2)
        self.record_BOX_Y = 140
        
        self.record_BOX_HEIGHT = 40  
        self.record_box_rect = pygame.Rect(self.record_BOX_X,
                                          self.record_BOX_Y,
                                          self.record_BOX_WIDTH,
                                          self.record_BOX_HEIGHT)
        self.recording_text_display_width = self.record_box_rect.width - 10
        self.recording_active = False
        # webcam frame
        self.webcam_width = 1080
        self.webcam_height = 720
        self.webcam_frame_width = 2
        self.webcam_y_pixel = self.input_box_rect.bottom + self.webcam_frame_width +20
        self.webcam_x_pixel = 70
        # output text 
        self.input_history = []
        self.box_history_y = self.input_box_rect.bottom + 20
        self.box_history_height = self.y_pixel - self.box_history_y - 20
        self.history_area_rect = pygame.Rect(self.input_box_rect.x, self.box_history_y,
                                        self.input_box_rect.width, self.box_history_height)
        # roboarm status and reset
        # roboter 1
        self.reset_arm_1 = False
        self.ip_arm_1 = "10.2.134.150"
        self.position_robo_1 = np.array([0., 0., 0., 0., 0., 0.])
        self.status_robo_1 = 0
        self.width_box_robo = 150
        self.height_box_robo = 200
        self.origin_x_box_robo_1 = self.webcam_x_pixel
        self.origin_y_box_robo_1 = self.webcam_y_pixel        
        self.box_robo_1 = pygame.Rect(self.origin_x_box_robo_1,
                                          self.origin_y_box_robo_1,
                                          self.width_box_robo,
                                          self.height_box_robo)
        # roboter 2
        self.reset_arm_2 = False
        self.ip_arm_2 = "10.2.134.151"
        self.position_robo_2 = np.array([0., 0., 0., 0., 0., 0.])
        self.status_robo_2 = 0
        self.origin_x_box_robo_2 = self.webcam_x_pixel + self.webcam_width - self.width_box_robo
        self.origin_y_box_robo_2 = self.webcam_y_pixel      
        self.box_robo_2 = pygame.Rect(self.origin_x_box_robo_2,
                                          self.origin_y_box_robo_2,
                                          self.width_box_robo,
                                          self.height_box_robo)
        
        

    def webcam_to_pygame(self, frame: tuple, rotation:bool=False, flip:bool=False):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if rotation:
            frame = np.rot90(frame)
        if flip:
           frame = np.flipud(frame) 

        pygame_frame = pygame.surfarray.make_surface(frame)
        resized_pygame_frame = pygame.transform.scale(pygame_frame, (self.webcam_width, self.webcam_height))
        return resized_pygame_frame
    
    def text_field(self,screen: pygame.Surface):   
        if self.typing_active:
            if self.current_time - self.cursor_timer > self.cursor_blink_interval:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = self.current_time
            else:
                pass
        else:
            self.cursor_visible = False
        
        wrapped_lines = wrap_text(self.user_text, self.font_big, self.text_display_width)
        required_height = len(wrapped_lines) * self.font_big.get_height() + \
                      (len(wrapped_lines) - 1) * self.LINE_SPACING + 10
        
        self.input_box_rect.height = max(self.MIN_INPUT_BOX_HEIGHT, required_height)

        border_color = DARK_BLUE
        pygame.draw.rect(screen, border_color, self.input_box_rect, 4)
        pygame.draw.rect(screen, LIGHT_BLUE, self.input_box_rect.inflate(-4, -4))

        current_text_y = self.input_box_rect.y + 5 
        last_line_rect = None

        for line in wrapped_lines:
            line_surface = self.font_big.render(line, True, DARK_BLUE)
            line_rect = line_surface.get_rect(topleft=(self.input_box_rect.x + 5, current_text_y))
            screen.blit(line_surface, line_rect)
            current_text_y += self.font_big.get_height() + self.LINE_SPACING
            last_line_rect = line_rect

        if self.typing_active and self.cursor_visible and last_line_rect:
            cursor_x = last_line_rect.right
            cursor_y = last_line_rect.y
            cursor_height = self.font_big.get_height()
            pygame.draw.line(screen, DARK_BLUE, (cursor_x, cursor_y), (cursor_x, cursor_y + cursor_height), 2)
        elif self.typing_active and self.cursor_visible:
            cursor_x = self.input_box_rect.x + 5 
            cursor_y = self.input_box_rect.y + (self.input_box_rect.height - self.font_big.get_height()) // 2
            cursor_height = self.font_big.get_height()
            pygame.draw.line(screen, DARK_BLUE, (cursor_x, cursor_y), (cursor_x, cursor_y + cursor_height), 2)
        else:
            pass

    def record_field(self,screen: pygame.Surface):   
        if self.recording_active:
            if self.current_time - self.cursor_timer > self.cursor_blink_interval:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = self.current_time
            else:
                pass
        else:
            self.cursor_visible = False
        
        
        border_color = DARK_BLUE
        pygame.draw.rect(screen, border_color, self.record_box_rect, 4)
        pygame.draw.rect(screen, LIGHT_BLUE, self.record_box_rect.inflate(-4, -4))  


        line_surface = self.font_big.render(self.record_button_text, True, DARK_BLUE)
        line_rect = line_surface.get_rect(topleft=(self.record_box_rect.x + 15, self.record_box_rect.y + 10 ))
        screen.blit(line_surface, line_rect)


    def history_field(self,screen: pygame.Surface):
        self.box_history_y = self.input_box_rect.bottom + 20
        self.box_history_height = self.y_pixel - self.box_history_y - 60
        self.history_area_rect.topleft = (self.input_box_rect.x, self.box_history_y)
        self.history_area_rect.width = self.input_box_rect.width 
        self.history_area_rect.height = self.box_history_height

        pygame.draw.rect(screen, DARK_BLUE, self.history_area_rect, 4)
        pygame.draw.rect(screen, LIGHT_BLUE, self.history_area_rect.inflate(-4, -4)) 

        history_y_offset = 0
        line_height = self.font_big.get_height() + 2

        for i in range(len(self.input_history) -1, -1, -1): # Loop backwards
            line_text = self.input_history[i]    
            wrapped_history_lines = wrap_text(line_text, self.font_big, self.history_area_rect.width - 10)
            
            first_line=True
            for h_line in reversed(wrapped_history_lines): # Draw wrapped history lines from bottom up
                line_surface = self.font_big.render(h_line, True, DARK_BLUE)
                current_line_y = self.history_area_rect.y + self.history_area_rect.height - (history_y_offset + line_height) - 5 # 5px bottom
                current_line_x = self.history_area_rect.x + 5 

                if current_line_y < self.history_area_rect.y + 5: 
                    break

                screen.blit(line_surface, (current_line_x, current_line_y))
                history_y_offset += line_height
            else:                 
                if wrapped_history_lines: 
                    history_y_offset += self.HISTORY_SPACING

    def robo_fields(self, screen: pygame.Surface, request_robot_reset):
        # draw background area
        if request_robot_reset.is_set() or self.status_robo_1!=0:
            pygame.draw.rect(screen, LIGHT_RED, self.box_robo_1)
        else:        
            pygame.draw.rect(screen, LIGHT_BLUE, self.box_robo_1)
        self.draw_frame(screen,self.origin_x_box_robo_1,self.origin_y_box_robo_1, self.width_box_robo, self.height_box_robo)
        # display ip
        show_info_robo(screen,
                       request_robot_reset,
                       self.ip_arm_1,
                       self.origin_x_box_robo_1,
                       self.origin_y_box_robo_1,
                       self.position_robo_1,
                       self.status_robo_1,
                       self.font_big, self.font_small)
        # draw background area
        if request_robot_reset.is_set() or self.status_robo_2!=0:
            pygame.draw.rect(screen, LIGHT_RED, self.box_robo_2)
        else:        
            pygame.draw.rect(screen, LIGHT_BLUE, self.box_robo_2)
        self.draw_frame(screen,self.origin_x_box_robo_2,self.origin_y_box_robo_2, self.width_box_robo, self.height_box_robo)
        # display ip
        show_info_robo(screen,
                       request_robot_reset,
                       self.ip_arm_2,
                       self.origin_x_box_robo_2,
                       self.origin_y_box_robo_2,
                       self.position_robo_2,
                       self.status_robo_2,
                       self.font_big, self.font_small)


    def history_field_multiprocessing(self,screen: pygame.Surface, shared_data, test_mode: bool=False):
        self.box_history_y = self.input_box_rect.bottom + 20
        self.box_history_height = self.y_pixel - self.box_history_y - 60
        self.history_area_rect.topleft = (self.input_box_rect.x, self.box_history_y)
        self.history_area_rect.width = self.input_box_rect.width 
        self.history_area_rect.height = self.box_history_height

        pygame.draw.rect(screen, DARK_BLUE, self.history_area_rect, 4)
        pygame.draw.rect(screen, LIGHT_BLUE, self.history_area_rect.inflate(-4, -4)) 

        history_y_offset = 0
        line_height = self.font_big.get_height() + 2

        if not test_mode:
            self.input_history = shared_data.output_hist


        for i in range(len(self.input_history) -1, -1, -1): # Loop backwards
            line_text = self.input_history[i]    
            wrapped_history_lines = wrap_text(line_text, self.font_big, self.history_area_rect.width - 10)
            
            first_line=True
            for h_line in reversed(wrapped_history_lines): # Draw wrapped history lines from bottom up
                line_surface = self.font_big.render(h_line, True, DARK_BLUE)
                current_line_y = self.history_area_rect.y + self.history_area_rect.height - (history_y_offset + line_height) - 5 # 5px bottom
                current_line_x = self.history_area_rect.x + 5 

                if current_line_y < self.history_area_rect.y + 5: 
                    break

                screen.blit(line_surface, (current_line_x, current_line_y))
                history_y_offset += line_height
            else:                 
                if wrapped_history_lines: 
                    history_y_offset += self.HISTORY_SPACING

    def draw_webcam_image(self,image: tuple,screen: pygame.Surface):
        x = self.webcam_x_pixel
        y = self.webcam_y_pixel 
        self.draw_frame(screen,x,y, self.webcam_width, self.webcam_height)
        screen.blit(image, (x, y))
        

    def draw_frame(self, screen: pygame.Surface, x: int, y: int, width: int, height: int):
        frame_width = 2
        rect = pygame.Rect(x-frame_width, y-frame_width,width+2*frame_width, height+2*frame_width)
        pygame.draw.rect(screen, DARK_BLUE, rect, frame_width)
    
    def input_management(self):
        self.current_time = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.input_box_rect.collidepoint(event.pos):
                    self.typing_active = True 
                    if self.typing_active:
                        self.user_text = "" 
                else:
                    self.typing_active = False 
                    self.user_text = "Provide Task" 
                self.cursor_timer = self.current_time
                self.cursor_visible = True
            if event.type == pygame.KEYDOWN:
                if self.typing_active:
                    if event.key == pygame.K_BACKSPACE:
                        self.user_text = self.user_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        if self.user_text.strip() != "": # Only add if not empty
                            self.input_history.append(self.user_text) # Add current input to history
                            self.user_task = self.user_text
                        self.user_text = ""
                    else:
                        self.user_text += event.unicode
    
    def input_management_multiprocess(self, input_queue,request_robot_reset: EventClass):
        self.current_time = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.input_box_rect.collidepoint(event.pos):
                    self.typing_active = True 
                    if self.typing_active:
                        self.user_text = "" 
                elif self.box_robo_1.collidepoint(event.pos):
                    if request_robot_reset.is_set():
                        request_robot_reset.clear()
                        self.reset_arm_1 = False
                    else:
                        request_robot_reset.set()
                        self.reset_arm_1 = True
                elif self.record_box_rect.collidepoint(event.pos):
                    self.recording_active = not self.recording_active
                    if self.recording_active:
                        self.record_button_text ="Recording..."
                    else:
                        self.record_button_text ="Record Task"
                else:
                    self.typing_active = False 
                    self.user_text = "Provide Task" 
                self.cursor_timer = self.current_time
                self.cursor_visible = True
            if event.type == pygame.KEYDOWN:
                if self.typing_active:
                    if event.key == pygame.K_BACKSPACE:
                        self.user_text = self.user_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        if self.user_text.strip() != "": # Only add if not empty
                            self.input_history.append(self.user_text) # Add current input to history
                            self.user_task = self.user_text
                            input_queue.put(self.user_task)
                        self.user_text = ""
                    else:
                        self.user_text += event.unicode
                if event.key == pygame.K_ESCAPE:
                    self.running = False