from openpi.training import config as pi05_config
from openpi.policies import policy_config
from openpi.shared import download

from multiprocessing.synchronize import Event as EventClass
from multiprocessing.connection import Connection as ConnectionClass
import numpy as np
import time

TASK_DESCRIPTION = "Do nothing"

def model_loop(stop_runtime: EventClass,
               model_loaded: EventClass,
               request_pause: EventClass,
               obs_receiver: ConnectionClass,
               prompt_receiver:ConnectionClass,
               output_sender: ConnectionClass,
               model_config: str,
               model_path: str
               ):
    
    print('Loading Model...')
    config = pi05_config.get_config(model_config)
    checkpoint_dir = download.maybe_download(model_path)
    pi0_policy = policy_config.create_trained_policy(config, checkpoint_dir)
    model_loaded.set()
    prompt = TASK_DESCRIPTION
    observation = None
    print('Model Loaded')
    pred_times = [] 
    try:
        while not stop_runtime.is_set():

            while observation is None:
                if obs_receiver.poll(2.0):
                    observation = obs_receiver.recv()
                if stop_runtime.is_set():
                    break

            if observation is None:
                break

            if prompt_receiver.poll():
                # take latest prompt
                while prompt_receiver.poll():
                    prompt = prompt_receiver.recv()
            

            state_keys = [f"right_joint_{i+1}.pos" for i in range(7)] + ["right_gripper.pos"] + [f"left_joint_{i+1}.pos" for i in range(7)] + ["left_gripper.pos"]
            states = np.array([observation[key] for key in state_keys])
            
            print(f"Prompt is: {prompt}")

            # Prepare input for Pi0
            # Adjust for robot
            pi0_input = {
                "prompt": prompt,
                "observation.state": states,
            }
            
            for k in ["top_down", "wrist_right", "wrist_left"]:
                pi0_input[f"observation.images.{k}"] = observation[k]
            
            # Run inference
            t_pred_start = time.perf_counter()
            output = pi0_policy.infer(pi0_input)
            output_sender.send(output)
            t_pred = time.perf_counter() - t_pred_start
            
            # Reset Observation
            observation = None
            # Keep track of last 10 prediction times
            pred_times.append(t_pred)
            pred_times = pred_times[-10:]  # Keep last 10

            print(f"Prediction took {t_pred:.3f}s (avg over last {len(pred_times)}: {np.mean(pred_times):.3f}s)")

    except KeyboardInterrupt:
        print('Ended process Model')