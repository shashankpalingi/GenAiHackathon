"""
Drishyamitra - AI-Powered Photo Management System
Flask Backend Application

Adapted from FileMind main.py (FastAPI → Flask).
Reuses: CORS setup, WebSocket for real-time updates, file upload/delete patterns.
New: Photo/Person/Chat/Delivery endpoints for face-based photo management.
"""

import os
import threading
from datetime import datetime

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO

from config import (
    UPLOAD_FOLDER, ORGANIZED_FOLDER,
    SECRET_KEY, DEBUG, HOST, PORT,
    ALLOWED_EXTENSIONS
)
from models import init_db, get_session, Photo, Person, Face, User, DeliveryHistory
from face_engine import detect_faces, extract_image_metadata, is_valid_image
from cluster_engine import (
    add_face, sync_folders, storage,
    rename_person as cluster_rename_person,
    get_person_photos, get_all_persons
)
from naming_engine import load_names_from_storage
from chatbot import process_query, clear_session
from delivery import send_email, send_whatsapp, log_delivery
from watcher import start_watching, index_existing_photos, PhotoHandler

# -----------------------------
# APP SETUP
# -----------------------------

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize database
init_db()

# Load person names from storage on startup
load_names_from_storage(storage)

# -----------------------------
# ROOT
# -----------------------------

@app.route("/")
def index():
    return jsonify({"message": "Drishyamitra Backend Running", "version": "1.0.0"})


# -----------------------------
# STATUS (adapted from FileMind)
# -----------------------------

@app.route("/status")
def system_status():
    """System status — same pattern as FileMind."""
    persons = get_all_persons()
    total_photos = sum(p.get("photo_count", 0) for p in persons.values())
    return jsonify({
        "status": "running",
        "persons": len(persons),
        "total_photos": total_photos,
        "total_faces": sum(p.get("face_count", 0) for p in persons.values())
    })


# -----------------------------
# PHOTO UPLOAD (adapted from FileMind /upload)
# -----------------------------

