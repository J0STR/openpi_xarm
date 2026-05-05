from my_scripts.gui_code.app_modern import PyGameApp
from multiprocessing.synchronize import Event as EventClass
from multiprocessing.connection import Connection as ConnectionClass

def gui_loop(stop_runtime: EventClass,
             request_record: EventClass,
             request_robot_reset: EventClass,
             request_pausing_movement: EventClass,
             request_manual: EventClass,
             prompt_sender: ConnectionClass,
             fullscreen = False,
             test_mode: bool = False):
    
    App = PyGameApp(fullscreen=fullscreen,uses_multiprocess=True)
    App.GUI_loop(stop_runtime,
                          request_robot_reset,
                          request_record,
                          request_pausing_movement,
                          request_manual,
                          prompt_sender,
                          test_mode)
    App.destroy()