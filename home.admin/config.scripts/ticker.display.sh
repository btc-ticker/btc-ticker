#!/bin/bash

# command info
if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "-help" ]; then
  echo "# make changes to the LCD screen"
  echo "# ticker.display.sh rotate [on|off]"
  echo "# ticker.display.sh image [path]"
  echo "# ticker.display.sh set-display [eink|lcd]"
  exit 1
fi

# 1. Parameter: lcd command
command=$1

# check if LCD (/dev/fb1) or HDMI (/dev/fb0)
# see https://github.com/rootzoll/raspiblitz/pull/1580
# but basically this just says if the driver for GPIO LCD is installed - not if connected
lcdExists=$(sudo ls /dev/fb1 2>/dev/null | grep -c "/dev/fb1")


##################
# ROTATE
# see issue: https://github.com/rootzoll/raspiblitz/issues/681
###################

if [ "${command}" == "rotate" ]; then

  # TURN ROTATE ON (the new default)
  if [ "$2" = "1" ] || [ "$2" = "on" ]; then

    # change rotation config
    echo "# Turn ON: LCD ROTATE"
    sudo sed -i "s/^dtoverlay=.*/dtoverlay=waveshare35a:rotate=90/g" /boot/config.txt
    sudo rm /etc/X11/xorg.conf.d/40-libinput.conf >/dev/null
    echo "# OK - a restart is needed: sudo shutdown -r now"

  # TURN ROTATE OFF
  elif [ "$2" = "0" ] || [ "$2" = "off" ]; then

    # change rotation config
    echo "#Turn OFF: LCD ROTATE"
    sudo sed -i "s/^dtoverlay=.*/dtoverlay=waveshare35a:rotate=270/g" /boot/config.txt


    echo "# also rotate touchscreen ..."
    cat << EOF | sudo tee /etc/X11/xorg.conf.d/40-libinput.conf >/dev/null
Section "InputClass"
        Identifier "libinput touchscreen catchall"
        MatchIsTouchscreen "on"
        Option "CalibrationMatrix" "0 1 0 -1 0 1 0 0 1"
        MatchDevicePath "/dev/input/event*"
        Driver "libinput"
EndSection
EOF
    echo "OK - a restart is needed: sudo shutdown -r now"

  else
    echo "error='missing second parameter - see help'"
    exit 1
  fi
  exit 0
fi


###################
# IMAGE
###################

if [ "${command}" == "image" ]; then

  imagePath=$2
  if [ ${#imagePath} -eq 0 ]; then
    echo "error='missing second parameter - see help'"
    exit 1
  else
    # test the image path - if file exists
    if [ -f "$imagePath" ]; then
      echo "# OK - file exists: ${imagePath}"
    else
      echo "error='file does not exist'"
      exit 1
    fi
  fi

  # see https://github.com/rootzoll/raspiblitz/pull/1580
  if [ ${lcdExists} -eq 1 ] ; then
    # LCD
    sudo fbi -a -T 1 -d /dev/fb1 --noverbose ${imagePath} 2> /dev/null
  else
    # HDMI
    sudo fbi -a -T 1 -d /dev/fb0 --noverbose ${imagePath} 2> /dev/null
  fi
  exit 0
fi

function install_eink() {
  echo "# nothing to install - eink is the default/clean mode"
}

function uninstall_eink() {
  echo "# nothing to uninstall - eink is the default/clean mode"
}


function install_lcd() {

  echo "*** 32bit LCD DRIVER ***"
  echo "--> Downloading LCD Driver from Github"
  cd /home/admin/
  sudo -u admin git clone https://github.com/MrYacha/LCD-show.git
  sudo -u admin chmod -R 755 LCD-show
  sudo -u admin chown -R admin:admin LCD-show
  cd LCD-show/
  sudo -u admin git reset --hard 53dd0bf || exit 1
  # install xinput calibrator package
  echo "--> install xinput calibrator package"
  sudo apt install -y libxi6
  sudo dpkg -i xinput-calibrator_0.7.5-1_armhf.deb

  # activate LCD and trigger reboot
  # dont do this on dietpi to allow for automatic build

  echo "Installing 32-bit LCD drivers ..."
  sudo chmod +x -R /home/admin/LCD-show
  cd /home/admin/LCD-show/
  sudo apt-mark hold raspberrypi-bootloader
  sudo ./LCD35-show

}


function uninstall_lcd() {

  echo "# UNINSTALL 64bit LCD DRIVER"

  # hold bootloader
  sudo apt-mark hold raspberrypi-bootloader

  # make sure xinput-calibrator is installed
  sudo apt-get install -y xinput-calibrator

  # remove modifications of config.txt
  sudo sed -i '/^hdmi_force_hotplug=/d' /boot/config.txt 2>/dev/null
  sudo sed -i '/^hdmi_group=/d' /boot/config.txt 2>/dev/null
  sudo sed -i "/^hdmi_mode=/d" /boot/config.txt 2>/dev/null
  sudo sed -i "s/^dtoverlay=.*//g" /boot/config.txt 2>/dev/null
  echo "hdmi_group=1" >> /boot/config.txt
  echo "hdmi_mode=3" >> /boot/config.txt
  echo "dtoverlay=pi3-disable-bt" >> /boot/config.txt
  echo "dtoverlay=disable-bt" >> /boot/config.txt

  # remove modification of cmdline.txt
  sudo sed -i "s/ dwc_otg.lpm_enable=0 quiet fbcon=map:10 fbcon=font:ProFont6x11 logo.nologo//g" /boot/cmdline.txt

  # un-prepare X11
  sudo mv /home/admin/wavesharelcd-64bit-rpi/40-libinput.conf /etc/X11/xorg.conf.d/40-libinput.conf 2>/dev/null
  sudo rm -rf /etc/X11/xorg.conf.d/99-calibration.conf


  echo "# OK uninstall LCD done ... reboot needed"

}


###################
# SET DISPLAY TYPE
###################

if [ "${command}" == "set-display" ]; then

  paramDisplayClass=$2
  paramDisplayType=$3
  echo "# ticker.display.sh set-display ${paramDisplayClass} ${paramDisplayType}"

  # check if started with sudo
  if [ "$EUID" -ne 0 ]; then
    echo "error='missing sudo'"
    exit 1
  fi

  # check if display class parameter is given
  if [ "${paramDisplayClass}" == "" ]; then
    echo "err='missing parameter'"
    exit 1
  fi

  echo "# old(${displayClass})"
  echo "# new(${paramDisplayClass})"

  if [ "${paramDisplayClass}" == "eink" ] || [ "${paramDisplayClass}" == "lcd" ]; then

    # uninstall old state
    uninstall_$displayClass

    # install new state
    install_$paramDisplayClass

  else
    echo "err='unknown parameter'"
    exit 1
  fi

  exit 0

fi

# unknown command
echo "error='unknown command'"
exit 1