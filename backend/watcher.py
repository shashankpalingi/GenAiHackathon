"""
Drishyamitra - Photo File Watcher
Adapted from FileMind watcher.py
Same watchdog pattern but processes images through face detection pipeline.
"""

import time
import os
import traceback
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from face_engine import detect_faces, extract_image_metadata, is_valid_image
from cluster_engine import add_face, sync_folders, storage
from config import UPLOAD_FOLDER, ORGANIZED_FOLDER, ALLOWED_EXTENSIONS


# Cache to skip re-processing unchanged files (same as FileMind)
file_mtime_cache = {}


class PhotoHandler(FileSystemEventHandler):
    """
    Watches for new/modified image files and processes them through
    the face detection → embedding → clustering pipeline.
    
    Adapted from FileMind's FileHandler — same structure, but the
    process_file() method runs the face pipeline instead of text extraction.
    """

    def on_created(self, event):
        if not event.is_directory:
            self.process_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.process_file(event.src_path)

    def on_deleted(self, event):
        """Handle file deletion — remove from storage."""
        if not event.is_directory:
            file_path = os.path.abspath(event.src_path)
            removed = False

            for person_data in storage.values():
                if file_path in person_data.get("photos", {}):
                    person_data["photos"].pop(file_path)
                    if "metadata" in person_data and file_path in person_data["metadata"]:
                        person_data["metadata"].pop(file_path)
                    removed = True
                    break

            if removed:
                print(f"Watcher: Removed deleted file from index: {file_path}")
                from cluster_engine import save_storage
                from storage import save_storage as _save
                _save(storage)
                sync_folders(ORGANIZED_FOLDER)

    def process_file(self, file_path):
        """
        Process a single image file through the face pipeline.
        
        Pipeline (adapted from FileMind):
        1. Validate image → was: validate text file
        2. Detect faces + embeddings → was: extract text + chunk + embed
        3. Cluster each face into person groups → was: cluster into topic groups
        4. Sync organized folders → same pattern
        """
        if not os.path.exists(file_path):
            return

        abs_path = os.path.abspath(file_path)

        # Check file extension
        ext = os.path.splitext(abs_path)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return

        # Check mtime to skip unchanged files (same as FileMind)
        try:
            mtime = os.path.getmtime(abs_path)
            if file_mtime_cache.get(abs_path) == mtime:
                return
            file_mtime_cache[abs_path] = mtime
        except Exception:
            pass

        try:
            # Validate image
            if not is_valid_image(abs_path):
                print(f"Watcher: Skipping invalid image: {file_path}")
                return

            # Deduplication: skip if photo is already indexed
            already_indexed = False
            for person_data in storage.values():
                if abs_path in person_data.get("photos", {}):
                    already_indexed = True
                    break
            if already_indexed:
                print(f"Watcher: Skipping already indexed: {os.path.basename(file_path)}")
                return

            # Extract image metadata (replaces FileMind's extract_metadata)
            metadata = extract_image_metadata(abs_path)

            # Detect faces and get embeddings (replaces FileMind's text extraction + embedding)
            print(f"Watcher: Processing {os.path.basename(file_path)}...")
            faces = detect_faces(abs_path)

            if not faces:
                print(f"Watcher: No faces detected in {os.path.basename(file_path)}")
                # Still store photo even without faces (for non-face queries)
                add_face(abs_path, [], {"x": 0, "y": 0, "w": 0, "h": 0}, metadata)
                return

            # Cluster each detected face into person groups
            for face_data in faces:
                add_face(
                    photo_path=abs_path,
                    face_embedding=face_data["embedding"],
                    bbox=face_data["bbox"],
                    metadata=metadata
                )

            # Organize into person folders (same as FileMind's sync_folders)
            sync_folders(ORGANIZED_FOLDER)
            print(f"Watcher: Processed & organized: {os.path.basename(file_path)} ({len(faces)} face(s))")

        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Watcher: Processing error for {file_path}: {e}")
            traceback.print_exc()


def start_watching(path=None):
    """
    Start watching the upload folder for new photos.
    Same pattern as FileMind's start_watching.
    """
    if path is None:
        path = UPLOAD_FOLDER

    event_handler = PhotoHandler()
    observer = Observer()
    observer.schedule(event_handler, path=path, recursive=True)
    observer.start()
    print(f"Watcher: Watching folder (recursive): {path}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


def index_existing_photos(path=None):
    """
    Index all existing photos in the upload folder.
    Same pattern as FileMind's index_existing_files.
    """
    if path is None:
        path = UPLOAD_FOLDER

    print("Watcher: Indexing existing photos...")
    handler = PhotoHandler()

    for root, _, files in os.walk(path):
        for file in files:
            if file.startswith("."):
                continue
            filepath = os.path.join(root, file)
            handler.process_file(filepath)

    sync_folders(ORGANIZED_FOLDER)
    print("Watcher: Initial photo indexing complete.")
