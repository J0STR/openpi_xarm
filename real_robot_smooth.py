import multiprocessing

from my_scripts.robot_process import robot_loop
from my_scripts.model_process import model_loop


if __name__ =="__main__":
    stop_runtime = multiprocessing.Event()
    model_loaded = multiprocessing.Event()
    obs_receiver, obs_sender = multiprocessing.Pipe()
    output_receiver, output_sender = multiprocessing.Pipe()


    process_robot = multiprocessing.Process(target=robot_loop, args=(stop_runtime,
                                                                     model_loaded,
                                                                     obs_sender,
                                                                     output_receiver,
                                                                     ))
    process_robot.start()


    process_model = multiprocessing.Process(target=model_loop, args=(stop_runtime,
                                                                     model_loaded,
                                                                     obs_receiver,
                                                                     output_sender,
                                                                     ))
    process_model.start()
    
    try:
        process_robot.join()
        process_model.join()
    except KeyboardInterrupt:
        process_robot.join(timeout=5)
        process_model.join(timeout=5)