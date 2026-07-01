import dataclasses
import einops
import numpy as np
from openpi import transforms
from openpi.models import model as _model

def _parse_image(image) -> np.ndarray:
    image = np.asarray(image)
    if np.issubdtype(image.dtype, np.floating):
        image = (255 * image).astype(np.uint8)
    # LeRobot often provides (C, H, W), OpenPI wants (H, W, C)
    if image.shape[0] == 3:
        image = einops.rearrange(image, "c h w -> h w c")
    return image

@dataclasses.dataclass(frozen=True)
class SpotInputs(transforms.DataTransformFn):
    # Do not change this for your own dataset.
    action_dim: int

    # Determines which model will be used.
    # Do not change this for your own dataset.
    model_type: _model.ModelType = _model.ModelType.PI05

    def __call__(self, data: dict) -> dict:
        state = transforms.pad_to_dim(data["observation.state"], self.action_dim)

        gripper = _parse_image(data["observation.images.gripper"])
        front_left = _parse_image(data["observation.images.front_left"])
        front_right = _parse_image(data["observation.images.front_right"])

        inputs = {
            "state": data["observation.state"],
            "image": {
                "base_0_rgb": gripper,
                "left_wrist_0_rgb": front_left,
                "right_wrist_0_rgb": front_right,
            },
            "image_mask": {
                "base_0_rgb": np.True_,
                "left_wrist_0_rgb": np.True_,
                "right_wrist_0_rgb": np.True_,
            },
        }

        if "action" in data:
            actions = transforms.pad_to_dim(data["action"], self.action_dim)
            inputs["actions"] = actions

        if "prompt" in data:
            inputs["prompt"] = data["prompt"]

        return inputs

@dataclasses.dataclass(frozen=True)
class SpotOutputs(transforms.DataTransformFn):
    def __call__(self, data: dict) -> dict:
        return {"actions": np.asarray(data["actions"][:, :10])}