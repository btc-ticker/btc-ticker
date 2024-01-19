#!/bin/bash
#########################################################################
# Build your SD card image based on: 2023-12-05-raspios-bookworm-armhf.img.xz
# https://downloads.raspberrypi.org/raspios_oldstable_armhf/images/raspios_oldstable_armhf-2023-12-06/
# SHA256: ca3b1c40b7b051e1626b663e16fbf5a0a8abff3b8a3a27319d164d52b0c96c05
# also change in: btc-ticker/ci/armhf-rpi/build.arm64-rpi.pkr.hcl
# PGP fingerprint: 8738CD6B956F460C - to check signature:
# curl -O https://www.raspberrypi.org/raspberrypi_downloads.gpg.key && gpg --import ./raspberrypi_downloads.gpg.key && gpg --verify *.sig
# setup fresh SD card with image above - login via SSH and run this script:
##########################################################################

defaultRepo="btc-ticker" #user that hosts a `btc-ticker` repo
defaultBranch="main"

me="${0##/*}"

nocolor="\033[0m"
red="\033[31m"

## usage as a function to be called whenever there is a huge mistake on the options
usage(){
  printf %s"${me} [--option <argument>]

Options:
  -EXPORT                                  just print build parameters & exit'
  -h, --help                               this help info
  -i, --interaction [0|1]                  interaction before proceeding with execution (default: 1)
  -f, --fatpack [0|1]                      fatpack mode (default: 1)
  -u, --github-user [btc-ticker|other]     github user to be checked from the repo (default: ${defaultRepo})
  -b, --branch [main|other]                 branch to be built on (default: ${defaultBranch})
  -d, --display [eink|lcd]        display class (default: eink)
  -t, --tweak-boot-drive [0|1]             tweak boot drives (default: 1)
  -w, --wifi-region [off|DE|US|GB|other]      wifi iso code (default: DE) or 'off'

Notes:
  all options, long and short accept --opt=value mode also
  [0|1] can also be referenced as [false|true]
"
  exit 1
}
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
  usage
fi

# check if started with sudo
if [ "$EUID" -ne 0 ]; then
  echo "error='run as root / may use sudo'"
  exit 1
fi

if [ "$1" = "-EXPORT" ] || [ "$1" = "EXPORT" ]; then
  cd /home/admin/btc-ticker 2>/dev/null
  activeBranch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
  if [ "${activeBranch}" == "" ]; then
    activeBranch="${defaultBranch}"
  fi
  echo "githubUser='${defaultRepo}'"
  echo "githubBranch='${activeBranch}'"
  echo "defaultAPIuser='${defaultAPIuser}'"
  echo "defaultAPIrepo='${defaultAPIrepo}'"
  echo "defaultWEBUIuser='${defaultWEBUIuser}'"
  echo "defaultWEBUIrepo='${defaultWEBUIrepo}'"
  exit 0
fi

## default user message
error_msg(){ printf %s"${red}${me}: ${1}${nocolor}\n"; exit 1; }

## assign_value variable_name "${opt}"
## it strips the dashes and assign the clean value to the variable
## assign_value status --on IS status=on
## variable_name is the name you want it to have
## $opt being options with single or double dashes that don't require arguments
assign_value(){
  case "${2}" in
    --*) value="${2#--}";;
    -*) value="${2#-}";;
    *) value="${2}"
  esac
  case "${value}" in
    0) value="false";;
    1) value="true";;
  esac
  ## Escaping quotes is needed because else if will fail if the argument is quoted
  # shellcheck disable=SC2140
  eval "${1}"="\"${value}\""
}

## get_arg variable_name "${opt}" "${arg}"
## get_arg service --service ssh
## variable_name is the name you want it to have
## $opt being options with single or double dashes
## $arg is requiring and argument, else it fails
## assign_value "${1}" "${3}" means it is assining the argument ($3) to the variable_name ($1)
get_arg(){
  case "${3}" in
    ""|-*) error_msg "Option '${2}' requires an argument.";;
  esac
  assign_value "${1}" "${3}"
}

