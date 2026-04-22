#from lerobot
from lerobot.utils.import_utils import register_third_party_plugins
from lerobot.robots import make_robot_from_config
from lerobot_robot_dual_xarm7.lerobot_robot_dual_xarm7.config_dual_xarm7 import Dual_xArm7Config
from lerobot_robot_dual_xarm7.lerobot_robot_dual_xarm7.dual_xarm7 import Dual_xArm7
from lerobot.utils.robot_utils import precise_sleep

from multiprocessing.synchronize import Event as EventClass
from multiprocessing.connection import Connection as ConnectionClass

import time
import numpy as np

FPS = 30
ACTIONS_TO_EXECUTE = 10

init_pose = np.array([-0.020695317536592484,
                       -0.979644238948822,
                         -0.008580705150961876,
                           0.6497616767883301,
                             0.018501725047826767,
                               1.630096197128296,
                                 -0.0007919175550341606])

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


def robot_loop_gui(stop_runtime: EventClass,
               model_loaded: EventClass,
               request_reset: EventClass,
               request_pausing_movement: EventClass,
               request_manual: EventClass,
               obs_sender: ConnectionClass,
               output_receiver:ConnectionClass,
               ):
    
    register_third_party_plugins()
    robot_config = Dual_xArm7Config()
    robot: Dual_xArm7 = make_robot_from_config(robot_config)
    robot.connect()
    print('Robot connected')

    step = 0
    last_actions = None
    action_index = 0
    output = None

    dt = 1/30 # 30 Hz
    v_joints = np.pi/4 # 90 deg/s
    error_threshold = 0.01

    manual_mode = False

    try:
        while not stop_runtime.is_set():
            t0 = time.perf_counter()

            # wait till model is loaded
            if not model_loaded.is_set():
                continue
            
            # handle reset 
            if request_reset.is_set():
                code_left, [joints_left, velocity, effort] = robot.robot_left.get_joint_states(is_radian=True)
                code_right, [joints_right, velocity, effort] = robot.robot_right.get_joint_states(is_radian=True)
                code, gripper_pos_left = robot.robot_left.get_gripper_position()
                code, gripper_pos_right = robot.robot_right.get_gripper_position()
                # left robot
                code_robo, [error_code_robo, warn_code]= robot.robot_left.get_err_warn_code()
                if code_robo == 0 and error_code_robo!=0: 
                    robot.robot_left.motion_enable(enable=True)
                    robot.robot_left.set_mode(1)
                    robot.robot_left.set_state(0)
                else:
                    delta_left = init_pose - joints_left
                    error_norm_left = np.linalg.norm(delta_left)
                    delta_left = np.clip(delta_left,-v_joints*dt,v_joints*dt)
                    angles_left = joints_left + delta_left
                # right robot
                code_robo, [error_code_robo, warn_code]= robot.robot_right.get_err_warn_code()
                if code_robo == 0 and error_code_robo!=0: 
                    robot.robot_right.motion_enable(enable=True)
                    robot.robot_right.set_mode(1)
                    robot.robot_right.set_state(0)
                else:
                    delta_right = init_pose - joints_right
                    error_norm_right = np.linalg.norm(delta_right)
                    delta_right = np.clip(delta_right,-v_joints*dt,v_joints*dt)
                    angles_right = joints_right + delta_right
                action_left = np.hstack((angles_left,gripper_pos_left))
                action_right = np.hstack((angles_right,gripper_pos_right))

                if error_norm_left < error_threshold and error_norm_right < error_threshold:
                    request_reset.clear()
                    print("Reset complete: Threshold reached.")

                # write action to dict
                action = {f"right_joint_{i+1}.pos": val for i, val in enumerate(action_right[:-1])}
                action["right_gripper.pos"] = action_right[-1]
                action.update({f"left_joint_{i+1}.pos": val for i, val in enumerate(action_left[:-1])})
                action["left_gripper.pos"] = action_left[-1]

                # send
                robot.send_action(action)
                # get new trajectory after
                action_index = 100

            # handle manual
            elif request_manual.is_set() or manual_mode:
                
                if not request_manual.is_set():
                    manual_mode = False
                    robot.robot_left.motion_enable(enable=True)
                    robot.robot_left.set_mode(1)
                    robot.robot_left.set_state(0)
                    robot.robot_right.motion_enable(enable=True)
                    robot.robot_right.set_mode(1)
                    robot.robot_right.set_state(0)
                elif manual_mode == False:
                    manual_mode = True
                    # activate manual mode
                    robot.robot_left.motion_enable(enable=True)
                    robot.robot_left.set_mode(0)
                    robot.robot_left.set_state(0)
                    robot.robot_left.set_mode(2)
                    robot.robot_left.set_state(0)
                    # ---
                    robot.robot_right.motion_enable(enable=True)
                    robot.robot_right.set_mode(0)
                    robot.robot_right.set_state(0)
                    robot.robot_right.set_mode(2)
                    robot.robot_right.set_state(0)
                else:
                    # get new trajectory after
                    action_index = 100
                    continue                 

            # handle pause button
            elif request_pausing_movement.is_set():
                # while pausing dont move
                continue
            
            # handle policy
            elif last_actions is None or action_index >= min(ACTIONS_TO_EXECUTE, len(last_actions)):
                output = None
                observation = robot.get_observation()
                
                # send obs -->
                obs_sender.send(observation)
                # <-- receive model output
                while output is None:
                    if output_receiver.poll(timeout=2.0):
                        output = output_receiver.recv()
                    if stop_runtime.is_set():
                        break


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