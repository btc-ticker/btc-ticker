#!/bin/bash
#########################################################################
# Build your SD card image based on:
# raspios_armhf-2021-03-25
# https://downloads.raspberrypi.org/raspios_armhf/images/raspios_armhf-2021-03-25/
# SHA256: a30a3650c3ef22a69f6f025760c6b04611a5992961a8c2cd44468f1c429d68bb
##########################################################################
# setup fresh SD card with image above - login per SSH and run this script:
# This script has been modified from https://raw.githubusercontent.com/rootzoll/raspiblitz/v1.7/build_sdcard.sh
##########################################################################

echo ""
echo "*****************************************"
echo "* BTCTICKER SD CARD IMAGE SETUP v0.5.0  *"
echo "*****************************************"
echo "For details on optional parameters - see build script source code:"

# 1st optional paramater: NO-INTERACTION
# ----------------------------------------
# When 'true' then no questions will be ask on building .. so it can be used in build scripts
# for containers or as part of other build scripts (default is false)

noInteraction="$1"
if [ ${#noInteraction} -eq 0 ]; then
  noInteraction="false"
fi
if [ "${noInteraction}" != "true" ] && [ "${noInteraction}" != "false" ]; then
  echo "ERROR: NO-INTERACTION parameter needs to be either 'true' or 'false'"
  exit 1
else
  echo "1) will use NO-INTERACTION --> '${noInteraction}'"
fi

# 2rd optional paramater: GITHUB-USERNAME
# ---------------------------------------
# could be any valid github-user that has a fork of the btc-ticker repo - 'rootzoll' is default
# The 'btc-ticker' repo of this user is used to provisioning sd card
# with btc-ticker assets/scripts later on.
# If this parameter is set also the branch needs to be given (see next parameter).
githubUser="$2"
if [ ${#githubUser} -eq 0 ]; then
  githubUser="btc-ticker"
fi
echo "2) will use GITHUB-USERNAME --> '${githubUser}'"

# 3th optional paramater: GITHUB-BRANCH
# -------------------------------------
# could be any valid branch of the given GITHUB-USERNAME forked btc-ticker repo - 'dev' is default
githubBranch="$3"
if [ ${#githubBranch} -eq 0 ]; then
  githubBranch="main"
fi
echo "3) will use GITHUB-BRANCH --> '${githubBranch}'"


# 4th optional paramater: TWEAK-BOOTDRIVE
# ---------------------------------------
# could be 'true' (default) or 'false'
# If 'true' it will try (based on the base OS) to optimize the boot drive.
# If 'false' this will skipped.
tweakBootdrives="$4"
if [ ${#tweakBootdrives} -eq 0 ]; then
  tweakBootdrives="true"
fi
if [ "${tweakBootdrives}" != "true" ] && [ "${tweakBootdrives}" != "false" ]; then
  echo "ERROR: TWEAK-BOOTDRIVE parameter needs to be either 'true' or 'false'"
  exit 1
else
  echo "4) will use TWEAK-BOOTDRIVE --> '${tweakBootdrives}'"
fi

# 5th optional parameter: DISPLAY-CLASS
# ----------------------------------------
# Could be 'eink', or 'lcd' (eink is default)
displayClass="$5"
if [ ${#displayClass} -eq 0 ]; then
  displayClass="eink"
fi
if [ "${displayClass}" != "eink" ] && [ "${displayClass}" != "lcd" ]; then
  echo "ERROR: DISPLAY-CLASS parameter needs to be 'eink', or 'lcd'"
  exit 1
else
  echo "5) will use DISPLAY-CLASS --> '${displayClass}'"
fi

# 6th optional paramater: WIFI
# ---------------------------------------
# could be 'false' or 'true' (default) or a valid WIFI country code like 'US' (default)
# If 'false' WIFI will be deactivated by default
# If 'true' WIFI will be activated by with default country code 'US'
# If any valid wifi country code Wifi will be activated with that country code by default
modeWifi="$6"
if [ ${#modeWifi} -eq 0 ] || [ "${modeWifi}" == "true" ]; then
  modeWifi="US"
fi
echo "6) will use WIFI --> '${modeWifi}'"

# AUTO-DETECTION: CPU-ARCHITECTURE
# ---------------------------------------
# keep in mind that DietPi for Raspberry is also a stripped down Raspbian
isARM=$(uname -m | grep -c 'arm')
isAARCH64=$(uname -m | grep -c 'aarch64')
isX86_64=$(uname -m | grep -c 'x86_64')
cpu="?"
if [ ${isARM} -gt 0 ]; then
  cpu="arm"
elif [ ${isAARCH64} -gt 0 ]; then
  cpu="aarch64"
elif [ ${isX86_64} -gt 0 ]; then
  cpu="x86_64"
else
  echo "!!! FAIL !!!"
  echo "Can only build on ARM, aarch64, x86_64 not on:"
  uname -m
  exit 1
fi
echo "X) will use CPU-ARCHITECTURE --> '${cpu}'"

# AUTO-DETECTION: OPERATINGSYSTEM
# ---------------------------------------
baseimage="?"
isDietPi=$(uname -n | grep -c 'DietPi')
isRaspbian=$(grep -c 'Raspbian' /etc/os-release 2>/dev/null)
isDebian=$(grep -c 'Debian' /etc/os-release 2>/dev/null)
isUbuntu=$(grep -c 'Ubuntu' /etc/os-release 2>/dev/null)
isNvidia=$(uname -a | grep -c 'tegra')
if [ ${isRaspbian} -gt 0 ]; then
  baseimage="raspbian"
fi
if [ ${isDebian} -gt 0 ]; then
  if [ $(uname -n | grep -c 'rpi') -gt 0 ] && [ ${isAARCH64} -gt 0 ]; then
    baseimage="debian_rpi64"
  elif [ $(uname -n | grep -c 'raspberrypi') -gt 0 ] && [ ${isAARCH64} -gt 0 ]; then
    baseimage="raspios_arm64"
  elif [ ${isAARCH64} -gt 0 ] || [ ${isARM} -gt 0 ] ; then
    baseimage="armbian"
  else
    baseimage="debian"
  fi
fi
if [ ${isUbuntu} -gt 0 ]; then
  baseimage="ubuntu"
fi
if [ ${isDietPi} -gt 0 ]; then
  baseimage="dietpi"
fi
if [ "${baseimage}" = "?" ]; then
  cat /etc/os-release 2>/dev/null
  echo "!!! FAIL: Base Image cannot be detected or is not supported."
  exit 1
fi
echo "X) will use OPERATINGSYSTEM ---> '${baseimage}'"

# USER-CONFIRMATION
if [ "${noInteraction}" != "true" ]; then
  echo -n "Do you agree with all parameters above? (yes/no) "
  read installBtcTickerAnswer
  if [ "$installBtcTickerAnswer" != "yes" ] ; then
    exit 1
  fi
fi
echo "Building btc-ticker ..."
echo ""
sleep 3



# FIXING LOCALES
# https://daker.me/2014/10/how-to-fix-perl-warning-setting-locale-failed-in-raspbian.html
# https://stackoverflow.com/questions/38188762/generate-all-locales-in-a-docker-image
if [ "${baseimage}" = "raspbian" ] || [ "${baseimage}" = "dietpi" ] || \
   [ "${baseimage}" = "raspios_arm64" ]||[ "${baseimage}" = "debian_rpi64" ]; then
  echo ""
  echo "*** FIXING LOCALES FOR BUILD ***"

  sudo sed -i "s/^# en_US.UTF-8 UTF-8.*/en_US.UTF-8 UTF-8/g" /etc/locale.gen
  sudo sed -i "s/^# en_US ISO-8859-1.*/en_US ISO-8859-1/g" /etc/locale.gen
  sudo locale-gen
  export LANGUAGE=en_US.UTF-8
  export LANG=en_US.UTF-8
  if [ "${baseimage}" = "raspbian" ] || [ "${baseimage}" = "dietpi" ]; then
    export LC_ALL=en_US.UTF-8

    sudo sed -i "s/^    SendEnv LANG LC.*/#   SendEnv LANG LC_*/g" /etc/ssh/ssh_config

    # remove unneccesary files
    sudo rm -rf /home/pi/MagPi
    # https://www.reddit.com/r/linux/comments/lbu0t1/microsoft_repo_installed_on_all_raspberry_pis/
    sudo rm -f /etc/apt/sources.list.d/vscode.list
    sudo rm -f /etc/apt/trusted.gpg.d/microsoft.gpg
  fi
  if [ ! -f /etc/apt/sources.list.d/raspi.list ]; then
    echo "# Add the archive.raspberrypi.org/debian/ to the sources.list"
    echo "deb http://archive.raspberrypi.org/debian/ buster main" | sudo tee /etc/apt/sources.list.d/raspi.list
  fi
fi

# remove some (big) packages that are not needed

sudo apt remove --purge -y libreoffice* oracle-java* chromium-browser nuscratch scratch sonic-pi plymouth python2 vlc cups vnstat
if [ "${displayClass}" == "eink" ]; then
  sudo apt remove -y --purge xserver* lightdm* lxde* mesa* lx* gnome* desktop* gstreamer* pulseaudio*
  sudo apt remove -y --purge raspberrypi-ui-mods  gtk* hicolor-icon-theme*
else
  sudo apt remove -y --purge lightdm* vlc* lxde* lx* mesa* chromium* desktop* gnome* gstreamer* pulseaudio*
  sudo apt remove -y --purge raspberrypi-ui-mods gtk* hicolor-icon-theme*
fi
sudo apt clean
sudo apt -y autoremove

echo "sleeping 60 seconds"
# sleep for 60 seconds
sleep 60

if [ -f "/usr/bin/python3.9" ]; then
  # use python 3.9 if available
  sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.9 1
  echo "python calls python3.9"
elif [ -f "/usr/bin/python3.10" ]; then
  # use python 3.10 if available
  sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1
  sudo ln -s /usr/bin/python3.10 /usr/bin/python3.9
  echo "python calls python3.10"
elif [ -f "/usr/bin/python3.11" ]; then
  # use python 3.11 if available
  sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1
  sudo ln -s /usr/bin/python3.11 /usr/bin/python3.9
  echo "python calls python3.11"
elif [ -f "/usr/bin/python3.8" ]; then
  # use python 3.8 if available
  sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.8 1
  echo "python calls python3.8"
else
  echo "!!! FAIL !!!"
  echo "There is no tested version of python present"
  exit 1
fi

# update debian
echo ""
echo "*** UPDATE ***"
sudo apt update -y
# sudo apt upgrade -f -y

echo "sleeping 60 seconds"
# sleep for 60 seconds
sleep 60

echo ""
echo "*** PREPARE ${baseimage} ***"

# make sure the pi user is present
if [ "$(compgen -u | grep -c dietpi)" -gt 0 ];then
  echo "# Renaming dietpi user to pi"
  sudo usermod -l pi dietpi
elif [ "$(compgen -u | grep -c pi)" -eq 0 ];then
  echo "# Adding the user pi"
  sudo adduser --disabled-password --gecos "" pi
  sudo adduser pi sudo
fi

# special prepare when Raspbian
if [ "${baseimage}" = "raspbian" ]||[ "${baseimage}" = "raspios_arm64" ]||\
   [ "${baseimage}" = "debian_rpi64" ]; then
  sudo apt install -y raspi-config
  # do memory split (16MB)
  sudo raspi-config nonint do_memory_split 16
  # set to wait until network is available on boot (0 seems to yes)
  sudo raspi-config nonint do_boot_wait 0
  # Enable SPI
  sudo raspi-config nonint do_spi 1
  # set WIFI country so boot does not block
  if [ "${modeWifi}" != "false" ]; then
    # this will undo the softblock of rfkill on RaspiOS
    sudo raspi-config nonint do_wifi_country $modeWifi
  fi

  configFile="/boot/config.txt"
  max_usb_current="max_usb_current=1"
  max_usb_currentDone=$(grep -c "$max_usb_current" $configFile)

  if [ ${max_usb_currentDone} -eq 0 ]; then
    echo "" | sudo tee -a $configFile
    echo "# Raspiblitz" | sudo tee -a $configFile
    echo "$max_usb_current" | sudo tee -a $configFile
  else
    echo "$max_usb_current already in $configFile"
  fi

  # run fsck on sd root partition on every startup to prevent "maintenance login" screen
  # use command to check last fsck check: sudo tune2fs -l /dev/mmcblk0p2
  if [ "${tweakBootdrives}" == "true" ]; then
    echo "* running tune2fs"
    sudo tune2fs -c 1 /dev/mmcblk0p2
  else
    echo "* skipping tweakBootdrives"
  fi

  # edit kernel parameters
  kernelOptionsFile=/boot/cmdline.txt
  fsOption1="fsck.mode=force"
  fsOption2="fsck.repair=yes"
  fsOption1InFile=$(grep -c ${fsOption1} ${kernelOptionsFile})
  fsOption2InFile=$(grep -c ${fsOption2} ${kernelOptionsFile})

  if [ ${fsOption1InFile} -eq 0 ]; then
    sudo sed -i "s/^/$fsOption1 /g" "$kernelOptionsFile"
    echo "$fsOption1 added to $kernelOptionsFile"
  else
    echo "$fsOption1 already in $kernelOptionsFile"
  fi
  if [ ${fsOption2InFile} -eq 0 ]; then
    sudo sed -i "s/^/$fsOption2 /g" "$kernelOptionsFile"
    echo "$fsOption2 added to $kernelOptionsFile"
  else
    echo "$fsOption2 already in $kernelOptionsFile"
  fi
fi

# special prepare when Nvidia Jetson Nano
if [ ${isNvidia} -eq 1 ] ; then
  # disable GUI on boot
  sudo systemctl set-default multi-user.target
fi

echo ""
echo "*** CONFIG ***"
# based on https://github.com/Stadicus/guides/blob/master/raspibolt/raspibolt_20_pi.md#raspi-config

# set new default password for root user
echo "root:btcticker" | sudo chpasswd
echo "pi:btcticker" | sudo chpasswd



# change log rotates
echo "/var/log/syslog" >> ./rsyslog
echo "{" >> ./rsyslog
echo "	rotate 7" >> ./rsyslog
echo "	daily" >> ./rsyslog
echo "	missingok" >> ./rsyslog
echo "	notifempty" >> ./rsyslog
echo "	delaycompress" >> ./rsyslog
echo "	compress" >> ./rsyslog
echo "	postrotate" >> ./rsyslog
echo "		invoke-rc.d rsyslog rotate > /dev/null" >> ./rsyslog
echo "	endscript" >> ./rsyslog
echo "}" >> ./rsyslog
echo "" >> ./rsyslog
echo "/var/log/mail.info" >> ./rsyslog
echo "/var/log/mail.warn" >> ./rsyslog
echo "/var/log/mail.err" >> ./rsyslog
echo "/var/log/mail.log" >> ./rsyslog
echo "/var/log/daemon.log" >> ./rsyslog
echo "{" >> ./rsyslog
echo "        rotate 4" >> ./rsyslog
echo "        size=100M" >> ./rsyslog
echo "        missingok" >> ./rsyslog
echo "        notifempty" >> ./rsyslog
echo "        compress" >> ./rsyslog
echo "        delaycompress" >> ./rsyslog
echo "        sharedscripts" >> ./rsyslog
echo "        postrotate" >> ./rsyslog
echo "                invoke-rc.d rsyslog rotate > /dev/null" >> ./rsyslog
echo "        endscript" >> ./rsyslog
echo "}" >> ./rsyslog
echo "" >> ./rsyslog
echo "/var/log/kern.log" >> ./rsyslog
echo "/var/log/auth.log" >> ./rsyslog
echo "{" >> ./rsyslog
echo "        rotate 4" >> ./rsyslog
echo "        size=100M" >> ./rsyslog
echo "        missingok" >> ./rsyslog
echo "        notifempty" >> ./rsyslog
echo "        compress" >> ./rsyslog
echo "        delaycompress" >> ./rsyslog
echo "        sharedscripts" >> ./rsyslog
echo "        postrotate" >> ./rsyslog
echo "                invoke-rc.d rsyslog rotate > /dev/null" >> ./rsyslog
echo "        endscript" >> ./rsyslog
echo "}" >> ./rsyslog
echo "" >> ./rsyslog
echo "/var/log/user.log" >> ./rsyslog
echo "/var/log/lpr.log" >> ./rsyslog
echo "/var/log/cron.log" >> ./rsyslog
echo "/var/log/debug" >> ./rsyslog
echo "/var/log/messages" >> ./rsyslog
echo "{" >> ./rsyslog
echo "	rotate 4" >> ./rsyslog
echo "	weekly" >> ./rsyslog
echo "	missingok" >> ./rsyslog
echo "	notifempty" >> ./rsyslog
echo "	compress" >> ./rsyslog
echo "	delaycompress" >> ./rsyslog
echo "	sharedscripts" >> ./rsyslog
echo "	postrotate" >> ./rsyslog
echo "		invoke-rc.d rsyslog rotate > /dev/null" >> ./rsyslog
echo "	endscript" >> ./rsyslog
echo "}" >> ./rsyslog
sudo mv ./rsyslog /etc/logrotate.d/rsyslog
sudo chown root:root /etc/logrotate.d/rsyslog
sudo service rsyslog restart

echo ""
echo "*** SOFTWARE UPDATE ***"
# based on https://github.com/Stadicus/guides/blob/master/raspibolt/raspibolt_20_pi.md#software-update

# installs like on RaspiBolt
sudo apt install -y htop git curl bash-completion vim jq dphys-swapfile bsdmainutils

# installs bandwidth monitoring for future statistics
sudo apt install -y vnstat

# network tools
sudo apt install -y autossh telnet

# prepare for display graphics mode
sudo apt install -y fbi

sudo apt-get install -y qrencode

# prepare for powertest
sudo apt install -y sysbench

# check for dependencies on DietPi, Ubuntu, Armbian
sudo apt install -y build-essential

# add armbian-config
if [ "${baseimage}" = "armbian" ]; then
  # add armbian config
  sudo apt install armbian-config -y
fi

# dependencies for python
sudo apt install -y python3-venv python3-dev python3-wheel python3-jinja2 python3-pip python3-pil python3-numpy libatlas-base-dev python3-flask

# make sure /usr/bin/pip exists (and calls pip3 in Debian Buster)
sudo update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# rsync is needed to copy from HDD
sudo apt install -y rsync
# install ifconfig
sudo apt install -y net-tools
#to display hex codes
sudo apt install -y xxd
# setuptools needed for Nyx
sudo pip install setuptools
# install OpenSSH client + server
sudo apt install -y openssh-client
sudo apt install -y openssh-sftp-server
sudo apt install -y sshpass
# install killall, fuser
sudo apt install -y psmisc
# install firewall
sudo apt install -y ufw

# make sure sqlite3 is available
sudo apt install -y sqlite3
# nginx
#sudo apt-get install -y nginx-common
#sudo apt-get install -y nginx

sudo apt clean
sudo apt -y autoremove

# for background processes
sudo apt -y install screen

# for multiple (detachable/background) sessions when using SSH
sudo apt -y install tmux

# install a command-line fuzzy finder (https://github.com/junegunn/fzf)
sudo apt -y install fzf

echo "sleeping 60 seconds"
# sleep for 60 seconds
sleep 60

echo ""
echo "*** Python DEFAULT libs & dependencies ***"

# for setup shell scripts
sudo apt -y install dialog bc python3-dialog

# libs (for global python scripts)
sudo -H python3 -m pip install requests[socks]==2.28.0
sudo -H python3 -m pip install RPi.GPIO
sudo -H python3 -m pip install spidev
sudo -H python3 -m pip install sdnotify
sudo -H python3 -m pip install numpy==1.22.4
echo "sleeping 60 seconds"
# sleep for 60 seconds
sleep 60
sudo -H python3 -m pip install matplotlib==3.5.2
sleep 60
sudo -H python3 -m pip install pandas==1.4.2
sudo -H python3 -m pip install mplfinance==0.12.9b1

echo "sleeping 60 seconds"
# sleep for 60 seconds
sleep 60

# sudo -H python3 -m pip install flask-bootstrap
# sudo -H python3 -m pip install wtforms
# sudo -H python3 -m pip install gunicorn

# *** fail2ban ***
# based on https://stadicus.github.io/RaspiBolt/raspibolt_21_security.html
echo "*** HARDENING ***"
sudo apt install -y --no-install-recommends python3-systemd fail2ban

sudo rm -rf /home/admin/bcm2835-1.71
wget http://www.airspayce.com/mikem/bcm2835/bcm2835-1.71.tar.gz
tar zxvf bcm2835-1.71.tar.gz
cd bcm2835-1.71/
sudo ./configure
sudo make
sudo make check
sudo make install
cd ..


echo "sleeping 60 seconds"
# sleep for 60 seconds
sleep 60


echo ""
echo "*** ADDING MAIN USER admin ***"
# using the default password 'btcticker'

sudo adduser --disabled-password --gecos "" admin
echo "admin:btcticker" | sudo chpasswd
sudo adduser admin sudo
sudo chsh admin -s /bin/bash

sudo usermod -a -G gpio admin
sudo usermod -a -G spi admin

# configure sudo for usage without password entry
echo '%sudo ALL=(ALL) NOPASSWD:ALL' | sudo EDITOR='tee -a' visudo



echo ""
echo "Build matplot cache"
cd /home/admin/
sudo -u admin python3 -c "from pylab import *; set_loglevel('debug'); plot(); show()"

echo ""
echo "*** SHELL SCRIPTS AND ASSETS ***"

# copy btc-ticker repo from github
cd /home/admin/
sudo -u admin git config --global user.name "${githubUser}"
sudo -u admin git config --global user.email "johndoe@example.com"
sudo -u admin rm -rf /home/admin/btc-ticker
sudo -u admin git clone -b ${githubBranch} https://github.com/${githubUser}/btc-ticker.git
sudo -u admin cp -r /home/admin/btc-ticker/home.admin/*.* /home/admin
sudo -u admin chmod +x *.sh
sudo -u admin cp -r /home/admin/btc-ticker/home.admin/assets /home/admin/
sudo -u admin cp -r /home/admin/raspiblitz/home.admin/.tmux.conf /home/admin
sudo -u admin cp -r /home/admin/btc-ticker/home.admin/config.scripts /home/admin/
sudo -u admin chmod +x /home/admin/config.scripts/*.sh

cd /home/admin/btc-ticker/
sudo -H python3 setup.py install
cd /home/admin/

echo "sleeping 60 seconds"
# sleep for 60 seconds
sleep 60


sudo rm -rf /home/admin/e-Paper/
sudo -u admin git clone https://github.com/waveshare/e-Paper
cd /home/admin/e-Paper/RaspberryPi_JetsonNano/python
sudo python3 setup.py install
cd /home/admin/

echo "sleeping 60 seconds"
# sleep for 60 seconds
sleep 60

# add /sbin to path for all
sudo bash -c "echo 'PATH=\$PATH:/sbin' >> /etc/profile"

echo ""
echo "*** BTCTICKER EXTRAS ***"


# optimization for torrent download
sudo bash -c "echo 'net.core.rmem_max = 4194304' >> /etc/sysctl.conf"
sudo bash -c "echo 'net.core.wmem_max = 1048576' >> /etc/sysctl.conf"

sudo bash -c "echo '' >> /home/admin/.bashrc"
sudo bash -c "echo 'NG_CLI_ANALYTICS=ci' >> /home/admin/.bashrc"

homeFile=/home/admin/.bashrc
keyBindings="source /usr/share/doc/fzf/examples/key-bindings.bash"
keyBindingsDone=$(grep -c "$keyBindings" $homeFile)

if [ ${keyBindingsDone} -eq 0 ]; then
  sudo bash -c "echo 'source /usr/share/doc/fzf/examples/key-bindings.bash' >> /home/admin/.bashrc"
  echo "key-bindings added to $homeFile"
else
  echo "key-bindings already in $homeFile"
fi


echo ""
echo "*** SWAP FILE ***"
# based on https://github.com/Stadicus/guides/blob/master/raspibolt/raspibolt_20_pi.md#moving-the-swap-file
# but just deactivating and deleting old (will be created alter when user adds HDD)

sudo dphys-swapfile swapoff
sudo dphys-swapfile uninstall

echo ""
echo "*** INCREASE OPEN FILE LIMIT ***"
# based on https://github.com/Stadicus/guides/blob/master/raspibolt/raspibolt_20_pi.md#increase-your-open-files-limit

sudo sed --in-place -i "56s/.*/*    soft nofile 128000/" /etc/security/limits.conf
sudo bash -c "echo '*    hard nofile 128000' >> /etc/security/limits.conf"
sudo bash -c "echo 'root soft nofile 128000' >> /etc/security/limits.conf"
sudo bash -c "echo 'root hard nofile 128000' >> /etc/security/limits.conf"
sudo bash -c "echo '# End of file' >> /etc/security/limits.conf"

sudo sed --in-place -i "23s/.*/session required pam_limits.so/" /etc/pam.d/common-session

sudo sed --in-place -i "25s/.*/session required pam_limits.so/" /etc/pam.d/common-session-noninteractive
sudo bash -c "echo '# end of pam-auth-update config' >> /etc/pam.d/common-session-noninteractive"



# *** CACHE DISK IN RAM ***
echo "Activating CACHE RAM DISK ... "
sudo /home/admin/config.scripts/ticker.cache.sh on

# *** Bluetooth & other configs ***
if [ "${baseimage}" = "raspbian" ]||[ "${baseimage}" = "raspios_arm64"  ]||\
   [ "${baseimage}" = "debian_rpi64" ]; then

  echo ""
  echo "*** DISABLE BLUETOOTH ***"

  configFile="/boot/config.txt"
  disableBT="dtoverlay=disable-bt"
  disableBTDone=$(grep -c "$disableBT" $configFile)

  if [ ${disableBTDone} -eq 0 ]; then
    # disable bluetooth module
    sudo echo "" >> $configFile
    sudo echo "# Raspiblitz" >> $configFile
    echo 'dtoverlay=pi3-disable-bt' | sudo tee -a $configFile
    echo 'dtoverlay=disable-bt' | sudo tee -a $configFile
  else
    echo "disable BT already in $configFile"
  fi

  # remove bluetooth services
  sudo systemctl disable bluetooth.service
  sudo systemctl disable hciuart.service

  # remove bluetooth packages
  sudo apt remove -y --purge pi-bluetooth bluez bluez-firmware
  echo

  # disable audio
  echo "*** DISABLE AUDIO (snd_bcm2835) ***"
  sudo sed -i "s/^dtparam=audio=on/# dtparam=audio=on/g" /boot/config.txt
  echo

  # disable DRM VC4 V3D
  echo "*** DISABLE DRM VC4 V3D driver ***"
  dtoverlay=vc4-fkms-v3d
  sudo sed -i "s/^dtoverlay=vc4-fkms-v3d/# dtoverlay=vc4-fkms-v3d/g" /boot/config.txt
  echo

  # I2C fix (make sure dtparam=i2c_arm is not on)
  sudo sed -i "s/^dtparam=i2c_arm=.*//g" /boot/config.txt
  #enable SPI
   sudo sed -i "s/^dtparam=spi=off/dtparam=spi=on/g" /boot/config.txt
fi

sudo timedatectl set-timezone Europe/Berlin

# *** BOOTSTRAP ***
# see background README for details
echo ""
echo "*** RASPI BOOTSTRAP SERVICE ***"
sudo chmod +x /home/admin/_bootstrap.sh
sudo cp ./assets/bootstrap.service /etc/systemd/system/bootstrap.service
sudo systemctl enable bootstrap

echo ""
echo "*** btc-ticker SERVICE ***"
sudo chmod +x /home/admin/run.sh
sudo cp /home/admin/assets/btcticker.service /etc/systemd/system/btcticker.service
sudo systemctl enable btcticker

echo "*** ro remount SERVICE ***"
sudo cp ./assets/ro_remount.service /etc/systemd/system/ro_remount.service
sudo systemctl enable ro_remount

# echo "*** check wlan SERVICE ***"
# sudo cp ./assets/check_wifi.service /etc/systemd/system/check_wifi.service
#sudo systemctl enable check_wifi.service

echo "sleeping 60 seconds"
# sleep for 60 seconds
sleep 60

# Enable firewwall
sudo /home/admin/90finishSetup.sh

# *** BTCTICKER IMAGE READY INFO ***
echo ""
echo "**********************************************"
echo "BASIC SD CARD BUILD DONE"
echo "**********************************************"
echo ""
echo "Your SD Card Image for btc-ticker is ready (might still do display config)."
echo "Take the chance & look thru the output above if you can spot any errors or warnings."
echo ""
echo "IMPORTANT IF WANT TO MAKE A RELEASE IMAGE FROM THIS BUILD:"
echo "1. login fresh --> user:admin password:btcticker"
echo "2. run --> ./XXprepareRelease.sh"
echo ""


# (do last - because might trigger reboot)
if [ "${displayClass}" != "eink" ] || [ "${baseimage}" = "raspbian" ] || [ "${baseimage}" = "raspios_arm64" ]; then
  echo "*** ADDITIONAL DISPLAY OPTIONS ***"
  echo "- calling: ticker.display.sh set-display ${displayClass}"
  sudo /home/admin/config.scripts/ticker.display.sh set-display ${displayClass}
  #sudo /home/admin/config.scripts/ticker.display.sh rotate 1
fi