import multiprocessing

from my_scripts.robot_process import robot_loop_gui
from my_scripts.model_process import model_loop_gui
from my_scripts.gui_code.GUI import gui_loop


if __name__ =="__main__":
    stop_runtime = multiprocessing.Event()
    model_loaded = multiprocessing.Event()
    request_sound_record = multiprocessing.Event()
    request_robot_reset = multiprocessing.Event()
    request_pausing_movement = multiprocessing.Event()
    request_pausing_movement.set()
    request_manual = multiprocessing.Event()

    obs_receiver, obs_sender = multiprocessing.Pipe()
    output_receiver, output_sender = multiprocessing.Pipe()
    prompt_receiver, prompt_sender = multiprocessing.Pipe()


    process_robot = multiprocessing.Process(target=robot_loop_gui, args=(stop_runtime,
                                                                     model_loaded,
                                                                     request_robot_reset,
                                                                     request_pausing_movement,
                                                                     request_manual,
                                                                     obs_sender,
                                                                     output_receiver,
                                                                     ))
    process_robot.start()


    process_model = multiprocessing.Process(target=model_loop_gui, args=(stop_runtime,
                                                                     model_loaded,
                                                                     request_pausing_movement,
                                                                     obs_receiver,
                                                                     prompt_receiver,
                                                                     output_sender,
                                                                     ))
    process_model.start()


    process_gui = multiprocessing.Process(target=gui_loop, args=(stop_runtime,
                                                                 request_sound_record,
                                                                request_robot_reset,
                                                                request_pausing_movement,
                                                                request_manual,
                                                                prompt_sender))
    process_gui.start()
    
    try:
        process_robot.join()
        process_model.join()
    except KeyboardInterrupt:
        process_robot.join(timeout=5)
        process_model.join(timeout=5)

    process_gui.join()