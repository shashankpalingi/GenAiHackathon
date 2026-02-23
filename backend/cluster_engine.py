"""
Drishyamitra - Face Clustering Engine
Adapted from FileMind cluster_engine.py
Clusters faces into person groups instead of text into topic groups.
Uses face embeddings + cosine similarity with the same threshold pattern.
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os
import shutil
from storage import load_storage, save_storage
from naming_engine import get_person_label
from config import FACE_SIMILARITY_THRESHOLD, ORGANIZED_FOLDER

# Global state
person_clusters = {}  # {person_id: [photo_paths]}
storage = load_storage()

# Rebuild person clusters from storage on startup
if storage:
    for person_id, person_data in storage.items():
        person_clusters[person_id] = list(person_data.get("photos", {}).keys())


def add_face(photo_path, face_embedding, bbox, metadata=None):
    """
    Add a detected face to the clustering system.
    Assigns to existing person or creates a new person group.
    
    Adapted from FileMind's add_file() — same centroid similarity logic,
    but operates on face embeddings instead of text embeddings.
    
    Args:
        photo_path: Absolute path to the photo
        face_embedding: Face embedding vector (list of floats)
        bbox: Bounding box dict {x, y, w, h}
        metadata: Optional image metadata dict
    """
    global person_clusters, storage

    photo_path = os.path.abspath(photo_path)
    face_emb = np.array(face_embedding)

    if metadata is None:
        metadata = {}

    face_record = {
        "bbox": bbox,
        "embedding": face_embedding if isinstance(face_embedding, list) else face_embedding.tolist(),
        "photo_path": photo_path,
    }

    # FIRST PERSON → create first person group
    if not person_clusters:
        person_id = "person_0"
        label = get_person_label(person_id)

        person_clusters[person_id] = [photo_path]
        storage[person_id] = {
            "name": label,
            "representative_embedding": face_emb.tolist(),
            "photos": {
                photo_path: [face_record]
            },
            "metadata": {
                photo_path: metadata
            },
            "face_count": 1
        }

        save_storage(storage)
        print(f"Cluster Engine: Created first person '{label}' with {os.path.basename(photo_path)}")
        return person_id

    # CHECK EXISTING PERSONS — same pattern as FileMind's cluster matching
    best_similarity = -1
    best_person_id = None

    for person_id, person_data in storage.items():
        rep_embedding = person_data.get("representative_embedding")
        if rep_embedding is None:
            continue

        rep_emb = np.array(rep_embedding)
        similarity = cosine_similarity([face_emb], [rep_emb])[0][0]

        print(f"Cluster Engine: Similarity with {person_data.get('name', person_id)} = {similarity:.3f}")

        if similarity > best_similarity:
            best_similarity = similarity
            best_person_id = person_id

    # MATCH FOUND → add to existing person
    if best_similarity >= FACE_SIMILARITY_THRESHOLD and best_person_id:
        pid = best_person_id

        if pid not in person_clusters:
            person_clusters[pid] = []
        person_clusters[pid].append(photo_path)

        # Add face to person's photos
        if photo_path not in storage[pid]["photos"]:
            storage[pid]["photos"][photo_path] = []
        storage[pid]["photos"][photo_path].append(face_record)

        storage[pid]["metadata"][photo_path] = metadata

        # Update representative embedding (running average — same as FileMind's centroid update)
        all_embeddings = []
        for faces_in_photo in storage[pid]["photos"].values():
            for face in faces_in_photo:
                if "embedding" in face:
                    all_embeddings.append(np.array(face["embedding"]))

        if all_embeddings:
            new_rep = np.mean(all_embeddings, axis=0)
            storage[pid]["representative_embedding"] = new_rep.tolist()

        storage[pid]["face_count"] = sum(
            len(faces) for faces in storage[pid]["photos"].values()
        )

        # Refresh label periodically (same pattern as FileMind)
        if storage[pid]["face_count"] % 10 == 0:
            storage[pid]["name"] = get_person_label(pid)

        save_storage(storage)
        print(f"Cluster Engine: Added to '{storage[pid]['name']}' (sim={best_similarity:.3f})")
        return pid

    # NO MATCH → create new person
    new_id = f"person_{len(storage)}"
    label = get_person_label(new_id)

    person_clusters[new_id] = [photo_path]
    storage[new_id] = {
        "name": label,
        "representative_embedding": face_emb.tolist(),
        "photos": {
            photo_path: [face_record]
        },
        "metadata": {
            photo_path: metadata
        },
        "face_count": 1
    }

    save_storage(storage)
    print(f"Cluster Engine: New person '{label}' created for {os.path.basename(photo_path)}")
    return new_id


def rename_person(person_id, new_name):
    """Rename a person (user-triggered)."""
    global storage
    if person_id in storage:
        old_name = storage[person_id].get("name", person_id)
        storage[person_id]["name"] = new_name
        save_storage(storage)
        print(f"Cluster Engine: Renamed '{old_name}' → '{new_name}'")
        return True
    return False


def get_person_photos(person_id):
    """Get all photos for a person."""
    if person_id in storage:
        return list(storage[person_id].get("photos", {}).keys())
    return []


def get_all_persons():
    """Get summary of all known persons."""
    persons = {}
    for person_id, data in storage.items():
        persons[person_id] = {
            "name": data.get("name", person_id),
            "face_count": data.get("face_count", 0),
            "photo_count": len(data.get("photos", {}))
        }
    return persons


def sync_folders(root_path=None):
    """
    Organize photos into person-named folders.
    Adapted from FileMind's sync_folders — same folder creation + file move pattern.
    """
    global storage

    if root_path is None:
        root_path = ORGANIZED_FOLDER

    os.makedirs(root_path, exist_ok=True)

    for person_id, person_data in storage.items():
        person_name = person_data.get("name", person_id)

        # Sanitize folder name
        safe_name = "".join(c for c in person_name if c.isalnum() or c in ("_", "-", " "))
        if not safe_name:
            safe_name = person_id

        person_folder = os.path.join(root_path, safe_name)
        os.makedirs(person_folder, exist_ok=True)

        updates = {}
        for photo_path in list(person_data.get("photos", {}).keys()):
            if not os.path.exists(photo_path):
                continue

            filename = os.path.basename(photo_path)
            destination = os.path.join(person_folder, filename)

            # Move if not already in the correct folder
            if os.path.abspath(photo_path) != os.path.abspath(destination):
                try:
                    shutil.copy2(photo_path, destination)  # Copy instead of move (keep original)
                    updates[photo_path] = destination
                    print(f"Cluster Engine: Organized {filename} → {safe_name}/")
                except Exception as e:
                    print(f"Cluster Engine: Move error: {e}")

        # Update storage with new paths
        for old_path, new_path in updates.items():
            face_data = person_data["photos"].pop(old_path)
            person_data["photos"][new_path] = face_data

    save_storage(storage)

    # Prune empty folders (same as FileMind)
    for item in os.listdir(root_path):
        item_path = os.path.join(root_path, item)
        if os.path.isdir(item_path) and not os.listdir(item_path):
            print(f"Cluster Engine: Pruning empty folder: {item}")
            try:
                os.rmdir(item_path)
            except Exception:
                pass
