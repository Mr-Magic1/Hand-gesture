import json
import os
import math
import numpy as np
import time
import joblib
from sklearn.ensemble import RandomForestClassifier

# Map HaGRID labels to our gesture names
HAGRID_TO_OURS = {
    "one": "POINT",
    "peace": "TWO_FINGERS",
    "two_up": "TWO_FINGERS",
    "three": "THREE_FINGERS",
    "palm": "OPEN_PALM",
    "fist": "FIST",
    "like": "THUMBS_UP",
    "rock": "ROCK",
    "mute": "GUN",
}

ANN_DIR = "ann_train_val"
MAX_SAMPLES_PER_CLASS = 15000  # Adjust based on speed (15k * 8 classes = 120k samples)

def normalize_landmarks(landmarks):
    """
    Translates landmarks so wrist is at (0,0), then scales so max distance from wrist is 1.0.
    landmarks is a list of [x, y] coordinates for 21 points.
    Returns a flattened list of 42 floats.
    """
    if not landmarks or len(landmarks) < 21:
        return None
    
    xs = [pt[0] for pt in landmarks]
    ys = [pt[1] for pt in landmarks]
    
    wrist_x, wrist_y = xs[0], ys[0]
    
    # Translate to wrist
    xs = [x - wrist_x for x in xs]
    ys = [y - wrist_y for y in ys]
    
    # Find max distance to scale
    max_dist = max(math.hypot(x, y) for x, y in zip(xs, ys))
    if max_dist == 0:
        return None
        
    # Scale and flatten (x0, y0, x1, y1, ...)
    features = []
    for x, y in zip(xs, ys):
        features.extend([x / max_dist, y / max_dist])
        
    return features

def main():
    if not os.path.exists(ANN_DIR):
        print(f"Error: {ANN_DIR} not found!")
        return

    features = []
    labels_int = []
    
    # Create an int-to-string label map
    label_map = list(set(HAGRID_TO_OURS.values()))
    label_to_int = {name: i for i, name in enumerate(label_map)}

    print("Loading JSON files and extracting features...")
    
    # Track counts per target class to balance the dataset
    class_counts = {name: 0 for name in label_map}
    
    for filename in os.listdir(ANN_DIR):
        if not filename.endswith(".json"): continue
        
        hagrid_label = filename.replace(".json", "").replace("_inverted", "")
        if hagrid_label not in HAGRID_TO_OURS:
            continue
            
        target_label = HAGRID_TO_OURS[hagrid_label]
        target_int = label_to_int[target_label]
        
        if class_counts[target_label] >= MAX_SAMPLES_PER_CLASS:
            continue

        file_path = os.path.join(ANN_DIR, filename)
        print(f"Parsing {filename} -> {target_label}...")
        
        with open(file_path, "r") as f:
            data = json.load(f)
            
        for img_id, ann in data.items():
            if class_counts[target_label] >= MAX_SAMPLES_PER_CLASS:
                break
                
            ann_labels = ann.get("labels", [])
            ann_landmarks = ann.get("landmarks", [])
            
            for lbl, lms in zip(ann_labels, ann_landmarks):
                # Ensure the individual hand label matches what we're looking for
                if lbl.replace("_inverted", "") == hagrid_label:
                    feat = normalize_landmarks(lms)
                    if feat is not None:
                        features.append(feat)
                        labels_int.append(target_int)
                        class_counts[target_label] += 1
                        
                        if class_counts[target_label] >= MAX_SAMPLES_PER_CLASS:
                            break

    print("\nExtraction complete! Class counts:")
    for name, count in class_counts.items():
        print(f" - {name}: {count}")
        
    print(f"\nTotal samples: {len(features)}")
    
    print("\nTraining scikit-learn Random Forest model... this may take a few minutes.")
    start_time = time.time()
    
    # Convert to numpy arrays
    X = np.array(features, dtype=np.float32)
    y = np.array(labels_int, dtype=np.int32)
    
    # Setup Random Forest
    rf = RandomForestClassifier(n_estimators=100, max_depth=20, min_samples_split=5, random_state=42, n_jobs=-1)
    
    # Train
    rf.fit(X, y)
    
    print(f"Training finished in {time.time() - start_time:.1f} seconds!")
    
    # Save the model
    model_path = "gesture_rf_model.pkl"
    joblib.dump(rf, model_path)
    print(f"Saved model to {model_path}")
    
    # Save the label map
    with open("gesture_label_map.json", "w") as f:
        json.dump(label_map, f)
    print("Saved label map to gesture_label_map.json")

if __name__ == "__main__":
    main()
