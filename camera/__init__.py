import cv2
import threading

def gst_pipeline():
    return (
        "v4l2src ! "
        "video/x-bayer, format=(string)rggb ! "
        "appsink"
    )

class Camera(threading.Thread):
    def __init__(self, data_queue, shutdown_event):
        super().__init__()
        self.shutdown_event = shutdown_event
        self.data_queue = data_queue
        self.capture = cv2.VideoCapture(gst_pipeline(), cv2.CAP_GSTREAMER)

    def run(self):
        while not self.shutdown_event.is_set():
            ret, frame = self.capture.read()

            if not ret:
                print("Error reading frame!")
                break

            frame = cv2.pyrDown(frame)
            self.data_queue.put(('cam', frame))

        capture.release()

