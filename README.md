## Eye in the Sky Service

The eye in the sky service is written 

### Required Hardware:
- Raspberry Pi 4B
- RTL-SDR Dongle
- Septentrio Mosaic-X5 GNSS Receiver
- Vision Components IMX565 MIPI Camera

### Setup Instructions:
Outside of Skynix, the system environment can be replicated on Raspbian Lite Bullseye for arm64.

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
