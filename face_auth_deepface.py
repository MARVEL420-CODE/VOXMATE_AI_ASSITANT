"""
face_auth_deepface.py
---------------------
Performs face authentication using DeepFace and OpenCV webcam.
Stores authorized user images in 'authorized_faces_deep' folder.
"""

import os
import time
import cv2
from deepface import DeepFace

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
AUTHORIZED_DIR = "authorized_faces_deep"
MODEL = "ArcFace"        # Options: "Facenet", "VGG-Face", "ArcFace", "DeepFace"
MAX_ATTEMPTS = 3
CAPTURE_TIMEOUT = 10     # seconds per attempt


# ------------------------------------------------------------
# Load Authorized Faces
# ------------------------------------------------------------
def load_authorized_images():
    """Load list of authorized image paths and names."""
    images, names = [], []
    if not os.path.exists(AUTHORIZED_DIR):
        raise FileNotFoundError(f"{AUTHORIZED_DIR} not found. Please create it and add face images.")
    for fname in os.listdir(AUTHORIZED_DIR):
        path = os.path.join(AUTHORIZED_DIR, fname)
        if os.path.isfile(path):
            images.append(path)
            names.append(os.path.splitext(fname)[0])
    return images, names


# ------------------------------------------------------------
# Authenticate Face
# ------------------------------------------------------------
def authenticate_face_deepface() -> bool:
    """
    Authenticate user's face using DeepFace with live camera feed.
    Shows live preview with colored status text:
      🟡 Initializing  → Yellow
      🔵 Retrying...   → Blue
      ✅ Verified      → Green
      ❌ Not Verified  → Red
    """

    known_images, known_names = load_authorized_images()
    if not known_images:
        print("❌ No authorized faces found in folder.")
        return False

    print("\n🔒 Face Authentication: Please look at the camera...\n")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("❌ Unable to access webcam.")
        return False

    time.sleep(2)  # Camera warm-up
    attempts = 0
    authenticated = False
    message = "Initializing..."
    color = (0, 255, 255)  # Yellow for initialize

    try:
        while attempts < MAX_ATTEMPTS and not authenticated:
            attempts += 1
            print(f"📸 Attempt {attempts}/{MAX_ATTEMPTS}")

            start_time = time.time()
            while time.time() - start_time < CAPTURE_TIMEOUT:
                ret, frame = cap.read()
                if not ret or frame is None:
                    message = "⚠️ Frame not captured..."
                    color = (0, 255, 255)  # Yellow
                    continue

                # Draw message background for clarity
                cv2.rectangle(frame, (10, 10), (640, 70), (0, 0, 0), -1)
                cv2.putText(frame, message, (30, 55), cv2.FONT_HERSHEY_SIMPLEX,
                            1, color, 2, cv2.LINE_AA)

                cv2.imshow("Face Authentication - Press 'q' to cancel", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\n❌ Authentication cancelled by user.")
                    message = "Cancelled by user"
                    color = (0, 0, 255)
                    authenticated = False
                    break

                cv2.imwrite("temp_frame.jpg", frame)

                try:
                    faces = DeepFace.extract_faces("temp_frame.jpg", detector_backend="opencv")
                    if not faces:
                        message = "No face detected"
                        color = (0, 255, 255)
                        continue
                except Exception:
                    message = "Detecting face..."
                    color = (0, 255, 255)
                    continue

                verified_this_frame = False
                for auth_img, name in zip(known_images, known_names):
                    try:
                        result = DeepFace.verify(
                            "temp_frame.jpg", auth_img,
                            model_name=MODEL, enforce_detection=True
                        )

                        distance = result.get("distance", 1.0)
                        verified = result.get("verified", False)
                        print(f"→ Comparing with {name}: verified={verified}, distance={distance:.3f}")

                        if verified and distance < 0.35:
                            message = f"✅ Verified: {name}"
                            color = (0, 255, 0)  # Green
                            authenticated = True
                            verified_this_frame = True
                            break
                    except Exception:
                        continue

                if not verified_this_frame:
                    message = "❌ Not Verified"
                    color = (0, 0, 255)  # Red

                if authenticated:
                    break

            if not authenticated and attempts < MAX_ATTEMPTS:
                print("⚠️ Attempt failed. Retrying...\n")
                message = "🔄 Retrying..."
                color = (255, 0, 0)  # Blue for retry

    finally:
        cap.release()
        cv2.destroyAllWindows()
        if os.path.exists("temp_frame.jpg"):
            os.remove("temp_frame.jpg")

    if authenticated:
        print("\n✅ Face authenticated successfully.")
        return True
    else:
        print("\n❌ Face authentication failed. Access denied.")
        return False


