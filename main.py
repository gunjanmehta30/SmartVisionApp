"""
Phase 2: Live camera feed with YOLOv8 (ONNX) object detection,
distance estimation, and voice alerts — fully on-device, no server needed.
"""
import cv2
import numpy as np
from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.utils import platform

# ---- CONFIG ----
MODEL_PATH = "assets/yolov8n.onnx"
INPUT_SIZE = 320
CONF_THRESHOLD = 0.4
NMS_THRESHOLD = 0.45

COCO_CLASSES = {
    0: "person", 1: "bicycle", 2: "car", 3: "motorcycle",
    5: "bus", 7: "truck", 16: "dog", 17: "cat",
}
RELEVANT_LABELS = {
    "person": "Human", "bicycle": "Bicycle", "car": "Car",
    "motorcycle": "Bike", "bus": "Bus/Truck", "truck": "Truck",
    "dog": "Animal", "cat": "Animal",
}
KNOWN_HEIGHTS_M = {
    "person": 1.7, "bicycle": 1.1, "car": 1.5, "motorcycle": 1.3,
    "bus": 3.2, "truck": 3.0, "dog": 0.5, "cat": 0.3,
}
FOCAL_LENGTH_PX = 700
SLOW_DOWN_DISTANCE_M = 3.0


def speak(text):
    """Cross-platform TTS — uses Android's native TTS via plyer when on device."""
    try:
        from plyer import tts
        tts.speak(message=text)
    except Exception as e:
        print(f"[TTS unavailable] {text} ({e})")


class Detector:
    def __init__(self):
        self.net = cv2.dnn.readNetFromONNX(MODEL_PATH)

    def detect(self, frame):
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(
            frame, scalefactor=1 / 255.0, size=(INPUT_SIZE, INPUT_SIZE),
            swapRB=True, crop=False
        )
        self.net.setInput(blob)
        output = self.net.forward()  # shape: (1, 84, N) for YOLOv8

        output = np.squeeze(output).T  # -> (N, 84)
        boxes, scores, class_ids = [], [], []

        x_scale = w / INPUT_SIZE
        y_scale = h / INPUT_SIZE

        for row in output:
            class_scores = row[4:]
            class_id = int(np.argmax(class_scores))
            conf = class_scores[class_id]
            if conf < CONF_THRESHOLD or class_id not in COCO_CLASSES:
                continue
            cx, cy, bw, bh = row[0], row[1], row[2], row[3]
            x1 = int((cx - bw / 2) * x_scale)
            y1 = int((cy - bh / 2) * y_scale)
            bw_px = int(bw * x_scale)
            bh_px = int(bh * y_scale)
            boxes.append([x1, y1, bw_px, bh_px])
            scores.append(float(conf))
            class_ids.append(class_id)

        indices = cv2.dnn.NMSBoxes(boxes, scores, CONF_THRESHOLD, NMS_THRESHOLD)

        detections = []
        for i in np.array(indices).flatten() if len(indices) > 0 else []:
            x, y, bw, bh = boxes[i]
            class_name = COCO_CLASSES[class_ids[i]]
            distance = self._estimate_distance(bh, class_name)
            detections.append({
                "bbox": (x, y, x + bw, y + bh),
                "class_name": class_name,
                "label": RELEVANT_LABELS.get(class_name, class_name),
                "conf": scores[i],
                "distance": distance,
            })
        return detections

    def _estimate_distance(self, bbox_height_px, class_name):
        real_h = KNOWN_HEIGHTS_M.get(class_name, 1.5)
        bbox_height_px = max(bbox_height_px, 1)
        return round((real_h * FOCAL_LENGTH_PX) / bbox_height_px, 2)


class CameraApp(App):
    def build(self):
        self.detector = Detector()
        self.last_spoken = None

        layout = BoxLayout(orientation="vertical")
        self.status_label = Label(text="Smart Vision - Live Detection", size_hint=(1, 0.08))
        layout.add_widget(self.status_label)

        self.img_widget = Image()
        layout.add_widget(self.img_widget)

        self.capture = cv2.VideoCapture(0)
        Clock.schedule_interval(self.update_frame, 1.0 / 15.0)  # ~15 FPS target
        return layout

    def update_frame(self, dt):
        ret, frame = self.capture.read()
        if not ret:
            return

        detections = self.detector.detect(frame)

        min_distance = None
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"{det['label']} {det['distance']}m",
                        (x1, max(y1 - 8, 15)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            if min_distance is None or det["distance"] < min_distance:
                min_distance = det["distance"]

        if min_distance is not None and min_distance <= SLOW_DOWN_DISTANCE_M:
            alert_text = f"Slow down, object {min_distance}m ahead"
            cv2.putText(frame, "SLOW DOWN", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            if alert_text != self.last_spoken:
                speak("Slow down, object ahead")
                self.last_spoken = alert_text
        else:
            self.last_spoken = None

        # Convert BGR (OpenCV) frame to Kivy texture
        frame = cv2.flip(frame, 0)
        buf = frame.tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt="bgr")
        texture.blit_buffer(buf, colorfmt="bgr", bufferfmt="ubyte")
        self.img_widget.texture = texture

    def on_stop(self):
        self.capture.release()


if __name__ == "__main__":
    CameraApp().run()