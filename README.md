# bitcoin-ticker
bitcoin-ticker is a E-ink ticker that shows usefull information about bitcoin. Due to the limited refresh lifetime, new information is currently shown every 5 minutes and whenever a new block arrives.

## Hardware

* waveshare 2.7 e-Paper HAT (e.g. from [berrybase](https://www.berrybase.de/sensoren-module/displays/epaper-displays/2.7-264-215-176-epaper-display-hat-f-252-r-raspberry-pi))
* rasberry pi zero WH (e.g. from [berrybase](https://www.berrybase.de/raspberry-pi/raspberry-pi-computer/boards/raspberry-pi-zero-wh))
* Power supply Micro USB 5V
* micro SD card with 16 GB or more

## Build SDcard

The sdcard build processed is inspired by the great [raspiblitz](https://github.com/rootzoll/raspiblitz).

* Download lastest [raspios image](https://downloads.raspberrypi.org/raspios_armhf/images/)
* Write the Image to a SD card [Tutorial](https://www.raspberrypi.org/documentation/installation/installing-images/README.md)
* Add a `ssh` file to the root when mounted on PC
* Add a `wpa_supplicant.conf` file, more information [here](https://www.raspberrypi.org/documentation/configuration/wireless/headless.md)
* Login via SSH to `ssh pi@[IP-OF-YOUR-RASPI]` using password `raspberry`


The image can now be build with:
```
wget https://raw.githubusercontent.com/btc-ticker/btc-ticker/main/build_sdcard.sh && sudo bash build_sdcard.sh
```

After everything run through, it is possible to login with the password `btcticker`
In order to prepare everyting for release, run `/home/admin/XXprepareRelease.sh`