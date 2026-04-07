# pipeline.py
import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""  # disables GPU completely
os.environ["FORCE_CUDA"] = "0"          # optional, just in case
import cv2
import json
import numpy as np
import pandas as pd
from pathlib import Path
import torch
import torch.nn as nn
import albumentations as A
from albumentations.pytorch import ToTensorV2
import segmentation_models_pytorch as smp


# =========================================================
# CONFIG / CONSTANTS
# =========================================================

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

PATCH_SIZE = 256
STRIDE = 128

# =========================================================
# CLASS DEFINITIONS (ALIGNED WITH YOUR NOTEBOOK)
# =========================================================

CLASS_NAMES = {
    0: "Analog",
    113: "Digital",
    174: "Ram/Rom",
    201: "Rom",
    109: "RF",
    124: "IO/Pad ring",
    169: "Cache",
    92: "PDN",
    164: "SRAM",
    72: "DMOS",
    97: "Flash"
}

CLASS_COLORS = {
    0:   (0, 0, 0),         # background
    113: (250, 50, 83),     # digital
    174: (51, 221, 255),    # ram/rom
    201: (255, 204, 51),    # rom
    109: (42, 125, 209),    # rf
    124: (250, 50, 183),    # io/pad ring
    169: (61, 245, 61),     # cache
    92:  (192, 15, 228),    # pdn
    164: (221, 140, 140),   # sram
    72:  (9, 110, 42),      # dmos
    97:  (241, 18, 127)     # flash
}

RAW_IDS = sorted(CLASS_NAMES.keys())
NUM_CLASSES = len(RAW_IDS)

RAW_TO_IDX = {rid: idx for idx, rid in enumerate(RAW_IDS)}
IDX_TO_RAW = {idx: rid for rid, idx in RAW_TO_IDX.items()}
IDX_TO_NAME = {RAW_TO_IDX[rid]: CLASS_NAMES[rid] for rid in RAW_IDS}
IDX_TO_COLOR = {RAW_TO_IDX[rid]: CLASS_COLORS[rid] for rid in RAW_IDS}

COLOR_TO_IDX = {
    CLASS_COLORS[rid]: RAW_TO_IDX[rid]
    for rid in RAW_IDS
}

# =========================================================
# TRANSFORM (ALIGNED WITH VALIDATION / INFERENCE)
# =========================================================

val_transform = A.Compose([
    A.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5)),
    ToTensorV2()
])


# =========================================================
# MODEL UTILITIES
# =========================================================

def get_model(arch="Unet", encoder="resnet34", num_classes=NUM_CLASSES):
    if arch == "Unet":
        model = smp.Unet(
            encoder_name=encoder,
            encoder_weights=None,
            in_channels=3,
            classes=num_classes
        )
    elif arch == "FPN":
        model = smp.FPN(
            encoder_name=encoder,
            encoder_weights=None,
            in_channels=3,
            classes=num_classes
        )
    elif arch == "DeepLabV3Plus":
        model = smp.DeepLabV3Plus(
            encoder_name=encoder,
            encoder_weights=None,
            in_channels=3,
            classes=num_classes
        )
    else:
        raise ValueError(f"Unsupported architecture: {arch}")
    return model


def load_trained_model(arch, encoder, weight_path, device=DEVICE):
    model = get_model(arch=arch, encoder=encoder).to(device)
    state = torch.load(weight_path, map_location=device)
    model.load_state_dict(state)
    model.eval()
    return model


# =========================================================
# MASK / COLOR UTILITIES
# =========================================================

def rgb_mask_to_class_mask(mask_rgb):
    """
    Convert RGB mask to contiguous class IDs [0..NUM_CLASSES-1]
    """
    h, w, _ = mask_rgb.shape
    class_mask = np.zeros((h, w), dtype=np.uint8)

    for color, class_idx in COLOR_TO_IDX.items():
        matches = np.all(mask_rgb == np.array(color), axis=-1)
        class_mask[matches] = class_idx

    return class_mask


def class_mask_to_rgb(mask_class):
    """
    Convert class mask [0..NUM_CLASSES-1] back to RGB visualization
    """
    h, w = mask_class.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for class_idx, color in IDX_TO_COLOR.items():
        rgb[mask_class == class_idx] = color
    return rgb


# =========================================================
# IMAGE PREPROCESSING (VERY IMPORTANT - ALIGNED WITH TRAINING)
# =========================================================

def create_3channel_input(gray_img):
    """
    Create the exact 3-channel representation used during training:
    [gray, clahe, sharpen]
    """
    gray = gray_img.copy()

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    sharpen = cv2.addWeighted(gray, 1.5, blur, -0.5, 0)

    img_3ch = np.stack([gray, clahe, sharpen], axis=-1)
    return img_3ch


# =========================================================
# PATCH / SLIDING WINDOW UTILITIES
# =========================================================