## hacky getopts
## 1. if the option requires an argument, and the option is preceeded by single or double dash and it
##    can be it can be specified with '-s=ssh' or '-s ssh' or '--service=ssh' or '--service ssh'
##    use: get_arg variable_name "${opt}" "${arg}"
## 2. if a bunch of options that does different things are to be assigned to the same variable
##    and the option is preceeded by single or double dash use: assign_value variable_name "${opt}"
##    as this option does not require argument, specifu $shift_n=1
## 3. if the option does not start with dash and does not require argument, assign to command manually.
while :; do
  case "${1}" in
    -*=*) opt="${1%=*}"; arg="${1#*=}"; shift_n=1;;
    -*) opt="${1}"; arg="${2}"; shift_n=2;;
    *) opt="${1}"; arg="${2}"; shift_n=1;;
  esac
  case "${opt}" in
    -i|-i=*|--interaction|--interaction=*) get_arg interaction "${opt}" "${arg}";;
    -f|-f=*|--fatpack|--fatpack=*) get_arg fatpack "${opt}" "${arg}";;
    -u|-u=*|--github-user|--github-user=*) get_arg github_user "${opt}" "${arg}";;
    -b|-b=*|--branch|--branch=*) get_arg branch "${opt}" "${arg}";;
    -d|-d=*|--display|--display=*) get_arg display "${opt}" "${arg}";;
    -t|-t=*|--tweak-boot-drive|--tweak-boot-drive=*) get_arg tweak_boot_drive "${opt}" "${arg}";;
    -w|-w=*|--wifi-region|--wifi-region=*) get_arg wifi_region "${opt}" "${arg}";;
    "") break;;
    *) error_msg "Invalid option: ${opt}";;
  esac
  shift "${shift_n}"
done

## if there is a limited option, check if the value of variable is within this range
## $ range_argument variable_name possible_value_1 possible_value_2
range_argument(){
  name="${1}"
  eval var='$'"${1}"
  shift
  if [ -n "${var:-}" ]; then
    success=0
    for tests in "${@}"; do
      [ "${var}" = "${tests}" ] && success=1
    done
    [ ${success} -ne 1 ] && error_msg "Option '--${name}' cannot be '${var}'! It can only be: ${*}."
  fi
}

apt_install() {
  for package in "$@"; do
    apt-get install -y -q "$package"
    if [ $? -eq 100 ]; then
      echo "FAIL! apt-get failed to install package: $package"
      exit 1
    fi
  done
}

general_utils="curl"
## loop through all general_utils to see if program is installed (placed on PATH) and if not, add to the list of commands to be installed
for prog in ${general_utils}; do
  ! command -v ${prog} >/dev/null && general_utils_install="${general_utils_install} ${prog}"
done
## if any of the required programs are not installed, update and if successfull, install packages
if [ -n "${general_utils_install}" ]; then
  echo -e "\n*** SOFTWARE UPDATE ***"
  apt-get update -y || exit 1
  apt_install ${general_utils_install}
fi

## use default values for variables if empty

# INTERACTION
# ----------------------------------------
# When 'false' then no questions will be asked on building .. so it can be used in build scripts
# for containers or as part of other build scripts (default is true)
: "${interaction:=true}"
range_argument interaction "0" "1" "false" "true"

# FATPACK
# -------------------------------
# could be 'true' (default) or 'false'
# When 'true' it will pre-install needed frameworks for additional apps and features
# as a convenience to safe on install and update time for additional apps.
# When 'false' it will just install the bare minimum and additional apps will just
# install needed frameworks and libraries on demand when activated by user.
# Use 'false' if you want to run your node without: go, dot-net, nodejs, docker, ...
: "${fatpack:=true}"
range_argument fatpack "0" "1" "false" "true"

# GITHUB-USERNAME
# ---------------------------------------
# could be any valid github-user that has a fork of the btc-ticker repo - 'btc-ticker' is default
# The 'btc-ticker' repo of this user is used to provisioning sd card with btc-ticker assets/scripts later on.
: "${github_user:=$defaultRepo}"
curl --header "X-GitHub-Api-Version:2022-11-28" -s "https://api.github.com/repos/${github_user}/btc-ticker" | grep -q "\"message\": \"Not Found\"" && error_msg "Repository 'btc-ticker' not found for user '${github_user}"

# GITHUB-BRANCH
# -------------------------------------
# could be any valid branch or tag of the given GITHUB-USERNAME forked btc-ticker repo
: "${branch:=$defaultBranch}"
curl --header "X-GitHub-Api-Version:2022-11-28" -s "https://api.github.com/repos/${github_user}/btc-ticker/branches/${branch}" | grep -q "\"message\": \"Branch not found\"" && error_msg "Repository 'btc-ticker' for user '${github_user}' does not contain branch '${branch}'"

