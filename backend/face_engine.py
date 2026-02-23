"""
Drishyamitra - Face Detection & Recognition Engine
Replaces FileMind's extractor.py + ai_engine.py
Uses DeepFace with Facenet512, RetinaFace, and MTCNN for face processing.
"""

import os
import numpy as np
from PIL import Image
from deepface import DeepFace
from config import (
    FACE_DETECTION_BACKEND,
    FACE_RECOGNITION_MODEL,
    FACE_SIMILARITY_THRESHOLD,
    FACE_DISTANCE_METRIC
)


def detect_faces(image_path):
    """
    Detect all faces in an image and return bounding boxes + embeddings.
    
    Returns:
        list of dict: [{"bbox": {x, y, w, h}, "embedding": [...], "confidence": float}, ...]
    """
    if not os.path.exists(image_path):
        print(f"Face Engine: Image not found: {image_path}")
        return []

    try:
        # Detect faces with bounding boxes
        faces = DeepFace.extract_faces(
            img_path=image_path,
            detector_backend=FACE_DETECTION_BACKEND,
            enforce_detection=False,
            align=True
        )

        if not faces:
            return []

        results = []
        for face_data in faces:
            # Skip low-confidence detections (0.85 filters out false positives like album art)
            confidence = face_data.get("confidence", 0)
            if confidence < 0.85:
                continue

            facial_area = face_data.get("facial_area", {})
            bbox = {
                "x": facial_area.get("x", 0),
                "y": facial_area.get("y", 0),
                "w": facial_area.get("w", 0),
                "h": facial_area.get("h", 0),
            }

            # Skip tiny faces (likely from objects like posters, album art, etc.)
            MIN_FACE_SIZE = 60
            if bbox["w"] < MIN_FACE_SIZE or bbox["h"] < MIN_FACE_SIZE:
                print(f"Face Engine: Skipping tiny face ({bbox['w']}x{bbox['h']}px) in {os.path.basename(image_path)}")
                continue

            # Get face embedding using Facenet512
            embedding = get_face_embedding(image_path, facial_area)

            if embedding is not None:
                results.append({
                    "bbox": bbox,
                    "embedding": embedding,
                    "confidence": float(confidence)
                })

        print(f"Face Engine: Detected {len(results)} face(s) in {os.path.basename(image_path)}")
        return results

    except Exception as e:
        print(f"Face Engine: Detection error for {image_path}: {e}")
        return []


def get_face_embedding(image_path, facial_area=None):
    """
    Generate a face embedding vector using Facenet512.
    
    Args:
        image_path: Path to the image file
        facial_area: Optional dict with x, y, w, h for cropping
    
    Returns:
        list: Embedding vector as a list of floats, or None on failure
    """
    try:
        embeddings = DeepFace.represent(
            img_path=image_path,
            model_name=FACE_RECOGNITION_MODEL,
            detector_backend=FACE_DETECTION_BACKEND,
            enforce_detection=False
        )

        if embeddings and len(embeddings) > 0:
            return embeddings[0].get("embedding", None)
        return None

    except Exception as e:
        print(f"Face Engine: Embedding error: {e}")
        return None


def compare_faces(embedding1, embedding2):
    """
    Compare two face embeddings and return similarity score.
    
    Args:
        embedding1: First face embedding (list of floats)
        embedding2: Second face embedding (list of floats)
    
    Returns:
        float: Cosine similarity score (0.0 to 1.0)
    """
    try:
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        return float(similarity)

    except Exception as e:
        print(f"Face Engine: Comparison error: {e}")
        return 0.0


def identify_person(embedding, known_persons):
    """
    Match a face embedding against known persons.
    
    Args:
        embedding: Face embedding to identify (list of floats)
        known_persons: dict of {person_id: {"name": str, "embedding": [...]}}
    
    Returns:
        tuple: (person_id, person_name, similarity) or (None, "Unknown", 0.0)
    """
    best_match_id = None
    best_match_name = "Unknown"
    best_similarity = 0.0

    for person_id, person_data in known_persons.items():
        rep_embedding = person_data.get("embedding")
        if rep_embedding is None:
            continue

        similarity = compare_faces(embedding, rep_embedding)

        if similarity > best_similarity:
            best_similarity = similarity
            best_match_id = person_id
            best_match_name = person_data.get("name", "Unknown")

    if best_similarity >= FACE_SIMILARITY_THRESHOLD:
        print(f"Face Engine: Identified as '{best_match_name}' (sim={best_similarity:.3f})")
        return best_match_id, best_match_name, best_similarity
    else:
        print(f"Face Engine: No match found (best sim={best_similarity:.3f})")
        return None, "Unknown", best_similarity


def extract_image_metadata(image_path):
    """
    Extract metadata from an image file (size, dimensions, EXIF).
    
    Returns:
        dict: Image metadata
    """
    try:
        stats = os.stat(image_path)
        metadata = {
            "filename": os.path.basename(image_path),
            "file_size": stats.st_size,
            "created": stats.st_ctime,
        }

        # Get image dimensions
        with Image.open(image_path) as img:
            metadata["width"], metadata["height"] = img.size
            metadata["format"] = img.format

            # Extract EXIF data if available
            exif_data = {}
            if hasattr(img, "_getexif") and img._getexif():
                from PIL.ExifTags import TAGS
                raw_exif = img._getexif()
                for tag_id, value in raw_exif.items():
                    tag_name = TAGS.get(tag_id, tag_id)
                    # Only keep serializable values
                    if isinstance(value, (str, int, float)):
                        exif_data[str(tag_name)] = value
            metadata["exif"] = exif_data

        return metadata

    except Exception as e:
        print(f"Face Engine: Metadata extraction error for {image_path}: {e}")
        return {"filename": os.path.basename(image_path)}


def is_valid_image(file_path):
    """Check if a file is a valid image."""
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}:
            return False
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False
