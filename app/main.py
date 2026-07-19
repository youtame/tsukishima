import cv2
import numpy as np
import psycopg2
from fastapi import FastAPI, UploadFile, File, HTTPException
from deepface import DeepFace

app = FastAPI(
    title="Face Recognition API",
    description="API that matches target faces against 512-dimensional database records and returns the top 4 most similar matches."
)

DB_URL = "postgresql://genius:tensai102do@db:5432/tsukishima_face_db"

def get_db_connection():
    return psycopg2.connect(DB_URL)

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Face Recognition API is running"}

@app.post("/search", summary="Execute Face Recognition (Selects Top 4 Matches)")
async def search_face(file: UploadFile = File(..., description="The query image file to recognize (e.g., frame cropped from video)")):
    # 1. Decode the uploaded image file in memory (Safely bypasses non-ASCII/Japanese path issues)
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file.")
    
    try:
        # 2. Extract 512-dimensional features from the query image.
        # Since target inputs might be cropped or poorly angled, using 'mtcnn' ensures robust face detection.
        embedding_objs = DeepFace.represent(
            img_path=img,
            model_name="ArcFace",
            detector_backend="mtcnn",
            enforce_detection=True
        )
        target_embedding = embedding_objs[0]["embedding"]
        
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not detect face. Please check the angle or image quality: {str(e)}")
    
    # 3. Perform a cosine similarity vector search against the DB and select the top 4 records.
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # '<=>' is the pgvector cosine distance operator. 
        # Cosine Similarity = 1 - Cosine Distance.
        cur.execute("""
            SELECT user_code, name, (1 - (face_embedding <=> %s::vector)) AS similarity
            FROM users
            ORDER BY face_embedding <=> %s::vector ASC
            LIMIT 4;
        """, (target_embedding, target_embedding))
        
        results = cur.fetchall()
        cur.close()
        conn.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error occurred: {str(e)}")
        
    # 4. Format the final JSON response payload
    response_data = []
    for rank, (user_code, name, similarity) in enumerate(results, 1):
        # Convert raw similarity value into a percentage confidence score (clamped between 0 and 100)
        confidence = max(0.0, min(100.0, similarity * 100))
        
        response_data.append({
            "rank": rank,
            "user_code": user_code,
            "name": name,
            "confidence": f"{round(confidence, 2)}%"
        })
        
    return {"results": response_data}