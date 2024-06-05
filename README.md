# Eye in the Sky Service

## Overview

The EITS service is the capture, computation, and rendering service intended for use on the asseembled eye in the sky device. This makes use of a multithreaded producer/consumer model to asynchronously aggregate input data from the SDR module, GPS, and camera as it is made available, pass it to a renderer thread which handles data computation and image compositing, and draw the outputs directly on the device framebuffer using PyQT5. A full explanation of each module is available below.

## Implementation

### Required Hardware:
- Raspberry Pi 4B
- RTL-SDR Dongle
- Septentrio Mosaic-X5 GNSS Receiver
- Vision Components IMX565 MIPI Camera

SOLIDWORKS part files for the system enclosure can be obtained from [https://github.com/jklingspon/eits-cad]

### Setup Instructions:
Though created for use with [Skynix](https://github.com/jklingspon/skynix), the system environment can be replicated easily on Raspberry Pi OS Lite Bullseye for arm64.

Set up the system and obtain necessary dependencies:
```
sudo apt -y update && sudo apt -y upgrade
sudo apt -y install python3 python3-pip python3-opencv dump1090-mutability gstreamer1.0-plugins-base gstreamer1.0-plugins-good rtl-sdr
```

Install the vision components MIPI camera driver:
```
sudo apt -y install raspberrypi-kernel-headers device-tree-compiler
sudo apt -y install dkms
wget https://files.vision-components.com/mipi/vc-mipi-driver-bcm2835-dkms_0.2.7_all.zip
unzip vc-mipi-driver-bcm2835-dkms_0.2.7_all.zip
sudo dpkg -i vc-mipi-driver-bcm2835-dkms_0.2.7_all.zip
# Clean up
rm vc-mipi
```

In `/boot/config_vc-mipi-driver-bcm2835.txt`, uncomment the lines for the Pi 4B config and device tree overlay for the imx565:

Add a line to execute `dump1090-mutability` with the `--net` flag to `/etc/rc-local` on boot time. This provides an error-corrected source for the ADS-B data through the RTL-SDR.
```
dump1090-mutability --net
```

Then clone the repo and install requirements:
```
git clone git@github.com:jklingspon/eye-in-the-sky.git
cd eye-in-the-sky
sudo pip3 install -r requirements.txt
```

### Usage

Attach a display to `hdmi0` on the Pi4 for framebuffer display.

Then, run `python3 main.py`

## Module Details

### Main
The main class initializes the data queue and device modules, and handles the rendering of the GUI with pyqt5. This will start all the modules and handle the passing if data from the program queue into the renderer, calling a render of the latest sensor data in the GUI each time a new camera frame is received. 

### GPS
The GPS module is intended to interface with a raw NMEA-type message stream served over a TCP/IP socket by the Septentrio Mosaic X-5. The Septentrio must be configured (via web-interface or serial) on the first boot to output an NMEA stream including at least GGA and HDT type messages, to obtain longitude, latitude, altitude, and heading. Once configured, these settings will persist.

On the GpsHandler thread run, a socket stream connection to the Septentrio is opened, and a parser provided by pynmeagps is configured to decode the raw binary messages. In the main loop, all relevant user position information is parsed from the incoming messages and published to a dictionary, which is copied to the program data queue.


### ADS-B
Similarly, the ADS-B module is written to connect to a running instance of dump1090 on the device and retrieve parsed aircraft position and identification data. dump1090-mutability is leveraged for its integrated error connection and ADS-B message parsing abilities (which didn't seem to work nearly as well with pyModeS as I'd hoped). 

When run with the `--net` flag, dump1090 publishes a JSON containing a list of tracked aircraft. This class requests this JSON and parses it into a python dictionary containing the list of aircraft by ICAO ID, and publishes it to the program data queue.


### Camera
As the Vision Components IMX565 driver for the Raspberry Pi 4B seems to only output bayer RGGB images and doesn't integrate with the Pi's hardware ISP, some extra image processing is required. OpenCV doesn't seem to like opening a bayer image stream directly through v4l, so a gstreamer pipeline is instead created and used as a source for an OpenCV VideoCapture. As the hardware ISP doesn't seem to work, any attempts at demosaicing must be done through software, which is a miserable time with a ~22fps stream of 4096x3000 images. Instead, OpenCV pyrDown is used, which performs a gaussian convolution along the bayer image pixels. This has the effect of not only downscaling for reasonable processing speeds, but also demosaicing into a grayscale image. Once this is done, the output frames are sent to the data queue.

### Renderer 
The renderer handles the final aggregation of data sources into the output images, and performs any necessary computation using the data. As data comes in from any sensor, the main service calls on the renderer to update its notion of the current values. Each time a frame arrives, the main service calls render_frame, which will use all the latest values from the renderer data store to create the output image appropriately, and return the complete frame to be passed to the QT GUI.
