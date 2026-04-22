import pygame
import numpy as np
from multiprocessing.synchronize import Event as EventClass
from multiprocessing.sharedctypes import Synchronized, SynchronizedArray
from multiprocessing.connection import Connection as ConnectionClass
import multiprocessing
import os

from pygame_gui import UIManager, UI_TEXT_ENTRY_CHANGED, UI_BUTTON_PRESSED, UI_TEXT_ENTRY_FINISHED
from pygame_gui.elements import  UITextEntryBox, UITextBox, UIImage, UIButton
from pygame_gui.core import ObjectID

class GuiHandler:
    def __init__(self, width: int, height: int):
        # general
        self.running = True
        self.x_pixel = width
        self.y_pixel = height
        self.current_time = 0
        # paths
        script_dir = os.path.dirname(__file__)
        # themes and font
        config_path = os.path.join(script_dir, "themes/theme.json")
        img_path = os.path.join(script_dir, "assets/CameraInit.jpg")
        self.manager = UIManager((self.x_pixel, self.y_pixel), config_path)
        self.manager.preload_fonts([{'name': 'noto_sans', 'point_size': 18, 'style': 'bold', 'antialiased': '1'}])

        # input text field
        self.user_task = None
        text_boxes_width = int(self.x_pixel*0.75)
        self.x_prompt_box = int((self.x_pixel/2)-0.5*text_boxes_width)
        self.y_prompt_box = int(self.y_pixel*0.3)

        self.height_prompt_box = int(self.y_pixel*0.1) 
        width_prompt_box = text_boxes_width - self.height_prompt_box - int(self.x_pixel*0.005)
        
        self.width_task_entry_box = width_prompt_box   # 10 % sreen 
        self.rect_prompt_box = pygame.Rect(self.x_prompt_box,
                                          self.y_prompt_box,
                                          self.width_task_entry_box,
                                          self.height_prompt_box)
        self.UI_prompt_box = UITextEntryBox(
            relative_rect=self.rect_prompt_box,
            initial_text="",
            manager=self.manager,
            object_id=ObjectID(class_id="text_entry_box",
                            object_id="#text_entry_box_1"),
            placeholder_text="Enter Task here..."
            )
        self.entry_done = False
        self.UI_prompt_box.blink_cursor_time = 0.6

        # chat_box
        self.y_chat_box = self.rect_prompt_box.bottom + int(self.y_pixel*0.01)
        self.width_chat_box = text_boxes_width
        self.height_chat_box = int(self.y_pixel*0.2)
        self.rect_chat_box = pygame.Rect(self.rect_prompt_box.x,
                                            self.y_chat_box,
                                            self.width_chat_box,
                                            self.height_chat_box)
        self.UI_chat_box = UITextBox(
            relative_rect=self.rect_chat_box,
            object_id=ObjectID(class_id="text_box",
                            object_id="#text_box_1"),
                            html_text='',
                            )
        self.old_text = ''
        self.text = ''

        # Push to Talk button        
        self.x_push_to_talk_box = self.x_prompt_box + self.width_task_entry_box + int(self.x_pixel*0.005)
        self.y_push_to_talk_box = self.y_prompt_box
        self.width_push_to_talk_box = self.height_prompt_box        
        self.height_push_to_talk_box = self.height_prompt_box  
        self.rect_push_to_talk_box = pygame.Rect(self.x_push_to_talk_box,
                                          self.y_push_to_talk_box,
                                          self.width_push_to_talk_box,
                                          self.height_push_to_talk_box)
        self.UI_push_to_talk = UIButton(relative_rect=self.rect_push_to_talk_box,
                                      text="",
                                      manager=self.manager,
                                      object_id='record_button_off')
        self.UI_push_to_talk.shape_corner_radius[0] = int(self.height_push_to_talk_box/2-2)
        self.UI_push_to_talk.shape_corner_radius[1] = int(self.height_push_to_talk_box/2-2)
        self.UI_push_to_talk.shape_corner_radius[2] = int(self.height_push_to_talk_box/2-2)
        self.UI_push_to_talk.shape_corner_radius[3] = int(self.height_push_to_talk_box/2-2)
        self.UI_push_to_talk.rebuild()
        self.recording_active = False
 
        # Robot Reset Button
        self.width_reset_button = self.width_push_to_talk_box
        self.height_reset_button = self.height_push_to_talk_box     
        self.x_reset_button = int((self.x_pixel/2) - self.width_reset_button/2 )
        self.y_reset_button = self.rect_chat_box.bottom + int(self.y_pixel*0.01)      
        
        self.rect_reset_button = pygame.Rect(self.x_reset_button,
                                          self.y_reset_button,
                                          self.width_reset_button,
                                          self.height_reset_button)
        self.UI_reset_button = UIButton(relative_rect=self.rect_reset_button,
                                      text="",
                                      manager=self.manager,
                                      object_id='reset_not_active_button')
        self.UI_reset_button.shape_corner_radius[0] = int(self.height_push_to_talk_box/2-2)
        self.UI_reset_button.shape_corner_radius[1] = int(self.height_push_to_talk_box/2-2)
        self.UI_reset_button.shape_corner_radius[2] = int(self.height_push_to_talk_box/2-2)
        self.UI_reset_button.shape_corner_radius[3] = int(self.height_push_to_talk_box/2-2)
        self.UI_reset_button.rebuild()
        self.reset_active = False

        # Play/Pause button        
        self.x_play_button_box = int((self.x_pixel/2) - 1.5*self.width_reset_button - int(self.x_pixel*0.005))
        self.y_play_button_box = self.rect_chat_box.bottom + int(self.y_pixel*0.01)   
        self.width_pause_button_box = self.height_prompt_box        
        self.height_pause_button_box = self.height_prompt_box  
        self.rect_pause_button_box = pygame.Rect(self.x_play_button_box,
                                          self.y_play_button_box,
                                          self.width_pause_button_box,
                                          self.height_pause_button_box)
        self.UI_play_button = UIButton(relative_rect=self.rect_pause_button_box,
                                      text="",
                                      manager=self.manager,
                                      object_id='play_button')
        self.UI_play_button.shape_corner_radius[0] = int(self.height_push_to_talk_box/2-2)
        self.UI_play_button.shape_corner_radius[1] = int(self.height_push_to_talk_box/2-2)
        self.UI_play_button.shape_corner_radius[2] = int(self.height_push_to_talk_box/2-2)
        self.UI_play_button.shape_corner_radius[3] = int(self.height_push_to_talk_box/2-2)
        self.UI_play_button.rebuild()

        self.pause_active = True

        # manual button        
        self.x_manual_box = int((self.x_pixel/2) + 0.5*self.width_reset_button + int(self.x_pixel*0.005))
        self.y_manual_box = self.rect_chat_box.bottom + int(self.y_pixel*0.01)   
        self.width_manual_box = self.height_prompt_box        
        self.height_manual_box = self.height_prompt_box  
        self.rect_manual_box = pygame.Rect(self.x_manual_box,
                                          self.y_manual_box,
                                          self.width_manual_box,
                                          self.height_manual_box)
        self.UI_manual_button = UIButton(relative_rect=self.rect_manual_box,
                                      text="",
                                      manager=self.manager,
                                      object_id='manual_inactive')
        self.UI_manual_button.shape_corner_radius[0] = int(self.height_manual_box/2-2)
        self.UI_manual_button.shape_corner_radius[1] = int(self.height_manual_box/2-2)
        self.UI_manual_button.shape_corner_radius[2] = int(self.height_manual_box/2-2)
        self.UI_manual_button.shape_corner_radius[3] = int(self.height_manual_box/2-2)
        self.UI_manual_button.rebuild()

        self.manual_active = False

        
    def update_chat_box(self):
        history_text = self.text
        if self.old_text != history_text:
            self.UI_chat_box.set_text(history_text)
            self.old_text = history_text
            if self.UI_chat_box.scroll_bar:
                self.UI_chat_box.scroll_bar.set_scroll_from_start_percentage(1.0)
    
    def input_management(self,
                         prompt_sender:ConnectionClass,
                         request_record: EventClass,
                         request_robot_reset: EventClass,
                         request_pausing_movement: EventClass,
                         request_manual: EventClass):
        self.current_time = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                if event.mod & pygame.KMOD_SHIFT: 
                    # Allow Shift+Enter to actually make a new line
                    pass 
                else:
                    text = self.UI_prompt_box.get_text().strip()
                    if text != '':
                        prompt_sender.send(text)
                        self.text += text + '<br><br>'
                    
                    self.UI_prompt_box.set_text('')
                    continue                                   

            if event.type == UI_BUTTON_PRESSED:
                if event.ui_element == self.UI_push_to_talk:
                    # Handle record Button
                    self.recording_active = not self.recording_active
                    if (self.recording_active):
                        self.UI_push_to_talk = UIButton(relative_rect=self.rect_push_to_talk_box,
                                      text="",
                                      manager=self.manager,
                                      object_id='record_button_off')
                        self.UI_push_to_talk.shape_corner_radius[0] = int(self.height_push_to_talk_box/2-2)
                        self.UI_push_to_talk.shape_corner_radius[1] = int(self.height_push_to_talk_box/2-2)
                        self.UI_push_to_talk.shape_corner_radius[2] = int(self.height_push_to_talk_box/2-2)
                        self.UI_push_to_talk.shape_corner_radius[3] = int(self.height_push_to_talk_box/2-2)
                        self.UI_push_to_talk.rebuild()
                        request_record.set()
                    else:
                        self.UI_push_to_talk = UIButton(relative_rect=self.rect_push_to_talk_box,
                                      text="",
                                      manager=self.manager,
                                      object_id='record_button_active')
                        self.UI_push_to_talk.shape_corner_radius[0] = int(self.height_push_to_talk_box/2-2)
                        self.UI_push_to_talk.shape_corner_radius[1] = int(self.height_push_to_talk_box/2-2)
                        self.UI_push_to_talk.shape_corner_radius[2] = int(self.height_push_to_talk_box/2-2)
                        self.UI_push_to_talk.shape_corner_radius[3] = int(self.height_push_to_talk_box/2-2)
                        self.UI_push_to_talk.rebuild()
                        request_record.clear()
                if event.ui_element == self.UI_reset_button:
                    # Handle record Button
                    self.reset_active = not self.reset_active
                    if (self.reset_active):
                        request_robot_reset.set()
                        self.UI_reset_button = UIButton(relative_rect=self.rect_reset_button,
                                      text="",
                                      manager=self.manager,
                                      object_id='reset_active_button')
                        self.UI_reset_button.shape_corner_radius[0] = int(self.height_reset_button/2-2)
                        self.UI_reset_button.shape_corner_radius[1] = int(self.height_reset_button/2-2)
                        self.UI_reset_button.shape_corner_radius[2] = int(self.height_reset_button/2-2)
                        self.UI_reset_button.shape_corner_radius[3] = int(self.height_reset_button/2-2)
                        self.UI_reset_button.rebuild()
                    else:
                        request_robot_reset.clear()
                        self.UI_reset_button = UIButton(relative_rect=self.rect_reset_button,
                                      text="",
                                      manager=self.manager,
                                      object_id='reset_not_active_button')
                        self.UI_reset_button.shape_corner_radius[0] = int(self.height_reset_button/2-2)
                        self.UI_reset_button.shape_corner_radius[1] = int(self.height_reset_button/2-2)
                        self.UI_reset_button.shape_corner_radius[2] = int(self.height_reset_button/2-2)
                        self.UI_reset_button.shape_corner_radius[3] = int(self.height_reset_button/2-2)
                        self.UI_reset_button.rebuild()
                if event.ui_element == self.UI_play_button:
                    # Handle record Button
                    self.pause_active = not self.pause_active
                    if (self.pause_active):
                        request_pausing_movement.set()
                        self.UI_play_button = UIButton(relative_rect=self.rect_pause_button_box,
                                      text="",
                                      manager=self.manager,
                                      object_id='play_button')
                        self.UI_play_button.shape_corner_radius[0] = int(self.height_push_to_talk_box/2-2)
                        self.UI_play_button.shape_corner_radius[1] = int(self.height_push_to_talk_box/2-2)
                        self.UI_play_button.shape_corner_radius[2] = int(self.height_push_to_talk_box/2-2)
                        self.UI_play_button.shape_corner_radius[3] = int(self.height_push_to_talk_box/2-2)
                        self.UI_play_button.rebuild()
                        

                    else:
                        request_pausing_movement.clear()
                        self.UI_play_button = UIButton(relative_rect=self.rect_pause_button_box,
                                      text="",
                                      manager=self.manager,
                                      object_id='pause_button')
                        self.UI_play_button.shape_corner_radius[0] = int(self.height_push_to_talk_box/2-2)
                        self.UI_play_button.shape_corner_radius[1] = int(self.height_push_to_talk_box/2-2)
                        self.UI_play_button.shape_corner_radius[2] = int(self.height_push_to_talk_box/2-2)
                        self.UI_play_button.shape_corner_radius[3] = int(self.height_push_to_talk_box/2-2)
                        self.UI_play_button.rebuild()

                if event.ui_element == self.UI_manual_button:
                    # Handle manual Button
                    self.manual_active = not self.manual_active
                    if (self.manual_active):
                        request_manual.set()
                        self.UI_manual_button = UIButton(relative_rect=self.rect_manual_box,
                                      text="",
                                      manager=self.manager,
                                      object_id='manual_active')
                        self.UI_manual_button.shape_corner_radius[0] = int(self.height_manual_box/2-2)
                        self.UI_manual_button.shape_corner_radius[1] = int(self.height_manual_box/2-2)
                        self.UI_manual_button.shape_corner_radius[2] = int(self.height_manual_box/2-2)
                        self.UI_manual_button.shape_corner_radius[3] = int(self.height_manual_box/2-2)
                        self.UI_manual_button.rebuild()
                        

                    else:
                        request_manual.clear()
                        self.UI_manual_button = UIButton(relative_rect=self.rect_manual_box,
                                      text="",
                                      manager=self.manager,
                                      object_id='manual_inactive')
                        self.UI_manual_button.shape_corner_radius[0] = int(self.height_manual_box/2-2)
                        self.UI_manual_button.shape_corner_radius[1] = int(self.height_manual_box/2-2)
                        self.UI_manual_button.shape_corner_radius[2] = int(self.height_manual_box/2-2)
                        self.UI_manual_button.shape_corner_radius[3] = int(self.height_manual_box/2-2)
                        self.UI_manual_button.rebuild()             
            
            self.manager.process_events(event)
        
        if ((not request_robot_reset.is_set()) and self.reset_active):
                self.reset_active = False
                self.UI_reset_button = UIButton(relative_rect=self.rect_reset_button,
                                        text="",
                                        manager=self.manager,
                                        object_id='reset_not_active_button')
                self.UI_reset_button.shape_corner_radius[0] = int(self.height_reset_button/2-2)
                self.UI_reset_button.shape_corner_radius[1] = int(self.height_reset_button/2-2)
                self.UI_reset_button.shape_corner_radius[2] = int(self.height_reset_button/2-2)
                self.UI_reset_button.shape_corner_radius[3] = int(self.height_reset_button/2-2)
                self.UI_reset_button.rebuild() 

                     
        