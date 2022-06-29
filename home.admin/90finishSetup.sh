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

sudo ufw allow nft
#sudo ufw allow 123/udp
#sudo ufw allow out 123/udp
#sudo ufw allow out 53
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
# helpful https://www.dzombak.com/blog/2021/11/Reducing-SD-Card-Wear-on-a-Raspberry-Pi-or-Armbian-Device.html

sudo dphys-swapfile swapoff
sudo dphys-swapfile uninstall
sudo update-rc.d dphys-swapfile remove
sudo apt-get remove --purge -y logrotate triggerhappy dphys-swapfile
sudo apt-get autoremove --purge -y
sudo apt-get install -y busybox-syslogd
sudo apt-get remove --purge -y rsyslog

sudo systemctl disable systemd-timesyncd.service
sudo apt-get install -y ntp

sudo systemctl enable ntp
## Add /etc/ntp.conf
# driftfile /tmp/ntp.drift
# sudo systemctl edit ntp and add
# "[Service]
# PrivateTmp=false
# "



sudo systemctl stop apt-daily.timer
sudo systemctl disable apt-daily.timer
sudo systemctl mask apt-daily.service
sudo systemctl mask apt-daily-upgrade.timer
sudo systemctl mask man-db.timer
sudo systemctl daemon-reload


# Internet is not working until reboot after the following line

sudo rm -rf /var/lock && sudo ln -s /tmp /var/lock
#sudo ln -s /tmp /var/lib/dhcp
#sudo ln -s /tmp /var/lib/dhcpcd5
# sudo ln -s /tmp /var/spool
# sudo ln -s /tmp /var/log/nginx
sudo mv /etc/resolv.conf /var/run/resolv.conf && sudo ln -s /var/run/resolv.conf /etc/resolv.conf

sudo rm -rf /var/lib/dhcp && sudo ln -s /var/run /var/lib/dhcp
sudo rm -rf /var/lib/dhcpcd5 && sudo ln -s /var/run /var/lib/dhcpcd5

#sudo mv /etc/resolv.conf /tmp/
#sudo ln -s /tmp/resolv.conf /etc/resolv.conf

sudo mv /var/lib/systemd/random-seed /tmp/systemd-random-seed && sudo ln -s /tmp/systemd-random-seed /var/lib/systemd/random-seed

echo "tmpfs         /var/log  tmpfs   defaults,noatime,nosuid,nodev,noexec  0  0
tmpfs         /var/tmp  tmpfs  defaults,noatime,nosuid,nodev  0  0
tmpfs         /tmp  tmpfs  defaults,noatime,nosuid,nodev  0  0
tmpfs  /var/spool/mail  tmpfs  defaults,noatime,nosuid,nodev,noexec,size=20M  0  0
tmpfs  /var/spool/rsyslog  tmpfs  defaults,noatime,nosuid,nodev,noexec,size=20M  0  0
tmpfs  /var/lib/logrotate  tmpfs  defaults,noatime,nosuid,nodev,noexec,size=1m,mode=0755  0  0
tmpfs  /var/lib/sudo  tmpfs  defaults,noatime,nosuid,nodev,noexec,size=1m,mode=0700  0  0
" | sudo tee -a /etc/fstab

#sudo sed -i /etc/fstab -e "s/\(.*\/boot.*vfat.*\)defaults\(.*\)/\1defaults,ro\2/"
#sudo sed -i /etc/fstab -e "s/\(.*\/.*ext4.*\)defaults\(.*\)/\1defaults,ro\2/"

sudo sed -i /boot/cmdline.txt -e "s/\(.*fsck.repair=yes.*\)rootwait\(.*\)/\1rootwait fsck.mode=skip noswap\2/"

echo 'ExecStartPre=/bin/echo "" >/tmp/random-seed' | sudo tee -a /lib/systemd/system/systemd-random-seed.service

sudo sed -i /etc/cron.hourly/fake-hwclock -e "s/.*fake\-hwclock save/  mount \-o remount,rw \/\n  fake\-hwclock save\n  mount \-o remount,ro \//g"

#sudo sed -i  /lib/systemd/system/raspberrypi-net-mods.service -e "s/RemainAfterExit=yes/RemainAfterExit=yes\nExecStart=\/usr\/bin\/mount \-o remount,rw \/\nExecStart=\/usr\/bin\/mount \-o remount,rw \/boot/g"
#sudo sed -i  /lib/systemd/system/raspberrypi-net-mods.service -e "s/ExecStartPost=\/usr\/sbin\/rfkill unblock wifi/ExecStartPost=\/usr\/sbin\/rfkill unblock wifi\nExecStartPost=\/usr\/bin\/sync \-f \/boot\nExecStartPost=\/usr\/bin\/sync \-f \/\nExecStartPost=\/usr\/bin\/mount \-o remount,ro \/\nExecStartPost=\/usr\/bin\/mount \-o remount,ro \/boot/g"

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

echo "sudo mount -o remount,ro / ; sudo mount -o remount,ro /boot
" | sudo tee -a /etc/bash.bash_logout