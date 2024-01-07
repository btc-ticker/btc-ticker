# Taken from https://github.com/rootzoll/raspiblitz/blob/v1.7/home.admin/99updateMenu.sh
#!/bin/bash

# load btc-ticker config data
source /home/admin/btc-ticker.info
source /home/admin/_version.info

## PROCEDURES

release()
{
  whiptail --title "Update Instructions" --yes-button "Not Now" --no-button "Start Update" --yesno "To update your btc-ticker to a new version:

- Download the new SD card image to your laptop:
  https://github.com/btc-ticker/btc-ticker
- Flash that SD card image to a new SD card (best)
  or override old SD card after shutdown (fallback)
- Choose 'Start Update' below.

No need to close channels or download blockchain again.
Do you want to start the Update now?
      " 16 62
  if [ $? -eq 0 ]; then
    exit 1
  fi


  whiptail --title "READY TO UPDATE?" --yes-button "START UPDATE" --no-button "Cancel" --yesno "If you start the update: The btc-ticker will power down.
Once the LCD is white and no LEDs are blicking anymore:

- Remove the Power from btc-ticker
- Exchange the old with the new SD card
- Connect Power back to the btc-ticker

Do you have the SD card with the new version image ready
and do you WANT TO START UPDATE NOW?
      " 16 62

  if [ $? -eq 1 ]; then
    dialog --title " Update Canceled " --msgbox "
OK. btc-ticker will NOT update now.
      " 7 39
    exit 1
  fi

  clear
  sudo shutdown now
}

patchNotice()
{
  whiptail --title "Patching Notice" --yes-button "Dont Patch" --no-button "Patch Menu" --yesno "This is the possibility to patch your btc-ticker:
It means it will sync the program code with the
GitHub repo for your version branch v${codeVersion}.

This can be useful if there are important updates
in between releases to fix severe bugs. It can also
be used to sync your own code with your btc-ticker
if you are developing on your own GitHub Repo.

BUT BEWARE: This means btc-ticker will contact GitHub,
hotfix the code and might compromise your security.

Do you want to Patch your btc-ticker now?
      " 18 58
  if [ $? -eq 0 ]; then
    exit 1
  fi
}

patch()
{

  # get sync info
  source <(sudo /home/admin/XXsyncScripts.sh info)

  # Patch Options
  OPTIONS=(PATCH "Patch/Sync btc-ticker with GitHub Repo" \
           REPO "Change GitHub Repo to sync with" \
           BRANCH "Change GitHub Branch to sync with" \
           PR "Checkout a PullRequest to test"
        )

  CHOICE=$(whiptail --clear --title "GitHub-User: ${activeGitHubUser} Branch: ${activeBranch}" --menu "" 11 55 4 "${OPTIONS[@]}" 2>&1 >/dev/tty)

  clear
  case $CHOICE in
    PATCH)
      sudo -u admin /home/admin/XXsyncScripts.sh -run
      sleep 4
      whiptail --title " Patching/Syncing " --yes-button "Reboot" --no-button "Skip Reboot" --yesno "  OK patching/syncing done.

  By default a reboot is advised.
  Only skip reboot if you know
  it will work without restart.
      " 11 40
      if [ $? -eq 0 ]; then
        clear
        echo "REBOOT .."
        sudo reboot
        sleep 8
      else
        echo "SKIP REBOOT .."
      fi
      exit 1
      ;;
    REPO)
      clear
      echo "..."
      newGitHubUser=$(whiptail --inputbox "\nPlease enter the GitHub USERNAME of the forked btc-ticker Repo?" 10 38 ${activeGitHubUser} --title "Change Sync Repo" 3>&1 1>&2 2>&3)
      exitstatus=$?
      if [ $exitstatus = 0 ]; then
        newGitHubUser=$(echo "${newGitHubUser}" | cut -d " " -f1)
        echo "--> " ${newGitHubUser}
        error=""
        source <(sudo -u admin /home/admin/XXsyncScripts.sh -clean ${activeBranch} ${newGitHubUser})
        if [ ${#error} -gt 0 ]; then
          whiptail --title "ERROR" --msgbox "${error}" 8 30
        fi
      fi
      patch
      exit 1
      ;;
    BRANCH)
      clear
      echo "..."
      newGitHubBranch=$(whiptail --inputbox "\nPlease enter the GitHub BRANCH of the btc-ticker Repo '${activeGitHubUser}'?" 10 38 ${activeBranch} --title "Change Sync Branch" 3>&1 1>&2 2>&3)
      exitstatus=$?
      if [ $exitstatus = 0 ]; then
        newGitHubBranch=$(echo "${newGitHubBranch}" | cut -d " " -f1)
        echo "--> " $newGitHubBranch
        error=""
        source <(sudo -u admin /home/admin/XXsyncScripts.sh ${newGitHubBranch})
        if [ ${#error} -gt 0 ]; then
          whiptail --title "ERROR" --msgbox "${error}" 8 30
        fi
      fi
      patch
      exit 1
      ;;
    PR)
      clear
      echo "..."
      pullRequestID=$(whiptail --inputbox "\nPlease enter the NUMBER of the PullRequest on btc-ticker Repo '${activeGitHubUser}'?" 10 46 --title "Checkout PullRequest ID" 3>&1 1>&2 2>&3)
      exitstatus=$?
      if [ $exitstatus = 0 ]; then
        pullRequestID=$(echo "${pullRequestID}" | cut -d " " -f1)
        echo "# --> " $pullRequestID
        cd /home/admin/btc-ticker
        git fetch origin pull/${pullRequestID}/head:pr${pullRequestID}
        error=""
        source <(sudo -u admin /home/admin/XXsyncScripts.sh pr${pullRequestID})
        if [ ${#error} -gt 0 ]; then
          whiptail --title "ERROR" --msgbox "${error}" 8 30
        else
          echo "# update installs .."
          /home/admin/XXsyncScripts.sh -justinstall
        fi
      fi
      exit 1
      ;;
  esac
}


# quick call by parameter
if [ "$1" == "github" ]; then
  patch
  exit 0
fi

# Basic Options Menu
HEIGHT=10 # add 6 to CHOICE_HEIGHT + MENU lines
WIDTH=55
CHOICE_HEIGHT=4 # 1 line / OPTIONS
OPTIONS=(
RELEASE "btc-ticker Release Update/Recovery"
PATCH "Patch btc-ticker v${codeVersion}"
)


CHOICE=$(dialog --clear \
                --backtitle "" \
                --title "Update Options" \
                --ok-label "Select" \
                --cancel-label "Main menu" \
                --menu "" \
          $HEIGHT $WIDTH $CHOICE_HEIGHT \
          "${OPTIONS[@]}" 2>&1 >/dev/tty)

case $CHOICE in
  RELEASE)
    release
    ;;
  PATCH)
    patchNotice
    patch
    ;;
esac