def get_patch_positions(h, w, patch_size, stride):
    ys = list(range(0, max(h - patch_size + 1, 1), stride))
    xs = list(range(0, max(w - patch_size + 1, 1), stride))

    if len(ys) == 0 or ys[-1] != h - patch_size:
        ys.append(max(h - patch_size, 0))
    if len(xs) == 0 or xs[-1] != w - patch_size:
        xs.append(max(w - patch_size, 0))

    return ys, xs


def prepare_patch_for_model(gray_patch):
    """
    Prepare one patch exactly like training pipeline.
    """
    patch_3ch = create_3channel_input(gray_patch)

    transformed = val_transform(
        image=patch_3ch,
        mask=np.zeros((gray_patch.shape[0], gray_patch.shape[1]), dtype=np.uint8)
    )

    x_tensor = transformed["image"].unsqueeze(0).to(DEVICE)
    return x_tensor


@torch.no_grad()
def predict_full_image_with_sliding_window(model, gray_img, patch_size=PATCH_SIZE, stride=STRIDE):
    """
    Predict one full grayscale image using sliding-window patch inference.
    Returns:
        pred_mask: [H, W]
        prob_map: [C, H, W]
    """
    h, w = gray_img.shape
    ys, xs = get_patch_positions(h, w, patch_size, stride)

    prob_map = np.zeros((NUM_CLASSES, h, w), dtype=np.float32)
    count_map = np.zeros((h, w), dtype=np.float32)

    for y in ys:
        for x in xs:
            patch = gray_img[y:y+patch_size, x:x+patch_size]

            patch_h_actual, patch_w_actual = patch.shape[:2]

            if patch_h_actual != patch_size or patch_w_actual != patch_size:
                padded = np.zeros((patch_size, patch_size), dtype=np.uint8)
                padded[:patch_h_actual, :patch_w_actual] = patch
                patch = padded

            x_tensor = prepare_patch_for_model(patch)

            logits = model(x_tensor)
            probs = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()  # [C,H,W]

            patch_h = min(patch_size, h - y)
            patch_w = min(patch_size, w - x)

            prob_map[:, y:y+patch_h, x:x+patch_w] += probs[:, :patch_h, :patch_w]
            count_map[y:y+patch_h, x:x+patch_w] += 1

    prob_map /= np.maximum(count_map[None, :, :], 1e-7)
    pred_mask = np.argmax(prob_map, axis=0).astype(np.uint8)

    return pred_mask, prob_map


@torch.no_grad()
def predict_full_image_ensemble(models, gray_img, patch_size=PATCH_SIZE, stride=STRIDE, weights=None):
    """
    Ensemble prediction from multiple models using weighted probability averaging.
    """
    if weights is None:
        weights = [1.0] * len(models)

    h, w = gray_img.shape
    ensemble_prob = np.zeros((NUM_CLASSES, h, w), dtype=np.float32)

    total_weight = sum(weights)

    for model, wgt in zip(models, weights):
        _, prob_map = predict_full_image_with_sliding_window(
            model, gray_img, patch_size=patch_size, stride=stride
        )
        ensemble_prob += prob_map * wgt

    ensemble_prob /= total_weight
    pred_mask = np.argmax(ensemble_prob, axis=0).astype(np.uint8)

    return pred_mask, ensemble_prob


# =========================================================
# OVERLAY / VISUALIZATION UTILITIES
# =========================================================

def overlay_mask_on_image(gray_img, pred_mask, alpha=0.45):
    """
    Overlay predicted mask on grayscale image.
    """
    rgb_img = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2RGB)
    rgb_mask = class_mask_to_rgb(pred_mask)
    overlay = cv2.addWeighted(rgb_img, 1 - alpha, rgb_mask, alpha, 0)
    return overlay


# =========================================================
# AREA CALCULATION
# =========================================================

