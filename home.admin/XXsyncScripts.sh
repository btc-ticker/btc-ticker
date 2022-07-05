#!/bin/bash

# taken from https://raw.githubusercontent.com/rootzoll/raspiblitz/v1.7/home.admin/XXsyncScripts.sh

# command info
if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ] || [ "$1" = "-help" ]; then
  echo "FOR DEVELOPMENT USE ONLY!"
  echo "btc-ticker Sync Scripts"
  echo "XXsyncScripts.sh info"
  echo "XXsyncScripts.sh [-run|-clean|-install|-justinstall] branch [repo]"
  exit 1
fi

cd /home/admin/btc-ticker
# gather info
activeGitHubUser=$(sudo -u admin cat /home/admin/btc-ticker/.git/config 2>/dev/null | grep "url = " | cut -d "=" -f2 | cut -d "/" -f4)
activeBranch=$(git branch 2>/dev/null | grep \* | cut -d ' ' -f2)

# if parameter is "info" just give back basic info about sync
if [ "$1" == "info" ]; then
  echo "activeGitHubUser='${activeGitHubUser}'"
  echo "activeBranch='${activeBranch}'"
  exit 1
fi

# change branch if set as parameter
vagrant=0
clean=0
install=0
wantedBranch="$1"
wantedGitHubUser="$2"
if [ "${wantedBranch}" = "-run" ]; then
  # "-run" ist just used by "patch" command and will ignore all further parameter
  wantedBranch="${activeBranch}"
  wantedGitHubUser="${activeGitHubUser}"
  # detect if running in vagrant VM
  vagrant=$(df | grep -c "/vagrant")
  if [ "$2" = "git" ]; then
    echo "# forcing guthub over vagrant sync"
    vagrant=0
  fi
fi
if [ "${wantedBranch}" = "-clean" ]; then
  clean=1
  wantedBranch="$2"
  wantedGitHubUser="$3"
fi
if [ "${wantedBranch}" = "-install" ]; then
  install=1
  wantedBranch="$2"
  wantedGitHubUser="$3"
fi
if [ "${wantedBranch}" = "-justinstall" ]; then
  clean=1
  install=1
  wantedBranch=""
  wantedGitHubUser=""
fi

# set to another GutHub repo as origin
if [ ${#wantedGitHubUser} -gt 0 ] && [ ${vagrant} -eq 0 ]; then
  echo "# your active GitHubUser is: ${activeGitHubUser}"
  echo "# your wanted GitHubUser is: ${wantedGitHubUser}"
  if [ "${activeGitHubUser}" = "${wantedGitHubUser}" ]; then
    echo "# OK"
  else

    echo "# checking repo exists .."
    repoExists=$(curl -s https://api.github.com/repos/${wantedGitHubUser}/btc-ticker | jq -r '.name' | grep -c 'btc-ticker')
    if [ ${repoExists} -eq 0 ]; then
      echo "error='repo not found'"
      exit 1
    fi

    echo "# try changing github origin .."
    git remote set-url origin https://github.com/${wantedGitHubUser}/btc-ticker.git
    activeGitHubUser=$(sudo -u admin cat /home/admin/btc-ticker/.git/config | grep "url = " | cut -d "=" -f2 | cut -d "/" -f4)
  fi
fi

if [ ${#wantedBranch} -gt 0 ] && [ ${vagrant} -eq 0 ]; then
  echo "# your active branch is: ${activeBranch}"
  echo "# your wanted branch is: ${wantedBranch}"
  if [ "${wantedBranch}" = "${activeBranch}" ]; then
    echo "# OK"
  else

    # always clean & install fresh on branch change
    clean=1
    install=1

    echo "# checking if branch is locally available"
    localBranch=$(git branch | grep -c "${wantedBranch}")
    if [ ${localBranch} -eq 0 ]; then
      echo "# checking branch exists .."
      branchExists=$(curl -s https://api.github.com/repos/${activeGitHubUser}/btc-ticker/branches/${wantedBranch} | jq -r '.name' | grep -c ${wantedBranch})
      if [ ${branchExists} -eq 0 ]; then
        echo "error='branch not found'"
        exit 1
      fi
      echo "# checkout/changing branch .."
      git fetch
      git checkout -b ${wantedBranch} origin/${wantedBranch}
    else
      echo "# changing branch .."
      git checkout ${wantedBranch}
    fi

    activeBranch=$(git branch | grep \* | cut -d ' ' -f2)
  fi
fi

if [ ${vagrant} -eq 0 ]; then
  origin=$(git remote -v | grep 'origin' | tail -n1)
  echo "# *** SYNCING btc-ticker CODE WITH GITHUB ***"
  echo "# This is for developing on your btc-ticker."
  echo "# THIS IS NOT THE REGULAR UPDATE MECHANISM"
  echo "# and can lead to dirty state of your scripts."
  echo "# REPO ----> ${origin}"
  echo "# BRANCH --> ${activeBranch}"
  echo "# ******************************************"
  git pull 1>&2
  cd ..
else
  cd ..
  echo "# --> VAGRANT IS ACTIVE"
  echo "# *** SYNCING btc-ticker CODE WITH VAGRANT LINKED DIRECTORY ***"
  echo "# This is for developing on your btc-ticker with a VM."
  echo "# - delete /home/admin/btc-ticker"
  sudo rm -r /home/admin/btc-ticker
  sudo mkdir /home/admin/btc-ticker
  echo "# - copy from vagrant new btc-ticker files (ignore hidden dirs)"
  sudo cp -r /vagrant/* /home/admin/btc-ticker
  echo "# - set admin as owner of files"
  sudo chown admin:admin -R /home/admin/btc-ticker
fi

if [ ${clean} -eq 1 ]; then
  echo "# Cleaning assets .. "
  sudo rm -f *.sh
  sudo rm -rf assets
  sudo -u admin mkdir assets
else
  echo "# ******************************************"
  echo "# NOT cleaning/deleting old files"
  echo "# use parameter '-clean' if you want that next time"
  echo "# ******************************************"
fi

echo "# Backup config.ini"
sudo -u admin cp -f /home/admin/config.ini /home/admin/config.ini.backup

echo "# COPYING from GIT-Directory to /home/admin/"
sudo rm -r /home/admin/config.scripts
sudo -u admin cp -r -f /home/admin/btc-ticker/home.admin/*.* /home/admin
sudo -u admin cp -r -f /home/admin/btc-ticker/home.admin/assets /home/admin
sudo -u admin chmod +x /home/admin/*.sh
sudo -u admin chmod +x /home/admin/*.py
sudo -u admin chmod +x /home/admin/config.scripts/*.sh
sudo -u admin chmod +x /home/admin/config.scripts/*.py
echo "# ******************************************"

sudo -u admin cp -f /home/admin/config.ini /home/admin/config.ini.new
sudo -u admin cp -f /home/admin/config.ini.backup /home/admin/config.ini

cd /home/admin/btc-ticker/
sudo -H python3 setup.py install

echo "# ******************************************"
echo "# OK - shell scripts and assets are synced"
echo "# Will restart btc-ticker now"
echo "# If it does not work, please reboot"
sudo -H systemctl restart btcticker
