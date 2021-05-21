# bitcoin-ticker
bitcoin-ticker is a E-ink ticker that shows usefull information about bitcoin. Due to the limited refresh lifetime, new information is currently shown every 5 minutes and whenever a new block arrives.

![](pictures/view6.jpg)
![](pictures/view1.jpg)
![](pictures/view2.jpg)
![](pictures/view3.jpg)
![](pictures/view4.jpg)


## Hardware

* waveshare 2.7 e-Paper HAT (e.g. from [berrybase](https://www.berrybase.de/sensoren-module/displays/epaper-displays/2.7-264-215-176-epaper-display-hat-f-252-r-raspberry-pi))
* rasberry pi zero WH (e.g. from [berrybase](https://www.berrybase.de/raspberry-pi/raspberry-pi-computer/boards/raspberry-pi-zero-wh))
* Power supply Micro USB 5V (e.g. from [berrybase](https://www.berrybase.de/raspberry-pi/raspberry-pi-computer/stromversorgung/netzteile-fuer-die-steckdose/micro-usb-netzteil/ladeadapter-5v/1a-flache-bauform-schwarz))
* micro SD card with 16 GB or more (e.g. from [berrybase](https://www.berrybase.de/raspberry-pi/raspberry-pi-computer/speicherkarten/sandisk-ultra-microsdhc-a1-98mb/s-class-10-speicherkarte-43-adapter-16gb))

## Usage
### Ticker view
The Tickers the following information:
* Block height, Mean block intervall in minutes, Time
* Minimal Block fee for the first 7 blocks in mempool
* Dollar price of a bitcoin
* Satoshi per Dollar (also know as moskow time)
* Sotoshi per Euro
* Euro price of a bitcoin

Whenever a new block has arrived on the blockchain, the following information is shown for 120 seconds (can be disabled in the config.ini):
* Euro price of a bitcoin, mean block intervall in minutes, Time
* Minimal Block fee for the first 7 blocks in mempool
* Blocks in mempook, Number of transaction in mempool
* Blocks until next difficulty retargeting, est. difficulty multiplier, est. retarget time
* Block height

Due to the limited lifetime of 1000000 refreshes and an expected lifetime of 5 years, the refresh period has been set to 216 seconds.
### Buttons
There are four buttons which the following behaviour (Please be patient after pressing, the e-ink is quite slow):
1. Switch through different ticker views
2. Switch BTC/fiat graph through 1, 7 and 30 days
3. Switch the layout of the ticker
4. Show new block screen (is also shown everytime a new block is created)

### Config.ini
It possible to personalize the ticker to your needs. After logging into your raspi with SSH, the config can be edited with
```
nano config.ini
```
After writing the change to the ini file, a restart of the btc-ticker service is needed:
```
sudo systemctl restart btcticker
```

### Update btc-ticker without reflashing the sdcard
After logging into the btc-ticker with SSH, the update can be started with
```
./99updateMenu.sh
```
Select now:
* PATCH
* Patch menu
* PATCH
to update the ticker to the newest updates from git.

## Flash SDcard

* Downlad version 0.3.1 from [btc-ticker-0_3_1.img.gz](https://btc-ticker.com/btc-ticker-0_3_1.img.gz)
* Verify SHA256 checksum. It should be: `C614031C9B7F9DF693D60B57A9B730053F86AE31CDFADDCAFC219E8069057FA6`
* add `wpa_supplicant.conf` to the boot partition when mounted on PC
```
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=[COUNTRY_CODE]
network={
  ssid="[WIFI_SSID]"
  psk="[WIFI_PASSWORD]"
}
```
* replace `[COUNTRY_CODE]` with the ISO2 code (e.g. DE)
* Set `[WIFI_SSID]` and `[WIFI_PASSWORD]`

## Build SDcard from scratch

The SDcard build process is inspired by the great [raspiblitz](https://github.com/rootzoll/raspiblitz).

* Download lastest [raspios image](https://downloads.raspberrypi.org/raspios_armhf/images/)
* Write the Image to a SD card [Tutorial](https://www.raspberrypi.org/documentation/installation/installing-images/README.md)
* Add a `ssh` file to the boot partition when mounted on PC
* Add a `wpa_supplicant.conf` file, as shown in the section before. More information are also available [here](https://www.raspberrypi.org/documentation/configuration/wireless/headless.md)
* Login via SSH to `ssh pi@[IP-OF-YOUR-RASPI]` using password `raspberry`


The image can now be build with:
```
wget https://raw.githubusercontent.com/btc-ticker/btc-ticker/main/build_sdcard.sh && sudo bash build_sdcard.sh
```

After everything run through, it is possible to login with the password `btcticker`
In order to prepare everyting for release, run `/home/admin/XXprepareRelease.sh`. When you just want to use it for yourself, you do not need to run `/home/admin/XXprepareRelease.sh`.

## Changing the ssh password
In order to secure your btc-ticker in your local network, you should change the SSH password after setting up everything.
* Login via SSH to `ssh admin@[IP-OF-YOUR-RASPI]` using the password `btcticker`
* Change the password (this will be improved in the next release)
```
echo "pi:NEWPASSWORD" | sudo chpasswd
echo "root:NEWPASSWORD" | sudo chpasswd
echo "admin:NEWPASSWORD" | sudo chpasswd
```
Replace `NEWPASSWORD` with the new password.

## Used APIs
btc-ticker is using the following APIs:
* [mempool.space/api](https://mempool.space/api), which can also be run locally in e.g. raspiblitz
* [coingecko api](https://www.coingecko.com/en/api)
* [blockchain API v1](https://github.com/blockchain/api-v1-client-python)