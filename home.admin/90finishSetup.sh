#!/bin/bash
echo ""


####### FIREWALL - just install (not configure)
echo ""
echo "*** Setting and Activating Firewall ***"
sudo apt-get install -y ufw
echo "deny incoming connection on other ports"
sudo ufw default deny incoming
echo "allow outgoing connections"
sudo ufw default allow outgoing
echo "allow: ssh"
sudo ufw allow ssh
echo "allow: public web HTTP"
sudo ufw allow from any to any port 80 comment 'allow public web HTTP'
sudo ufw allow from any to any port 443 comment 'allow public web HTTPS'
echo "allow: local web admin HTTPS"
sudo ufw allow from 10.0.0.0/8 to any port 443 comment 'allow local LAN HTTPS'
sudo ufw allow from 172.16.0.0/12 to any port 443 comment 'allow local LAN HTTPS'
sudo ufw allow from 192.168.0.0/16 to any port 443 comment 'allow local LAN HTTPS'
echo "open firewall for auto nat discover (see issue #129)"
sudo ufw allow proto udp from 10.0.0.0/8 port 1900 to any comment 'allow local LAN SSDP for UPnP discovery'
sudo ufw allow proto udp from 172.16.0.0/12 port 1900 to any comment 'allow local LAN SSDP for UPnP discovery'
sudo ufw allow proto udp from 192.168.0.0/16 port 1900 to any comment 'allow local LAN SSDP for UPnP discovery'
echo "enable lazy firewall"
sudo ufw --force enable
echo ""

# update system
echo ""
echo "*** Update System ***"
sudo apt-mark hold raspberrypi-bootloader
sudo apt-get update -y
echo "OK - System is now up to date"



# Make system readonly
sudo apt-get remove --purge -y logrotate triggerhappy dphys-swapfile
sudo apt-get autoremove --purge -y
sudo apt-get install -y busybox-syslogd
sudo apt-get remove --purge -y rsyslog

sudo apt-get install -y ntp

# Internet is not working until reboot after the following line

sudo rm -rf /var/lib/dhcp/ /var/spool /var/lock /var/lib/dhcpcd5
sudo ln -s /tmp /var/lib/dhcp
sudo ln -s /tmp /var/lib/dhcpcd5
sudo ln -s /tmp /var/spool
sudo ln -s /tmp /var/lock
sudo mv /etc/resolv.conf /tmp/
sudo ln -s /tmp/resolv.conf /etc/resolv.conf

sudo rm /var/lib/systemd/random-seed
sudo ln -s /tmp/random-seed /var/lib/systemd/random-seed

echo "tmpfs         /var/log  tmpfs  nodev,nosuid  0  0
tmpfs         /var/tmp  tmpfs  nodev,nosuid  0  0
tmpfs         /tmp  tmpfs  nodev,nosuid  0  0
" | sudo tee -a /etc/fstab

sudo sed -i /etc/fstab -e "s/\(.*\/boot.*vfat.*\)defaults\(.*\)/\1defaults,ro\2/"
sudo sed -i /etc/fstab -e "s/\(.*\/.*ext4.*\)defaults\(.*\)/\1defaults,ro\2/"

sudo sed -i /boot/cmdline.txt -e "s/\(.*fsck.repair=yes.*\)rootwait\(.*\)/\1rootwait fastboot noswap\2/"

echo 'ExecStartPre=/bin/echo "" >/tmp/random-seed' | sudo tee -a /lib/systemd/system/systemd-random-seed.service

sudo sed -i /etc/cron.hourly/fake-hwclock -e "s/.*fake\-hwclock save/  mount \-o remount,rw \/\n  fake\-hwclock save\n  mount \-o remount,ro \//g"

sudo sed -i  /lib/systemd/system/raspberrypi-net-mods.service -e "s/RemainAfterExit=yes/RemainAfterExit=yes\nExecStart=\/usr\/bin\/mount \-o remount,rw \/\nExecStart=\/usr\/bin\/mount \-o remount,rw \/boot/g"
sudo sed -i  /lib/systemd/system/raspberrypi-net-mods.service -e "s/ExecStartPost=\/usr\/sbin\/rfkill unblock wifi/ExecStartPost=\/usr\/sbin\/rfkill unblock wifi\nExecStartPost=\/usr\/bin\/sync \-f \/boot\nExecStartPost=\/usr\/bin\/sync \-f \/\nExecStartPost=\/usr\/bin\/mount \-o remount,ro \/\nExecStartPost=\/usr\/bin\/mount \-o remount,ro \/boot/g"

echo "
set_bash_prompt(){
" | sudo tee -a /etc/bash.bashrc
echo 'fs_mode=$(mount | sed -n -e "s/^\/dev\/.* on \/ .*(\(r[w|o]\).*/\1/p")
' | sudo tee -a /etc/bash.bashrc
echo "PS1='\[\033[01;32m\]\u@\h\${fs_mode:+(\$fs_mode)}\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\\$ '
}

alias ro='sudo mount -o remount,ro / ; sudo mount -o remount,ro /boot'
alias rw='sudo mount -o remount,rw / ; sudo mount -o remount,rw /boot'

PROMPT_COMMAND=set_bash_prompt
" | sudo tee -a /etc/bash.bashrc

