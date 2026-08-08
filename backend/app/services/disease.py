from pathlib import Path
import cv2
import numpy as np

def analyse_leaf(path: Path) -> dict:
    image = cv2.imread(str(path))
    if image is None: raise ValueError("The upload is not a readable image")
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    green = cv2.inRange(hsv, np.array([25, 25, 20]), np.array([95, 255, 255]))
    yellow = cv2.inRange(hsv, np.array([15, 45, 45]), np.array([35, 255, 255]))
    brown = cv2.inRange(hsv, np.array([5, 40, 20]), np.array([20, 255, 220]))
    leaf_pixels = max(1, int(np.count_nonzero(green | yellow | brown)))
    yellow_ratio, brown_ratio = np.count_nonzero(yellow) / leaf_pixels, np.count_nonzero(brown) / leaf_pixels
    if brown_ratio > .18: disease, confidence = "Leaf spot risk", min(.95, .55 + brown_ratio)
    elif yellow_ratio > .22: disease, confidence = "Chlorosis or nutrient stress", min(.92, .52 + yellow_ratio)
    else: disease, confidence = "No visible disease pattern", .72
    treatments = {"Leaf spot risk": ["Remove heavily affected leaves with clean tools.", "Avoid overhead irrigation and improve air circulation.", "Confirm crop-specific diagnosis with local extension support before treatment."], "Chlorosis or nutrient stress": ["Check soil pH and nutrient availability.", "Inspect roots and drainage before applying fertilizer.", "Use a soil test to choose any corrective nutrient."], "No visible disease pattern": ["Continue weekly scouting, including leaf undersides.", "Avoid wet foliage late in the day."]}
    return {"disease_name": disease, "confidence": round(confidence, 2), "symptoms": "Yellowing and necrotic-area ratios were measured from the uploaded leaf image.", "treatment": treatments[disease], "organic_treatment": "Use clean pruning, crop residue sanitation, and compost-supported soil health.", "expected_recovery": "Reassess in 7–10 days after correcting the identified stress."}
