import pygame
import numpy as np
from multiprocessing.synchronize import Event as EventClass
from multiprocessing.sharedctypes import Synchronized, SynchronizedArray
from multiprocessing.connection import Connection as ConnectionClass
import multiprocessing
import os

from .render_class_modern import GuiHandler

class PyGameApp:
    def __init__(self, fullscreen= False,uses_multiprocess:bool=False):
        pygame.init()
        self.width = 1080
        self.height = int(self.width*0.5625)
        app_name = "VLA-DuRoC"


        self.screen = pygame.display.set_mode((self.width, self.height),vsync=1)
        pygame.display.set_caption(app_name)
        self.app_loop = True

        self.GuiHandler = GuiHandler(self.width, self.height)

        script_dir = os.path.dirname(__file__)
        img_path = os.path.join(script_dir, "assets_gui/Background2.png")
        background_original = pygame.image.load(img_path).convert()
        self.background = pygame.transform.smoothscale(background_original, (self.width, self.height))
        

    def GUI_loop(self,
                stop_flag: EventClass,
                request_robot_reset: EventClass,
                request_record: EventClass,
                request_pausing_movement: EventClass,
                request_manual: EventClass,
                prompt_sender: ConnectionClass,
                test_mode: bool=False): 
        clock = pygame.time.Clock()   
        while self.GuiHandler.running:
            time_delta = clock.tick(60)/1000.0
            if stop_flag.is_set():
                self.GuiHandler.running = False

            self.screen.blit(self.background, (0, 0))

            self.GuiHandler.update_chat_box()        

            self.GuiHandler.input_management(prompt_sender,
                                             request_record,
                                             request_robot_reset,
                                             request_pausing_movement,
                                             request_manual)       
            
            self.GuiHandler.manager.update(time_delta)
            self.GuiHandler.manager.draw_ui(self.screen)            

            self.refresh_frame()
        stop_flag.set()

    def refresh_frame(self):
        pygame.display.flip()

    def destroy(self):
        pygame.quit()