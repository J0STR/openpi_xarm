#from lerobot
from lerobot.utils.import_utils import register_third_party_plugins
from lerobot.robots import make_robot_from_config
from lerobot_robot_dual_xarm7.lerobot_robot_dual_xarm7.config_dual_xarm7 import Dual_xArm7Config
from lerobot.utils.robot_utils import precise_sleep

from multiprocessing.synchronize import Event as EventClass
from multiprocessing.connection import Connection as ConnectionClass

import time
import numpy as np

FPS = 10
ACTIONS_TO_EXECUTE = 10

def robot_loop_buffering(stop_runtime: EventClass,
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
    action_index_when_received = 0
    action_index_when_started_with_new_input = 0


    try:
        # wait till model is loaded
        while not model_loaded.is_set():
            pass
        # actual loop
        while not stop_runtime.is_set():
            t0 = time.perf_counter()

            observation = robot.get_observation()

            # if output_receiver.poll():  # Check if there's a new output from the model                
            #     output = output_receiver.recv()
            #     action_index_when_received = action_index
            #     action_index_when_started_with_new_input = action_index - action_index_when_started_with_new_input
            #     print(f"Step {step}: Received new model output at current action index: {action_index_when_received}")
            #     print(f"action_index_when_started_with_new_input = {action_index}")
            #     obs_sender.send(observation)
            #     previous_actions = last_actions
            #     new_actions = output["actions"]
                
            #     last_actions = previous_actions[action_index_when_received:10]
            #     print(last_actions)
            #     action_index = 1 + action_index_when_started_with_new_input
            #     print(f"new action index= {action_index}")

            if output_receiver.poll():  
                output = output_receiver.recv()                
                # 1. Capture state before update
                action_index_when_received = action_index
                print(f"Step {step}: Received new model output at current action index: {action_index_when_received}")                
                # 2. Extract remaining old actions and the new actions
                # We take from current action_index to the end of the current buffer
                remaining_old_actions = last_actions[action_index_when_received:10]
                new_actions = np.array(output["actions"])                 
                # 3. Calculate how many new actions we need to fill back up to 10
                num_to_take_from_new = 10 - len(remaining_old_actions)
                
                # 4. Merge them: [Old Remaining] + [Start of New]
                last_actions = np.concatenate([
                    remaining_old_actions, 
                    new_actions[:num_to_take_from_new]
                ], axis=0)                
                # 5. Reset the index! 
                # Because last_actions[0] is now the next action to execute
                action_index = 0                 
                # Optional: Update your tracking variables for latency analysis
                action_index_when_started_with_new_input = action_index_when_received                 
                # Send observation to the model for the NEXT prediction cycle
                obs_sender.send(observation)                
                print(f"Merged actions. Buffer length: {len(last_actions)}. Next action index reset to 0.")

            if last_actions is None:
                observation = robot.get_observation()
                
                # send obs -->
                obs_sender.send(observation)
                # <-- receive model output
                # receive with timeout to avoid blocking if model is slow                
                output = output_receiver.recv()

                observation = robot.get_observation()
                obs_sender.send(observation)

                last_actions = output["actions"]
                action_index = 0

                print(f"Step {step}: Initialized scheme")
            elif action_index >= min(ACTIONS_TO_EXECUTE, len(last_actions)):
                print(f"Step {step}: executed full horizon of actions")
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