# DISPLAY-CLASS
# ----------------------------------------
# Could be 'eink', 'lcd' (eink is default)
: "${display:=eink}"
range_argument display "eink" "lcd"

# TWEAK-BOOTDRIVE
# ---------------------------------------
# could be 'true' (default) or 'false'
# If 'true' it will try (based on the base OS) to optimize the boot drive.
# If 'false' this will skipped.
: "${tweak_boot_drive:=true}"
range_argument tweak_boot_drive "0" "1" "false" "true"

# WIFI
# ---------------------------------------
# WIFI country code like 'DE' (default)
# If any valid wifi country code Wifi will be activated with that country code by default
: "${wifi_region:=DE}"


echo ""
echo "*****************************************"
echo "* BTCTICKER SD CARD IMAGE SETUP v0.6.0  *"
echo "*****************************************"
echo "For details on optional parameters - see build script source code:"


# output
for key in interaction fatpack github_user branch display tweak_boot_drive wifi_region; do
  eval val='$'"${key}"
  [ -n "${val}" ] && printf '%s\n' "${key}=${val}"
done

# AUTO-DETECTION: CPU-ARCHITECTURE
# ---------------------------------------
cpu="$(uname -m)" && echo "cpu=${cpu}"
case "${cpu}" in
  aarch64|x86_64|armv7l|armv6l);;
  *) echo -e "# FAIL #\nCan only build on aarch64 or x86_64 not on: cpu=${cpu}"; exit 1;;
esac
architecture="$(dpkg --print-architecture 2>/dev/null)" && echo "architecture=${architecture}"
case "${architecture}" in
  arm*|amd64|armv7l|armv6l);;
  *) echo -e "# FAIL #\nCan only build on arm* or amd64 not on: architecture=${cpu}"; exit 1;;
esac

# AUTO-DETECTION: OPERATINGSYSTEM
# ---------------------------------------
if [ $(cat /etc/os-release 2>/dev/null | grep -c 'Debian') -gt 0 ]; then
  if [ -f /etc/apt/sources.list.d/raspi.list ] && [ "${cpu}" = armv7l ]; then
    # default image for RaspberryPi
    baseimage="raspios_armhf"
  else
    # experimental: fallback for all to debian
    baseimage="debian"
  fi
elif [ $(cat /etc/os-release 2>/dev/null | grep -c 'Ubuntu') -gt 0 ]; then
  baseimage="ubuntu"
elif [ $(cat /etc/os-release 2>/dev/null | grep -c 'Armbian') -gt 0 ]; then
  baseimage="armbian"
elif [ $(cat /etc/os-release 2>/dev/null | grep -c 'Raspbian') -gt 0 ]; then
  baseimage="raspbian"
else
  echo "\n# FAIL: Base Image cannot be detected or is not supported."
  cat /etc/os-release 2>/dev/null
  uname -a
  exit 1
fi
echo "baseimage=${baseimage}"

# USER-CONFIRMATION
if [ "${interaction}" = "true" ]; then
  echo -n "# Do you agree with all parameters above? (yes/no) "
  read -r installBtcTickerAnswer
  [ "$installBtcTickerAnswer" != "yes" ] && exit 1
fi
echo -e "Building BTC-Ticker ...\n"
sleep 3 ## give time to cancel

export DEBIAN_FRONTEND=noninteractive

echo "*** Prevent sleep ***" # on all platforms https://wiki.debian.org/Suspend
systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
mkdir /etc/systemd/sleep.conf.d
echo "[Sleep]
AllowSuspend=no
AllowHibernation=no
AllowSuspendThenHibernate=no
AllowHybridSleep=no" | tee /etc/systemd/sleep.conf.d/nosuspend.conf
mkdir /etc/systemd/logind.conf.d
echo "[Login]
HandleLidSwitch=ignore
HandleLidSwitchDocked=ignore" | tee /etc/systemd/logind.conf.d/nosuspend.conf

