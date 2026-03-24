import os
# Configure JAX memory allocation before importing JAX-related modules
# Is needed to resolve possible issues with memory allocation
os.environ["XLA_PYTHON_CLIENT_MEM_FRACTION"] = "0.9"

import time
import numpy as np

from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig
from lerobot.utils.robot_utils import precise_sleep

# Import Pi0 model from openpi
from openpi.training import config as pi05_config
from openpi.policies import policy_config
from huggingface_hub import snapshot_download

#my imports
from openpi.shared import download
from openpi.training import config as _config
#from lerobot
from lerobot.utils.import_utils import register_third_party_plugins
from lerobot.robots import make_robot_from_config
from lerobot_robot_dual_xarm7.lerobot_robot_dual_xarm7.config_dual_xarm7 import Dual_xArm7Config

# Configuration
FPS = 30
TASK_DESCRIPTION = "Grab the rubics cube and place it in the box."
ACTIONS_TO_EXECUTE = 10  # Execute this many actions from each predicted chunk

# Load Pi0 model
print("Loading Pi0 model...")

# Use your robot Pi0 config - in my case "pi0_lekiwi_fast", "pi0_lekiwi" or "pi05_lekiwi"
config = pi05_config.get_config("pi05_xarm_dual")

# Use you trained policy HF directory
# You should upload your model (assets and params directories from the checkpoint) to Hugging Face to use it here
checkpoint_dir = download.maybe_download("/home/jonas/coding/openpi_xarm/checkpoints/sort_w_pushing_20k")
pi0_policy = policy_config.create_trained_policy(config, checkpoint_dir)
print("Pi0 model loaded successfully")

# Connect to robot
# Use your robot IP and ID
register_third_party_plugins()
robot_config = Dual_xArm7Config()
robot = make_robot_from_config(robot_config)
robot.connect()

if not robot.is_connected:
    raise ValueError("Robot is not connected!")

print(f"Robot connected. Starting control loop with task: '{TASK_DESCRIPTION}'")
print(f"Will execute {ACTIONS_TO_EXECUTE} actions from each predicted chunk")

# Control loop variables
step = 0
last_actions = None
action_index = 0
pred_times = []

while True:
    t0 = time.perf_counter()
    
    # Run prediction when we need new actions (either first time or when we've executed enough actions)
    if last_actions is None or action_index >= min(ACTIONS_TO_EXECUTE, len(last_actions)):
        # Get robot observation
        observation = robot.get_observation()

        state_keys = [f"right_joint_{i+1}.pos" for i in range(7)] + ["right_gripper.pos"] + [f"left_joint_{i+1}.pos" for i in range(7)] + ["left_gripper.pos"]
        states = np.array([observation[key] for key in state_keys])

        # Prepare input for Pi0
        # Adjust for your robot
        pi0_input = {
            "prompt": TASK_DESCRIPTION,
            "observation.state": states,
        }
        
        for k in ["top_down", "wrist_right", "wrist_left"]:
            pi0_input[f"observation.images.{k}"] = observation[k]
        
        # Run inference
        t_pred_start = time.perf_counter()
        output = pi0_policy.infer(pi0_input)
        t_pred = time.perf_counter() - t_pred_start
        
        # Keep track of last 10 prediction times
        pred_times.append(t_pred)
        pred_times = pred_times[-10:]  # Keep last 10
        
        last_actions = output["actions"]
        action_index = 0

        print(f"Step {step}: Predicted {len(last_actions)} actions, will execute {min(ACTIONS_TO_EXECUTE, len(last_actions))}")
        print(f"Prediction took {t_pred:.3f}s (avg over last {len(pred_times)}: {np.mean(pred_times):.3f}s)")
    
    # Execute action
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
    
    # Maintain FPS
    precise_sleep(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))