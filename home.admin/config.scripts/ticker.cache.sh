#!/usr/bin/env bash
# # This script has been modified from https://raw.githubusercontent.com/rootzoll/raspiblitz/v1.7/
# command info
if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ] || [ "$1" = "-help" ]; then
  echo "btcticker Cache RAM disk"
  echo "ticker.cache.sh [on|off]"
  exit 1
fi

###################
# SWITCH ON
###################
if [ "$1" = "1" ] || [ "$1" = "on" ]; then

  echo "Turn ON: Cache"

  if ! grep -Eq '^tmpfs.*/var/cache/btcticker' /etc/fstab; then

    if grep -Eq '/var/cache/btcticker' /etc/fstab; then
      # entry is in file but most likely just disabled -> re-enable it
      sudo sed -i -E 's|^#(tmpfs.*/var/cache/btcticker.*)$|\1|g' /etc/fstab
    else
      # missing -> add
      echo "" | sudo tee -a /etc/fstab >/dev/null
      echo "tmpfs         /var/cache/btcticker  tmpfs  nodev,nosuid,size=32M  0  0" | sudo tee -a /etc/fstab >/dev/null
    fi
  fi

  if ! findmnt -l /var/cache/btcticker >/dev/null; then
    sudo mkdir -p /var/cache/btcticker
    sudo mount /var/cache/btcticker
  fi

###################
# SWITCH OFF
###################
elif [ "$1" = "0" ] || [ "$1" = "off" ]; then

  echo "Turn OFF: Cache"

  if grep -Eq '/var/cache/btcticker' /etc/fstab; then
    sudo sed -i -E 's|^(tmpfs.*/var/cache/btcticker.*)$|#\1|g' /etc/fstab
  fi

  if findmnt -l /var/cache/btcticker >/dev/null; then
    sudo umount /var/cache/btcticker
  fi

else

  echo "# FAIL: parameter not known - run with -h for help"
fi