# FIXING LOCALES
# https://daker.me/2014/10/how-to-fix-perl-warning-setting-locale-failed-in-raspbian.html
# https://stackoverflow.com/questions/38188762/generate-all-locales-in-a-docker-image
if [ "${cpu}" = "aarch64" ] && { [ "${baseimage}" = "raspios_arm64" ] || [ "${baseimage}" = "raspian" ] || [ "${baseimage}" = "debian" ]; }; then
  echo -e "\n*** FIXING LOCALES FOR BUILD ***"
  sed -i "s/^# en_US.UTF-8 UTF-8.*/en_US.UTF-8 UTF-8/g" /etc/locale.gen
  sed -i "s/^# en_US ISO-8859-1.*/en_US ISO-8859-1/g" /etc/locale.gen
  locale-gen
  export LC_ALL=C
  export LANGUAGE=en_US.UTF-8
  export LANG=en_US.UTF-8
  if [ ! -f /etc/apt/sources.list.d/raspi.list ]; then
    echo "# Add the archive.raspberrypi.org/debian/ to the sources.list"
    echo "deb http://archive.raspberrypi.org/debian/ bullseye main" | tee /etc/apt/sources.list.d/raspi.list
  fi
fi


# remove some (big) packages that are not needed

apt remove --purge -y libreoffice* oracle-java* chromium-browser nuscratch scratch sonic-pi plymouth python2 vlc cups vnstat
apt remove --purge -y thonny libqt5* realvnc-vnc-server libgstreamer*
if [ "${display}" == "eink" ]; then
  apt remove -y --purge xserver* lightdm* lxde* mesa* lx* gnome* desktop* gstreamer* pulseaudio*
  apt remove -y --purge raspberrypi-ui-mods  gtk* hicolor-icon-theme*
else
  apt remove -y --purge lightdm* vlc* lxde* lx* mesa* chromium* desktop* gnome* gstreamer* pulseaudio*
  apt remove -y --purge raspberrypi-ui-mods gtk* hicolor-icon-theme*
fi
apt clean -y
apt autoremove -y

echo -e "\n*** UPDATE Debian***"
apt-get update -y
apt-get upgrade -f -y

echo -e "\n*** Python DEFAULT libs & dependencies ***"

if [ -f "/usr/bin/python3.11" ]; then
  # use python 3.11 if available
  update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1
  # keep python backwards compatible
  ln -s /usr/bin/python3.11 /usr/bin/python3.9
  ln -s /usr/bin/python3.11 /usr/bin/python3.10
  echo "python calls python3.11"
elif [ -f "/usr/bin/python3.10" ]; then
  # use python 3.10 if available
  update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1
  # keep python backwards compatible
  ln -s /usr/bin/python3.10 /usr/bin/python3.9
  echo "python calls python3.10"
elif [ -f "/usr/bin/python3.9" ]; then
  # use python 3.9 if available
  update-alternatives --install /usr/bin/python python /usr/bin/python3.9 1
  echo "python calls python3.9"
elif [ -f "/usr/bin/python3.8" ]; then
  # use python 3.8 if available
  update-alternatives --install /usr/bin/python python /usr/bin/python3.8 1
  echo "python calls python3.8"
else
  echo "# FAIL #"
  echo "There is no tested version of python present"
  exit 1
fi

# don't protect system packages from pip install
for PYTHONDIR in /usr/lib/python3.*; do
  if [ -f "$PYTHONDIR/EXTERNALLY-MANAGED" ]; then
    rm "$PYTHONDIR/EXTERNALLY-MANAGED"
  fi
done

update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

echo -e "\n*** PREPARE ${baseimage} ***"

# make sure the pi user is present
if ! compgen -u pi; then
  echo "# Adding the user pi"
  adduser --system --group --shell /bin/bash --home /home/pi pi
  # copy the skeleton files for login
  sudo -u pi cp -r /etc/skel/. /home/pi/
  adduser pi sudo
fi

