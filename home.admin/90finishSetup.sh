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
sudo apt-get remove --purge -y cron logrotate triggerhappy dphys-swapfile samba-common
sudo apt-get autoremove --purge -y

sudo rm -rf /var/lib/dhcp/ /var/spool /var/lock
sudo ln -s /tmp /var/lib/dhcp
sudo ln -s /tmp /var/spool
sudo ln -s /tmp /var/lock
sudo mv /etc/resolv.conf /tmp/
sudo ln -s /tmp/resolv.conf /etc/resolv.conf


if ! grep -Eq '^tmpfs.*/var/log' /etc/fstab; then

  if grep -Eq '/var/log' /etc/fstab; then
    # entry is in file but most likely just disabled -> re-enable it
    sudo sed -i -E 's|^#(tmpfs.*/var/log.*)$|\1|g' /etc/fstab
  else
    # missing -> add
    echo "" | sudo tee -a /etc/fstab >/dev/null
    echo "tmpfs         /var/log  tmpfs  nodev,nosuid  0  0" | sudo tee -a /etc/fstab >/dev/null
  fi
fi

if ! grep -Eq '^tmpfs.*/var/tmp' /etc/fstab; then

  if grep -Eq '/var/tmp' /etc/fstab; then
    # entry is in file but most likely just disabled -> re-enable it
    sudo sed -i -E 's|^#(tmpfs.*/var/tmp.*)$|\1|g' /etc/fstab
  else
    # missing -> add
    echo "" | sudo tee -a /etc/fstab >/dev/null
    echo "tmpfs         /var/tmp  tmpfs  nodev,nosuid  0  0" | sudo tee -a /etc/fstab >/dev/null
  fi
fi

if ! grep -Eq '^tmpfs.*/tmp' /etc/fstab; then

  if grep -Eq '/tmp' /etc/fstab; then
    # entry is in file but most likely just disabled -> re-enable it
    sudo sed -i -E 's|^#(tmpfs.*/tmp.*)$|\1|g' /etc/fstab
  else
    # missing -> add
    echo "" | sudo tee -a /etc/fstab >/dev/null
    echo "tmpfs         /tmp  tmpfs  nodev,nosuid  0  0" | sudo tee -a /etc/fstab >/dev/null
  fi
fi


sudo sed -i /etc/fstab -e "s/\(.*\/boot.*vfat.*\)defaults\(.*\)/\1defaults,ro\2/"
sudo sed -i /etc/fstab -e "s/\(.*\/.*ext4.*\)defaults\(.*\)/\1defaults,ro\2/"

sudo sed -i /boot/cmdline.txt -e "s/\(.*fsck.repair=yes.*\)rootwait\(.*\)/\1rootwait fastboot noswap\2/"

echo "set_bash_prompt(){" | sudo tee -a /etc/bash.bashrc >/dev/null
echo "fs_mode=$(mount | sed -n -e "s/^\/dev\/.* on \/ .*(\(r[w|o]\).*/\1/p")" | sudo tee -a /etc/bash.bashrc >/dev/null
echo "PS1='\[\033[01;32m\]\u@\h${fs_mode:+($fs_mode)}\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '" | sudo tee -a /etc/bash.bashrc >/dev/null
echo "}" | sudo tee -a /etc/bash.bashrc >/dev/null
echo "" | sudo tee -a /etc/bash.bashrc >/dev/null
echo "alias ro='sudo mount -o remount,ro / ; sudo mount -o remount,ro /boot'" | sudo tee -a /etc/bash.bashrc >/dev/null
echo "alias rw='sudo mount -o remount,rw / ; sudo mount -o remount,rw /boot'" | sudo tee -a /etc/bash.bashrc >/dev/null
echo "" | sudo tee -a /etc/bash.bashrc >/dev/null
echo "PROMPT_COMMAND=set_bash_prompt" | sudo tee -a /etc/bash.bashrc >/dev/null

# mark setup is done
sudo sed -i "s/^setupStep=.*/setupStep=100/g" /home/admin/btc-ticker.info