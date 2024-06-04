import time
import threading
import queue
import requests
import json

class AdsbHandler(threading.Thread):
    def __init__(self, data_queue, shutdown_event):
        super().__init__()
        self.data_queue = data_queue
        self.initialized = threading.Event()
        self.shutdown_event = shutdown_event
        self.aircraft = {}

    def run(self):
        self.initialized.set()
        try:
            while not self.shutdown_event.is_set():
                self.fetch_aircraft_data()
                self.data_queue.put(('adsb', self.aircraft.copy()))
                time.sleep(0.05)  # Adjust the sleep interval as needed
        except Exception as e:
            print(f"Exception in ADS-B handler: {e}")

    def fetch_aircraft_data(self):
        try:
            response = requests.get("http://10.0.5.10:8080/data.json")
            if response.status_code == 200:
                data = response.json()
                for aircraft in data:
                    self.aircraft[aircraft["hex"]] = aircraft
        except Exception as e:
            print(f"Error fetching aircraft data: {e}")

if __name__ == "__main__":
    data_queue = queue.Queue()
    shutdown_event = threading.Event()
    handler = AdsbHandler(data_queue, shutdown_event)
    handler.start()
    try:
        while True:
            if not data_queue.empty():
                data_type, aircraft_data = data_queue.get()
                if data_type == 'adsb':
                    print(f"Received aircraft data: {aircraft_data}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown_event.set()
        handler.join()

