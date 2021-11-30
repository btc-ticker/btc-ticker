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

  echo "# INSTALL 64bit LCD DRIVER"

  # set font
  sudo sed -i "s/^CHARMAP=.*/CHARMAP=\"UTF-8\"/" /etc/default/console-setup
  sudo sed -i "s/^CODESET=.*/CODESET=\"guess\"/" /etc/default/console-setup
  sudo sed -i "s/^FONTFACE=.*/FONTFACE=\"TerminusBoldVGA\"/" /etc/default/console-setup
  sudo sed -i "s/^FONTSIZE=.*/FONTSIZE=\"8x16\"/" /etc/default/console-setup

  # hold bootloader
  sudo apt-mark hold raspberrypi-bootloader

  # Downloading LCD Driver from Github
  cd /home/admin/
  sudo -u admin git clone https://github.com/tux1c/wavesharelcd-64bit-rpi.git
  sudo -u admin chmod -R 755 wavesharelcd-64bit-rpi
  sudo -u admin chown -R admin:admin wavesharelcd-64bit-rpi
  cd /home/admin/wavesharelcd-64bit-rpi
  sudo -u admin git reset --hard 5a206a7 || exit 1

  # customized from https://github.com/tux1c/wavesharelcd-64bit-rpi/blob/master/install.sh
  # prepare X11
  sudo mkdir -p /etc/X11/xorg.conf.d
  sudo mv /etc/X11/xorg.conf.d/40-libinput.conf /home/admin/wavesharelcd-64bit-rpi/40-libinput.conf 2>/dev/null
  sudo cp -rf ./99-calibration.conf /etc/X11/xorg.conf.d/99-calibration.conf
  # sudo cp -rf ./99-fbturbo.conf  /etc/X11/xorg.conf.d/99-fbturbo.conf # there is no such file

  # add waveshare mod
  sudo cp ./waveshare35a.dtbo /boot/overlays/

  # modify /boot/config.txt
  sudo sed -i "s/^hdmi_force_hotplug=.*//g" /boot/config.txt
  sudo sed -i '/^hdmi_group=/d' /boot/config.txt 2>/dev/null
  sudo sed -i "/^hdmi_mode=/d" /boot/config.txt 2>/dev/null
  #echo "hdmi_force_hotplug=1" >> /boot/config.txt
  sudo sed -i "s/^dtparam=i2c_arm=.*//g" /boot/config.txt
  # echo "dtparam=i2c_arm=on" >> /boot/config.txt --> this is to be called I2C errors - see: https://github.com/rootzoll/raspiblitz/issues/1058#issuecomment-739517713
  # don't enable SPI and UART ports by default
  # echo "dtparam=spi=on" >> /boot/config.txt
  # echo "enable_uart=1" >> /boot/config.txt
  sudo sed -i "s/^dtoverlay=.*//g" /boot/config.txt
  echo "dtoverlay=waveshare35a:rotate=90" >> /boot/config.txt

  # modify cmdline.txt
  modification="dwc_otg.lpm_enable=0 quiet fbcon=map:10 fbcon=font:ProFont6x11 logo.nologo"
  containsModification=$(sudo grep -c "${modification}" /boot/cmdline.txt)
  if [ ${containsModification} -eq 0 ]; then
    echo "# adding modification to /boot/cmdline.txt"
    cmdlineContent=$(sudo cat /boot/cmdline.txt)
    echo "${cmdlineContent} ${modification}" > /boot/cmdline.txt
  else
    echo "# /boot/cmdline.txt already contains modification"
  fi
  containsModification=$(sudo grep -c "${modification}" /boot/cmdline.txt)
  if [ ${containsModification} -eq 0 ]; then
    echo "# FAIL: was not able to modify /boot/cmdline.txt"
    echo "err='ended unclear state'"
    exit 1
  fi

  # touch screen calibration
  apt-get install -y xserver-xorg-input-evdev
  cp -rf /usr/share/X11/xorg.conf.d/10-evdev.conf /usr/share/X11/xorg.conf.d/45-evdev.conf
  # TODO manual touchscreen calibration option
  # https://github.com/tux1c/wavesharelcd-64bit-rpi#adapting-guide-to-other-lcds

  # set font that fits the LCD screen
  # https://github.com/rootzoll/raspiblitz/issues/244#issuecomment-476713706
  # there can be a different font for different types of LCDs with using the displayType parameter in the future
  sudo setfont /usr/share/consolefonts/Uni3-TerminusBold16.psf.gz

  echo "# OK install of LCD done ... reboot needed"

}

function install_lcd_legacy() {

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

  # remove github code of LCD drivers
  sudo rm -r /home/admin/wavesharelcd-64bit-rpi

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