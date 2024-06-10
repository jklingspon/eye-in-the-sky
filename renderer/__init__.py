import cv2
import math
import numpy as np
from pyproj import Proj, transform

# Define parameters
focal_length = 5.9  # in mm
sensor_width = 5.9 * (4128 / 3008)  # in mm, assuming square pixels
sensor_height = 5.9  # in mm
image_width = 2064  # in pixels
image_height = 1504  # in pixels

# Calculate the pixel size in mm
pixel_size_x = sensor_width / image_width
pixel_size_y = sensor_height / image_height

# Calculate the principal point (center of the image)
principal_point_x = image_width / 2
principal_point_y = image_height / 2

# Compute the intrinsic matrix K
K = np.array([
    [focal_length / pixel_size_x, 0, principal_point_x],
    [0, focal_length / pixel_size_y, principal_point_y],
    [0, 0, 1]
])

def ft_to_m(feet):
    return feet * 0.3048

def wgs84_to_utm(lat, lon):
    proj_utm = Proj(proj="utm", zone=10, datum="WGS84")  # Zone 10 is used for this specific latitude and longitude
    easting, northing = proj_utm(lon, lat)
    return easting, northing

def compute_vectors(gps, adsb):
    x0, y0 = wgs84_to_utm(gps['lat'], gps['lon'])
    z0 = gps['alt']

    adsb_transformed = {}
    distance = {}

    for icao, info in adsb.items():
        lat = info['lat']
        lon = info['lon']
        z = ft_to_m(info['altitude'])

        x, y = wgs84_to_utm(lat, lon)

        dx = x - x0
        dy = y - y0
        dz = z - z0

        # Negate 
        adsb_transformed[icao] = (-dx, dy, dz)

        dist_lat_m = np.sqrt(dx**2 + dy**2)
        dist_total_m = np.sqrt(dx**2 + dy**2 + dz**2)
        distance[icao] = (dist_lat_m / 1852, dist_total_m / 1852)

    return adsb_transformed, distance

# Function to generate the rotation matrix for yaw
def rotation_matrix(yaw):
    yaw = np.radians(yaw)

    R_yaw = np.array([
        [np.cos(yaw), -np.sin(yaw), 0],
        [np.sin(yaw), np.cos(yaw), 0],
        [0, 0, 1]
    ])

    return R_yaw

def project_to_image_plane(coords_dict, R, K):
    
    # Convert dictionary to numpy array for vectorized operations
    icao_ids = list(coords_dict.keys())

    coords = np.array(list(coords_dict.values()))

    coords = coords @ R.T

    x = coords[:, 0]
    y = coords[:, 1]
    z = coords[:, 2]

    # Avoid division by zero for points with y == 0
    mask = y != 0

    # Project the points using the intrinsic matrix K
    u = (x[mask] * K[0, 0] / y[mask]) + K[0, 2]
    v = (z[mask] * K[1, 1] / y[mask]) + K[1, 2]

    u = np.round(u).astype(int)
    v = np.round(v).astype(int)
    
    projected_coords = {icao_id: (u[i], v[i]) for i, icao_id in enumerate(icao_ids)}

    return projected_coords


class Renderer:
    def __init__(self):
        self.gps_data = None
        self.adsb_data = None
        self.adsb_projected = None
        self.adsb_transformed = None
        self.distance = None
        self.R = rotation_matrix(0)

    def update_data(self, source, data):
        if source == 'gps':
            self.gps_data = data
            self.R = rotation_matrix(self.gps_data['heading'])
        elif source == 'adsb':
            self.adsb_data = data

        if self.gps_data and self.adsb_data:
            self.adsb_transformed, self.distance = compute_vectors(self.gps_data, self.adsb_data)
            self.adsb_projected = project_to_image_plane(self.adsb_transformed, self.R, K)
         

    def generate_warnings(self):
        warnings = []

        # Loop through the points in adsb_transformed to check for warnings
        for key, (x, y, z) in self.adsb_transformed.items():
            flight = self.adsb_data[key]['flight'].strip()
            altitude_ft = z * 3.28084  # Convert meters to feet
            lateral = self.distance[key][0]
            if altitude_ft < 500:
                warnings.append(f"Warning: Aircraft {flight} within min VFR vertical clearance: {altitude_ft:.0f} ft. Lateral separation {lateral:.3f} nm")
            elif altitude_ft < 1000:
                warnings.append(f"Warning: Aircraft {flight} within min IFR vertical clearance: {altitude_ft:.0f} ft. Lateral separation {lateral:.3f} nm")

        return warnings

    def render_frame(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        image_width = 2064
        image_height = 1504

        if self.adsb_projected and self.adsb_transformed:
            # Generate warnings
            warnings = self.generate_warnings()

            # Display warnings at the top of the screen
            for i, warning in enumerate(warnings):
                color = (255, 0, 0) if "VFR" in warning else (255, 165, 0)
                cv2.putText(frame, warning, (200, 250 + 30 * i), cv2.FONT_HERSHEY_DUPLEX, 1, color, 2, cv2.LINE_AA)
            
            # Loop through the points in adsb_projected
            for key, (x, y) in self.adsb_projected.items():
                if 0 <= x < image_width and 0 <= y < image_height:
                    # Draw the point in red
                    cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
                    
                    # Get the flight, speed, lat, lon, altitude, and distance information
                    flight = self.adsb_data[key]['flight'].strip()
                    speed = self.adsb_data[key]['speed']
                    lat = self.adsb_data[key]['lat']
                    lon = self.adsb_data[key]['lon']
                    altitude = self.adsb_data[key]['altitude']
                    distance = self.distance[key]
                    
                    # Annotate the point with the flight, speed, lat, lon, altitude, and distance information
                    text1 = f"{flight} {speed} knots"
                    text2 = f"Lat: {lat:.4f}, Lon: {lon:.4f}, Alt: {altitude} ft"
                    text3 = f"Distance: {distance[1]:.2f} nm"
                    
                    text1_size, _ = cv2.getTextSize(text1, cv2.FONT_HERSHEY_DUPLEX, 0.5, 1)
                    text2_size, _ = cv2.getTextSize(text2, cv2.FONT_HERSHEY_DUPLEX, 0.5, 1)
                    text3_size, _ = cv2.getTextSize(text3, cv2.FONT_HERSHEY_DUPLEX, 0.5, 1)
                    
                    text1_width, text1_height = text1_size
                    text2_width, text2_height = text2_size
                    text3_width, text3_height = text3_size

                    # Adjust text position based on the point's location
                    max_text_width = max(text1_width, text2_width, text3_width)
                    if x + max_text_width + 10 > image_width:
                        text_x = x - max_text_width - 10
                    else:
                        text_x = x + 10

                    if y - text1_height - text2_height - text3_height < 0:
                        text_y1 = y + text1_height + 10
                        text_y2 = text_y1 + text2_height + 5
                        text_y3 = text_y2 + text3_height + 5
                    else:
                        text_y1 = y
                        text_y2 = text_y1 + text2_height + 5
                        text_y3 = text_y2 + text3_height + 5

                    cv2.putText(frame, text1, (text_x, text_y1), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                    cv2.putText(frame, text2, (text_x, text_y2), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                    cv2.putText(frame, text3, (text_x, text_y3), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        return frame
