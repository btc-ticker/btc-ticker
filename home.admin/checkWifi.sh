#!/bin/bash

# keep wifi alive

ping -c2 google.de > /dev/null


if [ $? != 0 ]
then
  echo " "
  echo "No network connection, restarting wlan0"
  sudo ifconfig wlan0 down
  sleep 30
  sudo ifconfig wlan0 up
else
    echo " "
fi