"""
Phase 1: Minimal Kivy app that opens the phone camera and shows a live preview.
No YOLO yet — this just confirms camera access works on your real device.
"""
from kivy.app import App
from kivy.uix.camera import Camera
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label


class CameraTestApp(App):
    def build(self):
        layout = BoxLayout(orientation="vertical")

        self.status_label = Label(text="Smart Vision - Camera Test", size_hint=(1, 0.1))
        layout.add_widget(self.status_label)

        try:
            self.camera = Camera(play=True, resolution=(640, 480))
            layout.add_widget(self.camera)
        except Exception as e:
            layout.add_widget(Label(text=f"Camera error: {e}"))

        return layout


if __name__ == "__main__":
    CameraTestApp().run()