@app.route("/upload", methods=["POST"])
def upload_photo():
    """
    Upload a photo → detect faces → cluster → organize.
    Adapted from FileMind's /upload endpoint.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    # Validate file type
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}"}), 400

    try:
        # Save to upload folder
        dest_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(dest_path)
        print(f"Upload: Saved {file.filename} to {dest_path}")

        # Process in background thread (same pattern as FileMind)
        handler = PhotoHandler()
        thread = threading.Thread(
            target=handler.process_file,
            args=(dest_path,),
            daemon=True
        )
        thread.start()

        # Emit real-time update via WebSocket
        socketio.emit("photo_uploaded", {
            "filename": file.filename,
            "path": dest_path
        })

        return jsonify({
            "status": "success",
            "filename": file.filename,
            "path": dest_path
        })

    except Exception as e:
        print(f"Upload Error: {e}")
        return jsonify({"error": str(e)}), 500


# -----------------------------
# PHOTOS LIST (adapted from FileMind /files)
# -----------------------------

@app.route("/photos")
def list_photos():
    """
    List all photos with face/person metadata.
    Adapted from FileMind's /files endpoint.
    """
    all_photos = []
    for person_id, person_data in storage.items():
        for photo_path, faces in person_data.get("photos", {}).items():
            all_photos.append({
                "file": photo_path,
                "filename": os.path.basename(photo_path),
                "person_id": person_id,
                "person_name": person_data.get("name", "Unknown"),
                "face_count": len(faces) if isinstance(faces, list) else 0,
                "metadata": person_data.get("metadata", {}).get(photo_path, {})
            })
    return jsonify(all_photos)


# -----------------------------
# PHOTO DELETE (adapted from FileMind /files/<filename>)
# -----------------------------

@app.route("/photos/<filename>", methods=["DELETE"])
def delete_photo(filename):
    """
    Delete a photo by filename.
    Adapted from FileMind's DELETE /files/<filename>.
    """
    try:
        # Find the file recursively
        file_path = None
        for folder in [UPLOAD_FOLDER, ORGANIZED_FOLDER]:
            for root, _, files in os.walk(folder):
                if filename in files:
                    file_path = os.path.join(root, filename)
                    break
            if file_path:
                break

        if not file_path:
            return jsonify({"error": f"Photo '{filename}' not found"}), 404

        abs_path = os.path.abspath(file_path)

        # Remove from storage (same pattern as FileMind)
        removed = False
        for person_id, person_data in storage.items():
            if abs_path in person_data.get("photos", {}):
                person_data["photos"].pop(abs_path)
                if "metadata" in person_data and abs_path in person_data["metadata"]:
                    person_data["metadata"].pop(abs_path)
                removed = True
                print(f"Delete: Removed {filename} from {person_data.get('name', person_id)}")
                break

        # Delete physical file
        if os.path.exists(abs_path):
            os.remove(abs_path)

        if removed:
            from storage import save_storage
            save_storage(storage)

        socketio.emit("photo_deleted", {"filename": filename})

        return jsonify({"status": "success", "filename": filename, "removed_from_index": removed})

    except Exception as e:
        print(f"Delete Error: {e}")
        return jsonify({"error": str(e)}), 500


# -----------------------------
# PERSONS ENDPOINTS (new)
# -----------------------------

@app.route("/persons")
def list_persons():
    """List all known persons with photo counts."""
    return jsonify(get_all_persons())


@app.route("/persons/<person_id>", methods=["PUT"])
def update_person(person_id):
    """Rename a person (user names an unknown face)."""
    data = request.get_json()
    new_name = data.get("name", "").strip()

    if not new_name:
        return jsonify({"error": "Name is required"}), 400

    success = cluster_rename_person(person_id, new_name)
    if success:
        # Re-sync folders with new name
        sync_folders(ORGANIZED_FOLDER)
        socketio.emit("person_renamed", {"person_id": person_id, "name": new_name})
        return jsonify({"status": "success", "person_id": person_id, "name": new_name})
    else:
        return jsonify({"error": f"Person '{person_id}' not found"}), 404


@app.route("/persons/<person_id>/photos")
def person_photos(person_id):
    """Get all photos for a specific person."""
    photos = get_person_photos(person_id)
    if not photos:
        return jsonify({"error": f"Person '{person_id}' not found or has no photos"}), 404
    return jsonify({"person_id": person_id, "photos": photos})


# -----------------------------
# SEARCH (adapted from FileMind /search)
# -----------------------------

@app.route("/search", methods=["POST"])
def search_photos():
    """
    Search photos by person name or natural language query.
    Adapted from FileMind's /search (cosine similarity on embeddings).
    """
    data = request.get_json()
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "Query is required"}), 400

    results = []
    query_lower = query.lower()

    # Simple name-based search
    for person_id, person_data in storage.items():
        person_name = person_data.get("name", "").lower()
        if query_lower in person_name or person_name in query_lower:
            for photo_path in person_data.get("photos", {}).keys():
                results.append({
                    "file": photo_path,
                    "filename": os.path.basename(photo_path),
                    "person_id": person_id,
                    "person_name": person_data.get("name", "Unknown"),
                    "match_type": "name"
                })

    return jsonify({"results": results, "query": query})


# -----------------------------
# CHATBOT (adapted from FileMind /ask)
# -----------------------------

@app.route("/chat", methods=["POST"])
def chat():
    """
    Chatbot endpoint — natural language interaction.
    Adapted from FileMind's /ask RAG endpoint.
    """
    data = request.get_json()
    user_message = data.get("message", "").strip()
    session_id = data.get("session_id", "default")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    # Build context for chatbot
    context = {
        "persons": get_all_persons(),
        "total_photos": sum(
            len(p.get("photos", {})) for p in storage.values()
        )
    }

    result = process_query(user_message, context=context, session_id=session_id)

    # Handle action if returned
    action = result.get("action")
    if action and action.get("type") == "search_person":
        person_name = action.get("person_name", "")
        # Auto-search and attach results
        search_results = []
        for pid, pdata in storage.items():
            if person_name.lower() in pdata.get("name", "").lower():
                search_results.extend(list(pdata.get("photos", {}).keys()))
        result["search_results"] = search_results

    return jsonify(result)


@app.route("/chat/clear", methods=["POST"])
def clear_chat():
    """Clear chatbot conversation history."""
    data = request.get_json() or {}
    session_id = data.get("session_id", "default")
    clear_session(session_id)
    return jsonify({"status": "cleared"})


# -----------------------------
# DELIVERY (new)
# -----------------------------

@app.route("/deliver", methods=["POST"])
def deliver_photos():
    """
    Send photos via email or WhatsApp.
    """
    data = request.get_json()
    method = data.get("method", "email")  # "email" or "whatsapp"
    recipient = data.get("recipient", "")
    person_id = data.get("person_id")
    photo_paths = data.get("photo_paths", [])
    subject = data.get("subject", "Photos from Drishyamitra")
    message = data.get("message", "")

    if not recipient:
        return jsonify({"error": "Recipient is required"}), 400

    # If person_id provided, get their photos
    if person_id and not photo_paths:
        photo_paths = get_person_photos(person_id)

    if not photo_paths:
        return jsonify({"error": "No photos to send"}), 400

    # Send via chosen method
    if method == "email":
        result = send_email(recipient, subject, photo_paths, message)
    elif method == "whatsapp":
        result = send_whatsapp(recipient, photo_paths, message)
    else:
        return jsonify({"error": f"Unsupported delivery method: {method}"}), 400

    return jsonify(result)


# -----------------------------
# SERVE IMAGES
# -----------------------------

@app.route("/image/<path:filepath>")
def serve_image(filepath):
    """Serve an image file."""
    # Security: only serve from upload/organized directories
    abs_path = os.path.abspath(filepath)

    for allowed_dir in [UPLOAD_FOLDER, ORGANIZED_FOLDER]:
        if abs_path.startswith(os.path.abspath(allowed_dir)):
            if os.path.exists(abs_path):
                return send_file(abs_path)

    return jsonify({"error": "File not found or access denied"}), 404


# -----------------------------
# WEBSOCKET (adapted from FileMind /ws)
# -----------------------------

@socketio.on("connect")
def handle_connect():
    print("Client connected via WebSocket")


@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected from WebSocket")


# -----------------------------
# WATCHER THREAD (adapted from FileMind)
# -----------------------------

def run_watcher():
    """Start background photo watcher — same pattern as FileMind."""
    print("Drishyamitra: Indexing existing photos...")
    index_existing_photos()
    print("Drishyamitra: Watching for new photos...")
    start_watching(UPLOAD_FOLDER)


# Start watcher in background thread
threading.Thread(target=run_watcher, daemon=True).start()


# -----------------------------
# MAIN
# -----------------------------

if __name__ == "__main__":
    print("=" * 50)
    print("  Drishyamitra - AI Photo Management System")
    print("=" * 50)
    socketio.run(app, host=HOST, port=PORT, debug=DEBUG)
