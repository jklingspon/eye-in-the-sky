import socket
import threading
from pynmeagps import NMEAReader

GPS_IP = "192.168.3.1"
GPS_PORT = 5000

class GpsHandler(threading.Thread):
    def __init__(self, data_queue, shutdown_event):
        super().__init__()
        self.data_queue = data_queue
        self.initialized = threading.Event()
        self.shutdown_event = shutdown_event
        self.socket = None
        self.nmea_reader = None
        self.location = {
            'lon': 0,
            'lat': 0,
            'alt': 0,
            'heading': 0
        }

    def run(self):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((GPS_IP, GPS_PORT))
        self.nmea_reader = NMEAReader(self.socket)

        self.initialized.set()
        while not self.shutdown_event.is_set():
            (raw, parsed) = self.nmea_reader.read()
            if parsed:
                if parsed._msgID == "GGA":
                    self.location['lon'] == parsed.lon
                    self.location['lat'] == parsed.lat
                    self.location['alt'] == parsed.alt
                elif parsed._msgID == 'HDT':
                    self.location['heading'] == parsed.heading

                if self.location['lon'] == 0:
                    self.location['lon'] = 33.120496
                    self.location['lat'] = -117.281936
                    self.location['alt'] = 63.34
                    self.location['heading'] = 0

            self.data_queue.put(('gps', self.location))