# special prepare when Raspbian
if [ "${baseimage}" = "raspbian" ]||[ "${baseimage}" = "raspios_armhf" ]||[ "${baseimage}" = "raspios_arm64" ]||\
   [ "${baseimage}" = "debian_rpi64" ]; then
  apt install -y raspi-config
  # do memory split (16MB)
  raspi-config nonint do_memory_split 16
  # set to wait until network is available on boot (0 seems to yes)
  raspi-config nonint do_boot_wait 0
  # Enable SPI
  raspi-config nonint do_spi 1
  # Enable i2c
  raspi-config nonint do_i2c 1
  # set WIFI country so boot does not block
  [ "${wifi_region}" != "off" ] && raspi-config nonint do_wifi_country $wifi_region

  configFile="/boot/config.txt"
  max_usb_current="max_usb_current=1"
  max_usb_currentDone=$(grep -c "$max_usb_current" $configFile)

  if [ ${max_usb_currentDone} -eq 0 ]; then
    echo | tee -a $configFile
    echo "# Raspiblitz" | tee -a $configFile
    echo "$max_usb_current" | tee -a $configFile
  else
    echo "$max_usb_current already in $configFile"
  fi

  # run fsck on sd root partition on every startup to prevent "maintenance login" screen
  # use command to check last fsck check: sudo tune2fs -l /dev/mmcblk0p2
  if [ "${tweak_boot_drive}" == "true" ]; then
    echo "* running tune2fs"
    tune2fs -c 1 /dev/mmcblk0p2
  else
    echo "* skipping tweak_boot_drive"
  fi

  # edit kernel parameters
  kernelOptionsFile=/boot/cmdline.txt
  fsOption1="fsck.mode=force"
  fsOption2="fsck.repair=yes"
  fsOption1InFile=$(grep -c ${fsOption1} ${kernelOptionsFile})
  fsOption2InFile=$(grep -c ${fsOption2} ${kernelOptionsFile})

  if [ ${fsOption1InFile} -eq 0 ]; then
    sed -i "s/^/$fsOption1 /g" "$kernelOptionsFile"
    echo "$fsOption1 added to $kernelOptionsFile"
  else
    echo "$fsOption1 already in $kernelOptionsFile"
  fi
  if [ ${fsOption2InFile} -eq 0 ]; then
    sed -i "s/^/$fsOption2 /g" "$kernelOptionsFile"
    echo "$fsOption2 added to $kernelOptionsFile"
  else
    echo "$fsOption2 already in $kernelOptionsFile"
  fi
fi

# special prepare when Nvidia Jetson Nano
if [ $(uname -a | grep -c 'tegra') -gt 0 ] ; then
  echo "Nvidia --> disable GUI on boot"
  systemctl set-default multi-user.target
fi

echo -e "\n*** CONFIG ***"
# based on https://github.com/Stadicus/guides/blob/master/raspibolt/raspibolt_20_pi.md#raspi-config

# set new default password for root user
echo "root:btcticker" | chpasswd
echo "pi:btcticker" | chpasswd

# limit journald system use
sed -i "s/^#SystemMaxUse=.*/SystemMaxUse=250M/g" /etc/systemd/journald.conf
sed -i "s/^#SystemMaxFileSize=.*/SystemMaxFileSize=50M/g" /etc/systemd/journald.conf


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
mv ./rsyslog /etc/logrotate.d/rsyslog
chown root:root /etc/logrotate.d/rsyslog
service rsyslog restart

echo ""
echo "*** SOFTWARE UPDATE ***"
# based on https://github.com/Stadicus/guides/blob/master/raspibolt/raspibolt_20_pi.md#software-update

# installs like on RaspiBolt
apt install -y htop git curl bash-completion vim jq dphys-swapfile bsdmainutils

# network tools
apt install -y autossh telnet

# prepare for display graphics mode
apt install -y fbi

apt-get install -y qrencode

# check for dependencies on DietPi, Ubuntu, Armbian
apt install -y build-essential

# add armbian-config
if [ "${baseimage}" = "armbian" ]; then
  # add armbian config
  apt install armbian-config -y
fi

# dependencies for python
apt install -y python3-venv python3-dev python3-wheel python3-jinja2 python3-pip python3-pil python3-numpy libatlas-base-dev python3-flask python3-matplotlib python3-pandas

# make sure /usr/bin/pip exists (and calls pip3 in Debian Buster)
update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# rsync is needed to copy from HDD
apt install -y rsync
# install ifconfig
apt install -y net-tools
#to display hex codes
apt install -y xxd
# install OpenSSH client + server
apt install -y openssh-client
apt install -y openssh-sftp-server
apt install -y sshpass
# install killall, fuser
apt install -y psmisc
# install firewall
apt install -y ufw

# make sure sqlite3 is available
apt install -y sqlite3
# nginx
#apt-get install -y nginx-common
#apt-get install -y nginx

apt clean
apt -y autoremove

# for background processes
apt -y install screen

# for multiple (detachable/background) sessions when using SSH
apt -y install tmux

# install a command-line fuzzy finder (https://github.com/junegunn/fzf)
apt -y install fzf

echo -e "\n*** Python DEFAULT libs & dependencies ***"