def calculate_class_areas_from_pred_mask(
    pred_mask,
    image_height_real=None,
    image_width_real=None,
    real_unit="um"
):
    """
    Calculate:
    1. pixel count per class
    2. percentage ratio per class
    3. actual real-world area per class (if real image size is given)

    pred_mask: [H, W] class index mask
    image_height_real: actual real image height (user-provided)
    image_width_real: actual real image width (user-provided)
    real_unit: measurement unit string
    """

    h, w = pred_mask.shape
    total_pixels = h * w

    has_real_size = (
        image_height_real is not None and
        image_width_real is not None and
        image_height_real > 0 and
        image_width_real > 0
    )

    if has_real_size:
        pixel_height = image_height_real / h
        pixel_width = image_width_real / w
        pixel_area_real = pixel_height * pixel_width
        total_real_area = image_height_real * image_width_real
    else:
        pixel_height = None
        pixel_width = None
        pixel_area_real = None
        total_real_area = None

    rows = []

    for class_idx in range(NUM_CLASSES):
        pixel_count = int(np.sum(pred_mask == class_idx))
        ratio_percent = (pixel_count / total_pixels) * 100 if total_pixels > 0 else 0.0

        row = {
            "class_idx": class_idx,
            "raw_id": IDX_TO_RAW[class_idx],
            "class_name": IDX_TO_NAME[class_idx],
            "pixel_count": pixel_count,
            "ratio_percent": ratio_percent
        }

        if has_real_size:
            actual_area = pixel_count * pixel_area_real
            row[f"actual_area_{real_unit}2"] = actual_area

        rows.append(row)

    df = pd.DataFrame(rows).sort_values("pixel_count", ascending=False).reset_index(drop=True)

    summary = {
        "mask_height_px": int(h),
        "mask_width_px": int(w),
        "total_pixels": int(total_pixels),
        "has_real_size": bool(has_real_size),
        "image_height_real": image_height_real,
        "image_width_real": image_width_real,
        "real_unit": real_unit,
        "pixel_height_real": pixel_height,
        "pixel_width_real": pixel_width,
        "pixel_area_real": pixel_area_real,
        "total_real_area": total_real_area
    }

    return df, summary


# =========================================================
# SAVE UTILITIES
# =========================================================

def save_area_results(area_df, summary, save_csv_path, save_json_path):
    area_df.to_csv(save_csv_path, index=False)

    with open(save_json_path, "w") as f:
        json.dump(summary, f, indent=4)

    return {
        "csv_path": save_csv_path,
        "json_path": save_json_path
    }


def save_prediction_outputs(
    save_dir,
    image_name,
    pred_mask,
    overlay_img
):
    os.makedirs(save_dir, exist_ok=True)

    pred_rgb = class_mask_to_rgb(pred_mask)

    pred_path = os.path.join(save_dir, f"{image_name}_ensemble_pred.png")
    overlay_path = os.path.join(save_dir, f"{image_name}_ensemble_overlay.png")

    cv2.imwrite(pred_path, cv2.cvtColor(pred_rgb, cv2.COLOR_RGB2BGR))
    cv2.imwrite(overlay_path, cv2.cvtColor(overlay_img, cv2.COLOR_RGB2BGR))

    return {
        "pred_mask_path": pred_path,
        "overlay_path": overlay_path
    }


# =========================================================
# MAIN PIPELINE CLASS
# =========================================================

class ChipSegmentationPipeline:
    def __init__(self, model_configs, device=DEVICE):
        """
        model_configs: list of dicts like:
        [
            {"arch": "Unet", "encoder": "resnet34", "weight_path": "..."},
            ...
        ]
        """
        self.device = device
        self.model_configs = model_configs
        self.models = []
        self._load_models()

    def _load_models(self):
        self.models = []
        for cfg in self.model_configs:
            model = load_trained_model(
                arch=cfg["arch"],
                encoder=cfg["encoder"],
                weight_path=cfg["weight_path"],
                device=self.device
            )
            self.models.append(model)

    def predict_image(
        self,
        image_path,
        image_height_real=None,
        image_width_real=None,
        real_unit="um",
        save_dir=None,
        alpha=0.45,
        weights=None
    ):
        """
        Main full pipeline for one image.
        Returns structured dictionary for GUI/backend usage.
        """

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        image_name = Path(image_path).stem

        gray_img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if gray_img is None:
            raise ValueError(f"Could not read image: {image_path}")

        # Ensemble prediction
        pred_mask, prob_map = predict_full_image_ensemble(
            self.models,
            gray_img,
            patch_size=PATCH_SIZE,
            stride=STRIDE,
            weights=weights
        )

        # Overlay
        overlay_img = overlay_mask_on_image(gray_img, pred_mask, alpha=alpha)

        # Area calculation
        area_df, area_summary = calculate_class_areas_from_pred_mask(
            pred_mask=pred_mask,
            image_height_real=image_height_real,
            image_width_real=image_width_real,
            real_unit=real_unit
        )

        save_paths = {}
        if save_dir is not None:
            os.makedirs(save_dir, exist_ok=True)

            pred_save = save_prediction_outputs(
                save_dir=save_dir,
                image_name=image_name,
                pred_mask=pred_mask,
                overlay_img=overlay_img
            )

            area_csv_path = os.path.join(save_dir, f"{image_name}_ensemble_area_report.csv")
            area_json_path = os.path.join(save_dir, f"{image_name}_ensemble_area_summary.json")

            area_save = save_area_results(
                area_df=area_df,
                summary=area_summary,
                save_csv_path=area_csv_path,
                save_json_path=area_json_path
            )

            save_paths = {**pred_save, **area_save}

        return {
            "image_name": image_name,
            "gray_image": gray_img,
            "pred_mask": pred_mask,
            "overlay_image": overlay_img,
            "prob_map": prob_map,
            "area_df": area_df,
            "area_summary": area_summary,
            "save_paths": save_paths
        }