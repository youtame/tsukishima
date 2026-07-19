import os
import glob
import psycopg2
import cv2
import numpy as np
from deepface import DeepFace

# Database connection URL and configuration constants
DB_URL = "postgresql://genius:tensai102do@db:5432/tsukishima_face_db"
IMAGE_DIR = "/app/scripts/images"

def get_db_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    return psycopg2.connect(DB_URL)

def register_faces():
    """
    Scans the image directory, extracts face embeddings using MTCNN/ArcFace,
    calculates an average vector per user, and upserts the records into the database.
    """
    # Retrieve file paths matching target image extensions
    image_paths = glob.glob(os.path.join(IMAGE_DIR, "*.jpg")) + glob.glob(os.path.join(IMAGE_DIR, "*.png"))
    
    if not image_paths:
        print(f"No image files found in {IMAGE_DIR}.")
        return

    # Dictionary map to group embeddings by unique user code
    # Structure: { user_code: { "name": "...", "embeddings": [ [...] , [...] ] } }
    user_data_map = {}

    print(f"Analyzing {len(image_paths)} images and extracting feature vectors...")
    print("-" * 70)

    for path in image_paths:
        filename = os.path.basename(path)
        basename = os.path.splitext(filename)[0]  # e.g., "224999_Genius_Railway-2" or "224999_Genius_Railway"
        
        # Strip branch indices / trailing modifiers (e.g., "-2") from the file name
        if "-" in basename:
            basename = basename.split("-")[0]  # "224999_Genius_Railway-2" -> "224999_Genius_Railway"
            
        parts = basename.split("_")
        if len(parts) < 3:
            print(f"Skipped due to invalid naming convention: {filename}")
            continue
            
        user_code = parts[0]
        name = f"{parts[1]} {parts[2]}"
        
        try:
            # Safe image loading workaround for paths containing non-ASCII / Japanese characters
            img_array = np.fromfile(path, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if img is None:
                print(f"Failed to decode image content: {filename}")
                continue

            # Extract features (Using the high-accuracy 'mtcnn' detector backend to prevent misses)
            embedding_objs = DeepFace.represent(
                img_path=img,
                model_name="ArcFace",
                detector_backend="mtcnn",
                enforce_detection=True
            )
            embedding = embedding_objs[0]["embedding"]
            
            # Initialize or accumulate data records in the mapping memory block
            if user_code not in user_data_map:
                user_data_map[user_code] = {"name": name, "embeddings": []}
            
            user_data_map[user_code]["embeddings"].append(embedding)
            print(f"Extracted embedding: [{user_code}] {name} ({filename})")
            
        except Exception as e:
            print(f"Analysis failed: {filename} - Reason: {str(e)}")

    # Database Persistence & Sync Phase
    print("\nCommencing database synchronization (Vector Averaging Phase)...")
    print("-" * 70)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    for user_code, data in user_data_map.items():
        name = data["name"]
        embeddings = data["embeddings"]
        
        if not embeddings:
            continue
            
        # Compute the unified vector center-point across all provided image profiles
        mean_embedding = np.mean(embeddings, axis=0).tolist()
        
        try:
            # Upsert operations (Conflict handling refreshes the record identity state)
            cur.execute("""
                INSERT INTO users (user_code, name, face_embedding) 
                VALUES (%s, %s, %s::vector)
                ON CONFLICT (user_code) 
                DO UPDATE SET 
                    name = EXCLUDED.name,
                    face_embedding = EXCLUDED.face_embedding;
            """, (user_code, name, mean_embedding))
            
            conn.commit()
            print(f"Synced average vector: [{user_code}] {name} (Integrated {len(embeddings)} images)")
        except Exception as e:
            conn.rollback()
            print(f"Database write failure: [{user_code}] {name} - Reason: {str(e)}")

    cur.close()
    conn.close()
    print("-" * 70)
    print("Core initial registration pipeline run finalized successfully.")

if __name__ == "__main__":
    register_faces()