# for setup shell scripts
apt -y install dialog bc python3-dialog

# libs (for global python scripts)
sudo -H python3 -m pip install --upgrade pip
sudo -H python3 -m pip install setuptools
sudo -H python3 -m pip install requests[socks]==2.31.0
sudo -H python3 -m pip install RPi.GPIO
sudo -H python3 -m pip install spidev
sudo -H python3 -m pip install sdnotify
sudo -H python3 -m pip install pydantic
sudo -H python3 -m pip install mplfinance==0.12.10b0


# sudo -H python3 -m pip install flask-bootstrap
# sudo -H python3 -m pip install wtforms
# sudo -H python3 -m pip install gunicorn

# *** fail2ban ***
# based on https://stadicus.github.io/RaspiBolt/raspibolt_21_security.html
echo "*** HARDENING ***"
apt install -y --no-install-recommends python3-systemd fail2ban

rm -rf /home/admin/bcm2835-1.73
wget http://www.airspayce.com/mikem/bcm2835/bcm2835-1.73.tar.gz
tar zxvf bcm2835-1.73.tar.gz
cd bcm2835-1.73/
./configure
make
# make check
make install
cd ..


echo -e "\n*** ADDING MAIN USER admin ***"
# using the default password 'btcticker'

adduser --disabled-password --gecos "" admin
echo "admin:btcticker" | chpasswd

adduser admin sudo
chsh admin -s /bin/bash

# configure sudo for usage without password entry
echo '%sudo ALL=(ALL) NOPASSWD:ALL' | EDITOR='tee -a' visudo
# check if group "admin" was created
if [ $(cat /etc/group | grep -c "^admin") -lt 1 ]; then
  echo -e "\nMissing group admin - creating it ..."
  /usr/sbin/groupadd --force --gid 1002 admin
  usermod -a -G admin admin
else
  echo -e "\nOK group admin exists"
fi

usermod -a -G gpio admin
usermod -a -G spi admin
usermod -a -G i2c admin


echo -e "\n*** SHELL SCRIPTS AND ASSETS ***"

# copy btc-ticker repo from github
cd /home/admin/
sudo -u admin git config --global user.name "${githubUser}"
sudo -u admin git config --global user.email "johndoe@example.com"
sudo -u admin rm -rf /home/admin/btc-ticker
sudo -u admin git clone -b "${branch}" https://github.com/${github_user}/btc-ticker.git
sudo -u admin cp -r /home/admin/btc-ticker/home.admin/*.* /home/admin
sudo -u admin chmod +x *.sh
sudo -u admin cp -r /home/admin/btc-ticker/home.admin/assets /home/admin/
sudo -u admin cp -r /home/admin/btc-ticker/home.admin/.tmux.conf /home/admin
sudo -u admin cp -r /home/admin/btc-ticker/home.admin/config.scripts /home/admin/
sudo -u admin chmod +x /home/admin/config.scripts/*.sh

cd /home/admin/btc-ticker/
sudo -H python3 setup.py install
cd /home/admin/


rm -rf /home/admin/e-Paper/
sudo -u admin git clone https://github.com/waveshare/e-Paper
cd /home/admin/e-Paper/RaspberryPi_JetsonNano/python
python3 setup.py install
cd /home/admin/

rm -rf /home/admin/Touch_e-Paper_HAT/
sudo -u admin git clone https://github.com/waveshare/Touch_e-Paper_HAT
cd /home/admin/Touch_e-Paper_HAT/python
python3 setup.py install
cd /home/admin/

sudo -H python3 -m pip remove Jetson.GPIO

# add /sbin to path for all
bash -c "echo 'PATH=\$PATH:/sbin' >> /etc/profile"

echo ""
echo "*** BTCTICKER EXTRAS ***"


# optimization for torrent download
bash -c "echo 'net.core.rmem_max = 4194304' >> /etc/sysctl.conf"
bash -c "echo 'net.core.wmem_max = 1048576' >> /etc/sysctl.conf"

bash -c "echo '' >> /home/admin/.bashrc"
bash -c "echo 'NG_CLI_ANALYTICS=ci' >> /home/admin/.bashrc"

homeFile=/home/admin/.bashrc
keyBindings="source /usr/share/doc/fzf/examples/key-bindings.bash"
keyBindingsDone=$(grep -c "$keyBindings" $homeFile)

if [ ${keyBindingsDone} -eq 0 ]; then
  bash -c "echo 'source /usr/share/doc/fzf/examples/key-bindings.bash' >> /home/admin/.bashrc"
  echo "key-bindings added to $homeFile"
else
  echo "key-bindings already in $homeFile"
fi


echo -e "\n*** SWAP FILE ***"
# based on https://github.com/Stadicus/guides/blob/master/raspibolt/raspibolt_20_pi.md#moving-the-swap-file
# but just deactivating and deleting old (will be created alter when user adds HDD)

dphys-swapfile swapoff
dphys-swapfile uninstall

echo -e "\n*** INCREASE OPEN FILE LIMIT ***"
# based on https://github.com/Stadicus/guides/blob/master/raspibolt/raspibolt_20_pi.md#increase-your-open-files-limit

sed --in-place -i "56s/.*/*    soft nofile 128000/" /etc/security/limits.conf
bash -c "echo '*    hard nofile 128000' >> /etc/security/limits.conf"
bash -c "echo 'root soft nofile 128000' >> /etc/security/limits.conf"
bash -c "echo 'root hard nofile 128000' >> /etc/security/limits.conf"
bash -c "echo '# End of file' >> /etc/security/limits.conf"

