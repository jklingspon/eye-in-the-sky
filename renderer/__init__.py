import cv2

class Renderer:
    def __init__(self):
        self.gps_data = None
        self.adsb_data = None

    def update_data(self, source, data):
        if source == 'gps':
            print("GPS!")
            print(data)
            self.gps_data = data
        elif source == 'adsb':
            self.adsb_data = data

    def render_frame(self, frame):
        if self.gps_data:
            cv2.putText(frame, f"GPS: {self.gps_data}", (10, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        if self.adsb_data:
            y_offset = 350
            for callsign, info in self.adsb_data.items():
                print(callsign)
                cv2.putText(frame, f"Callsign: {callsign}", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                y_offset += 30
                cv2.putText(frame, f"Longitude: {info['lon']}", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                y_offset += 30
                cv2.putText(frame, f"Latitude: {info['lat']}", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                y_offset += 30

        return frame
