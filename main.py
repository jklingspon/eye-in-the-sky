import threading
import queue
import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
import os
import time
from camera import Camera
from gps import GpsHandler
from adsb import AdsbHandler
from renderer import Renderer

class MainService(QMainWindow):
    def __init__(self):
        super().__init__()

        self.data_queue = queue.Queue()
        self.shutdown_event = threading.Event()
        self.gps = GpsHandler(self.data_queue, self.shutdown_event)
        self.adsb = AdsbHandler(self.data_queue, self.shutdown_event)
        self.camera = Camera(self.data_queue, self.shutdown_event)
        self.renderer = Renderer()

        # Set up the PyQt5 UI
        self.setWindowTitle('Live Camera Stream')
        self.setGeometry(0, 0, 1920, 1080)

        self.label = QLabel(self)
        self.label.setGeometry(0, 0, 1920, 1080)

        # Set up a timer to process the queue
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_queue)
        self.timer.start(5)

    def display_frame(self, frame):
        # Convert the image to RGB format
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w

        # Create a QImage from the RGB image
        qimg = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

        # Display the QImage on the label
        self.label.setPixmap(QPixmap.fromImage(qimg))

    def process_queue(self):
        if not self.data_queue.empty():
            source, data = self.data_queue.get()
            self.renderer.update_data(source, data)
            if source == 'cam':
                frame = self.renderer.render_frame(data)
                self.display_frame(frame)

    def start_services(self):
        self.camera.start()
        self.gps.start()
        self.adsb.start()

        try:
            while not self.shutdown_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutdown initiated...")
        finally:
            self.shutdown_event.set()
            self.camera.join()
            self.gps.join()

if __name__ == "__main__":
    # Set environment variable to use framebuffer
    os.putenv('QT_QPA_PLATFORM', 'linuxfb')
    os.putenv('QT_QPA_FB', '/dev/fb1')

    app = QApplication(sys.argv)
    service = MainService()
    service.show()

    # Start the services in a separate thread
    service_thread = threading.Thread(target=service.start_services)
    service_thread.start()

    sys.exit(app.exec_())
    service_thread.join()

