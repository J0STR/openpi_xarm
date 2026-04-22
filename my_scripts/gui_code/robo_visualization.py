import pygame

WHITE = (255, 255, 255)
LIGHT_RED = (218,27,38)
BACKGROUND = (235,249,255)
LIGHT_BLUE = (164,212,233)
DARK_BLUE = (0,159,227)

def show_info_robo(screen: pygame.Surface, request_robot_reset, ip_robo,  origin_x_box_robo, origin_y_box_robo, position_robo,robo_status, font_big, font_small):
   
    line_surface = font_big.render('IP:', True, WHITE)
    line_rect = line_surface.get_rect(topleft=(origin_x_box_robo + 5, origin_y_box_robo+5))
    screen.blit(line_surface, line_rect)
    line_surface = font_small.render(ip_robo, True, DARK_BLUE)
    line_rect = line_surface.get_rect(topleft=(origin_x_box_robo + 5, origin_y_box_robo+25))
    screen.blit(line_surface, line_rect)
    # display pos
    line_surface = font_big.render('XYZ:', True, WHITE)
    line_rect = line_surface.get_rect(topleft=(origin_x_box_robo + 5, origin_y_box_robo+55))
    screen.blit(line_surface, line_rect)
    line_surface = font_small.render(f"{position_robo[0]:.1f},{position_robo[1]:.1f},{position_robo[2]:.1f}", True, DARK_BLUE)
    line_rect = line_surface.get_rect(topleft=(origin_x_box_robo + 5, origin_y_box_robo+75))
    screen.blit(line_surface, line_rect)
    line_surface = font_big.render('Rotation:', True, WHITE)
    line_rect = line_surface.get_rect(topleft=(origin_x_box_robo + 5, origin_y_box_robo+105))
    screen.blit(line_surface, line_rect)
    line_surface = font_small.render(f"{position_robo[3]:.1f},{position_robo[4]:.1f},{position_robo[5]:.1f}", True, DARK_BLUE)
    line_rect = line_surface.get_rect(topleft=(origin_x_box_robo + 5, origin_y_box_robo+125))
    screen.blit(line_surface, line_rect)
    # display status
    line_surface = font_big.render('Status:', True, WHITE)
    line_rect = line_surface.get_rect(topleft=(origin_x_box_robo + 5, origin_y_box_robo+155))
    screen.blit(line_surface, line_rect)
    
    line_surface = font_small.render(str(robo_status), True, DARK_BLUE)
    line_rect = line_surface.get_rect(topleft=(origin_x_box_robo + 5, origin_y_box_robo+175))
    screen.blit(line_surface, line_rect)
   