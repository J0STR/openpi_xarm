import socket
import cv2
import numpy as np
import struct
import time

from openpi.training import config as pi05_config
from openpi.policies import policy_config
from openpi.shared import download

TASK_DESCRIPTION = "Place the blue cube in the lower right corner"

def recv_all(sock, n):
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet: return None
        data.extend(packet)
    return data


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', 12345))
    print("Connected to Isaac Sim. Waiting for events...")

    data_names = {
        0: "top_down",
        1: "wrist_right",
        2: "wrist_left"
    }

    print('Loading Model...')
    config = pi05_config.get_config("pi05_xarm_dual")
    checkpoint_dir = download.maybe_download("/home/jonas/coding/openpi_xarm/checkpoints/big_data_20k_steps")
    pi0_policy = policy_config.create_trained_policy(config, checkpoint_dir)

    print('Model Loaded')
    pred_times = [] 


    try:
        while True:
            # Read Header
            obs_dict = {}
            header_raw = recv_all(sock, 16)
            if header_raw is None: 
                break
            start = time.perf_counter()
            j_len, i0_len, i1_len, i2_len = struct.unpack('IIII', header_raw)
            
            # Read Payload based on header
            joint_data = recv_all(sock, j_len)
            img0_data = recv_all(sock, i0_len)
            img1_data = recv_all(sock, i1_len)
            img2_data = recv_all(sock, i2_len)

            if any(v is None for v in [joint_data, img0_data, img1_data, img2_data]):
                break
            
            # Receive
            joints = np.frombuffer(joint_data, dtype=np.float32)
            frame_top_view = cv2.imdecode(np.frombuffer(img0_data, np.uint8), cv2.IMREAD_COLOR)            
            frame_wrist_right = cv2.imdecode(np.frombuffer(img1_data, np.uint8), cv2.IMREAD_COLOR)            
            frame_wrist_left = cv2.imdecode(np.frombuffer(img2_data, np.uint8), cv2.IMREAD_COLOR)
            
            # Make Dict
            joints_right = joints[:8]
            joints_left = joints[8:]            
            for i, angle in enumerate(joints_right):  # store angle,velocity and effort
                if i<7:
                    obs_dict[f"right_joint_{i+1}.pos"] = angle
                else:
                    obs_dict["right_gripper.pos"] = angle
            for i, angle in enumerate(joints_left):  # store angle,velocity and effort
                if i<7:
                    obs_dict[f"left_joint_{i+1}.pos"] = angle
                else:
                    obs_dict["left_gripper.pos"] = angle
            obs_dict[data_names[0]] = frame_top_view
            obs_dict[data_names[1]] = frame_wrist_right
            obs_dict[data_names[2]] = frame_wrist_left

            cv_converted_frame = cv2.cvtColor(obs_dict[data_names[0]], cv2.COLOR_RGB2BGR)            
            window_name = data_names.get(0, f"Unknown Camera {0}")
            cv2.imshow(window_name, cv_converted_frame)

            ###
            # Inference
            state_keys = [f"right_joint_{i+1}.pos" for i in range(7)] + ["right_gripper.pos"] + [f"left_joint_{i+1}.pos" for i in range(7)] + ["left_gripper.pos"]
            states = np.array([obs_dict[key] for key in state_keys])

            # Prepare input for Pi0
            # Adjust for your robot
            pi0_input = {
                "prompt": TASK_DESCRIPTION,
                "observation.state": states,
            }
            
            for k in ["top_down", "wrist_right", "wrist_left"]:
                pi0_input[f"observation.images.{k}"] = obs_dict[k]
            
            # Run inference
            t_pred_start = time.perf_counter()
            output = pi0_policy.infer(pi0_input)
            ###
            # Send output to isaacsim
            actions = output["actions"].astype(np.float32)
            chunk_bytes = actions.tobytes()
            sock.sendall(struct.pack('I', len(chunk_bytes)) + chunk_bytes)
            ###
            t_pred = time.perf_counter() - t_pred_start
            
            # Keep track of last 10 prediction times
            pred_times.append(t_pred)
            pred_times = pred_times[-10:]  # Keep last 10
            
            end = time.perf_counter()

    except KeyboardInterrupt:
        sock.close()
    finally:
        sock.close()


if __name__ == "__main__":
    main()