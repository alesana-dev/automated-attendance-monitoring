import face_recognition
import numpy as np

def encode_face(image):
    # If input is a PIL Image, convert to numpy array
    if hasattr(image, 'convert'):
        image = np.array(image.convert('RGB'))
    encodings = face_recognition.face_encodings(image)
    return encodings[0].tolist() if encodings else None

def compare_faces(known_encodings, face_encoding, tolerance=0.5):
    known = [np.array(e) for e in known_encodings]
    face = np.array(face_encoding)
    return face_recognition.compare_faces(known, face, tolerance)
