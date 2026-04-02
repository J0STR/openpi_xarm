#from lerobot
from lerobot.utils.import_utils import register_third_party_plugins
from lerobot.robots import make_robot_from_config
from lerobot_robot_dual_xarm7.lerobot_robot_dual_xarm7.config_dual_xarm7 import Dual_xArm7Config
from lerobot.utils.robot_utils import precise_sleep

from multiprocessing.synchronize import Event as EventClass
from multiprocessing.connection import Connection as ConnectionClass

import time

FPS = 30
ACTIONS_TO_EXECUTE = 10

def robot_loop(stop_runtime: EventClass,
               model_loaded: EventClass,
               obs_sender: ConnectionClass,
               output_receiver:ConnectionClass,
               ):
    
    register_third_party_plugins()
    robot_config = Dual_xArm7Config()
    robot = make_robot_from_config(robot_config)
    robot.connect()
    print('Robot connected')

    step = 0
    last_actions = None
    action_index = 0


    try:
        # wait till model is loaded
        while not model_loaded.is_set():
            pass
        # actual loop
        while not stop_runtime.is_set():
            t0 = time.perf_counter()

            if last_actions is None or action_index >= min(ACTIONS_TO_EXECUTE, len(last_actions)):
                observation = robot.get_observation()
                
                # send obs -->
                obs_sender.send(observation)
                # <-- receive model output
                output = output_receiver.recv()

                last_actions = output["actions"]
                action_index = 0

                print(f"Step {step}: Predicted {len(last_actions)} actions, will execute {min(ACTIONS_TO_EXECUTE, len(last_actions))}")
            else:
                # Get current action from the sequence
                action = last_actions[action_index]
                
                # Convert action array to robot's expected format        
                action_dict = {}
                for i, action_name in enumerate(list(robot.action_features.keys())):
                    if i < len(action):
                        action_dict[action_name] = action[i]
                
                robot.send_action(action_dict)
                action_index += 1
                step += 1                   

            precise_sleep(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))

    except KeyboardInterrupt:
        stop_runtime.set()

    robot.disconnect()
    print('Ended process Robot')