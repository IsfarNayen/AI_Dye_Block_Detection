from pathlib import Path
import cv2
from ultralytics import YOLO


def pipeline(input_image_path):
    """
    Run node classification on a given input image path.

    Args:
        input_image_path (str or Path): Path of the input image passed from main.py

    Returns:
        dict: Prediction result containing:
              - image_path
              - node_name
              - confidence
    """
    output_json = {}

    input_image_path = Path(input_image_path)

    if not input_image_path.exists():
        raise FileNotFoundError(f"Input image not found: {input_image_path}")

    # Model path
    base_dir = Path(__file__).resolve().parent
    model_path = (
        base_dir.parent.parent.parent
        / "models"
        / "ai_Node_identification"
        / "node_classification_weights.pt"
    )

    print(f"Loading model: {model_path}")
    model = YOLO(model_path)

    # Output folder
    output_dir = base_dir.parent.parent.parent / "models" / "ai_Node_identification" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run prediction
    new_predictions = model.predict(source=str(input_image_path), conf=0.25, verbose=False)

    for pred in new_predictions:
        img_name = Path(pred.path).name

        class_name = None
        confidence = None

        if len(pred.boxes) > 0:
            for box in pred.boxes:
                class_name = pred.names[int(box.cls)]
                confidence = float(box.conf)

        else:
            output_json["image_path"] = None
            output_json["node_name"] = None
            output_json["confidence"] = None

        img_rgb = cv2.cvtColor(pred.plot(), cv2.COLOR_BGR2RGB)

        save_path = output_dir / img_name
        cv2.imwrite(str(save_path), img_rgb)

        output_json["image_path"] = str(save_path)
        output_json["node_name"] = class_name
        output_json["confidence"] = confidence
        
        model = None

    return output_json