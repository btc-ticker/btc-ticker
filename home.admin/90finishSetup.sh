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

# mark setup is done
sudo sed -i "s/^setupStep=.*/setupStep=100/g" /home/admin/btc-ticker.info