sed --in-place -i "23s/.*/session required pam_limits.so/" /etc/pam.d/common-session

sed --in-place -i "25s/.*/session required pam_limits.so/" /etc/pam.d/common-session-noninteractive
bash -c "echo '# end of pam-auth-update config' >> /etc/pam.d/common-session-noninteractive"



# *** CACHE DISK IN RAM ***
echo -e "\nActivating CACHE RAM DISK ... "
/home/admin/config.scripts/ticker.cache.sh on

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
    echo "" >> $configFile
    echo "# Raspiblitz" >> $configFile
    echo 'dtoverlay=pi3-disable-bt' | tee -a $configFile
    echo 'dtoverlay=disable-bt' | tee -a $configFile
  else
    echo "disable BT already in $configFile"
  fi

  # remove bluetooth services
  systemctl disable bluetooth.service
  systemctl disable hciuart.service

  # remove bluetooth packages
  apt remove -y --purge pi-bluetooth bluez bluez-firmware
  echo

  # disable audio
  echo "*** DISABLE AUDIO (snd_bcm2835) ***"
  sed -i "s/^dtparam=audio=on/# dtparam=audio=on/g" /boot/config.txt
  echo

  # disable DRM VC4 V3D
  echo "*** DISABLE DRM VC4 V3D driver ***"
  dtoverlay=vc4-fkms-v3d
  sed -i "s/^dtoverlay=vc4-fkms-v3d/# dtoverlay=vc4-fkms-v3d/g" /boot/config.txt
  echo

  #enable i2c
  sed -i "s/^dtparam=i2c_arm=off/dtparam=i2c_arm=on/g" /boot/config.txt
  #enable SPI
   sed -i "s/^dtparam=spi=off/dtparam=spi=on/g" /boot/config.txt
fi

timedatectl set-timezone Europe/Berlin

# *** BOOTSTRAP ***
# see background README for details
echo -e "\n*** RASPI BOOTSTRAP SERVICE ***"
cd /home/admin/
chmod +x /home/admin/_bootstrap.sh
cp /home/admin/assets/bootstrap.service /etc/systemd/system/bootstrap.service
systemctl enable bootstrap

echo -e "\n*** btc-ticker SERVICE ***"
chmod +x /home/admin/run.sh
cp /home/admin/assets/btcticker.service /etc/systemd/system/btcticker.service
systemctl enable btcticker

echo -e "\n*** ro remount SERVICE ***"
cp /home/admin/assets/ro_remount.service /etc/systemd/system/ro_remount.service
systemctl enable ro_remount

# echo "*** check wlan SERVICE ***"
# cp ./assets/check_wifi.service /etc/systemd/system/check_wifi.service
#systemctl enable check_wifi.service

# Enable firewwall
/home/admin/90finishSetup.sh

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
if [ "${display}" != "eink" ] || [ "${baseimage}" = "raspbian" ] || [ "${baseimage}" = "raspios_arm64" ]; then
  echo "*** ADDITIONAL DISPLAY OPTIONS ***"
  echo "- calling: ticker.display.sh set-display ${display}"
  /home/admin/config.scripts/ticker.display.sh set-display ${display}
  #/home/admin/config.scripts/ticker.display.sh rotate 1
fi
