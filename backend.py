# backend.py

import os
import cv2

from pipeline import ChipSegmentationPipeline, class_mask_to_rgb


# =========================================================
# MODEL CONFIGURATION
# =========================================================
# Update these paths according to where your .pth files are stored.

MODEL_CONFIGS = [
    {
        "arch": "Unet",
        "encoder": "resnet34",
        "weight_path": "models/Unet_resnet34_best.pth"
    },
    {
        "arch": "Unet",
        "encoder": "efficientnet-b0",
        "weight_path": "models/Unet_efficientnet-b0_best.pth"
    },
    {
        "arch": "FPN",
        "encoder": "resnet34",
        "weight_path": "models/FPN_resnet34_best.pth"
    },
    {
        "arch": "DeepLabV3Plus",
        "encoder": "mobilenet_v2",
        "weight_path": "models/DeepLabV3Plus_mobilenet_v2_best.pth"
    }
]


# =========================================================
# BACKEND WRAPPER CLASS
# =========================================================

class SegmentationBackend:
    """
    PyQt5-friendly backend wrapper.
    main.py should interact with this class only.
    """

    def __init__(self, model_configs=None):
        if model_configs is None:
            model_configs = MODEL_CONFIGS

        self.model_configs = model_configs
        self.pipeline = None

    # ---------------------------------------------------------
    # MODEL LOADING
    # ---------------------------------------------------------
    def load_models(self):
        """
        Load all trained models once.
        Call this once when app starts.
        """
        self.pipeline = ChipSegmentationPipeline(self.model_configs)
        return True

    def is_ready(self):
        """
        Check whether models are loaded.
        """
        return self.pipeline is not None

    # ---------------------------------------------------------
    # MAIN PREDICTION FUNCTION (THIS IS WHAT main.py WILL CALL)
    # ---------------------------------------------------------
    def predict_image_from_gui(
        self,
        image_path,
        image_height_real=None,
        image_width_real=None,
        real_unit="um",
        save_dir="outputs",
        alpha=0.45,
        weights=None
    ):
        """
        Main function for PyQt5 / main.py usage.

        Parameters:
            image_path (str): path of selected grayscale chip image
            image_height_real (float, optional): actual real chip height
            image_width_real (float, optional): actual real chip width
            real_unit (str): unit like 'um', 'mm'
            save_dir (str): output folder
            alpha (float): overlay transparency
            weights (list, optional): ensemble weights

        Returns:
            dict: prediction results
        """
        if self.pipeline is None:
            raise RuntimeError("Models are not loaded. Call load_models() first.")

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        result = self.pipeline.predict_image(
            image_path=image_path,
            image_height_real=image_height_real,
            image_width_real=image_width_real,
            real_unit=real_unit,
            save_dir=save_dir,
            alpha=alpha,
            weights=weights
        )

        return result

    # ---------------------------------------------------------
    # OPTIONAL HELPERS FOR GUI DISPLAY
    # ---------------------------------------------------------
    # def get_overlay_for_qt(self, overlay_image_rgb):
    #     """
    #     Convert RGB overlay image to BGR if needed for OpenCV/PyQt handling.
    #     """
    #     return cv2.cvtColor(overlay_image_rgb, cv2.COLOR_RGB2BGR)

    # def get_pred_mask_rgb(self, pred_mask):
    #     """
    #     Convert predicted class mask to RGB visualization.
    #     """
    #     return class_mask_to_rgb(pred_mask)

    def get_output_paths(self, result_dict):
        """
        Convenience helper for GUI if you only want saved file paths.
        """
        return result_dict.get("save_paths", {})

    def get_area_table(self, result_dict):
        """
        Return pandas DataFrame of area results.
        """
        return result_dict.get("area_df", None)

    def get_area_summary(self, result_dict):
        """
        Return summary dictionary of measurement results.
        """
        return result_dict.get("area_summary", {})