# install x-server
if git --version; then
  echo "GIT ALREADY INSTALLED!"
else
  time sudo apt-get -y install git
fi
function info() {
    system="$1"
    group="${system}"
    shift
    FG="1;32m"
    BG="40m"
    echo -e "[\033[${FG}\033[${BG}${system}\033[0m] $*"
}

time sudo apt-get -y install --no-install-recommends xserver-xorg
info SUCCESS "INSTALLED xserver-xorg"
time sudo apt-get -y install --no-install-recommends xinit
info SUCCESS "INSTALLED xinit"
time sudo apt-get -y install python-setuptools python-pip  redis-server
info SUCCESS "INSTALLED python libraries"
time sudo apt-get -y install --no-install-recommends x11-xserver-utils
info SUCCESS "installed x11-server-utils"
time sudo apt-get -y install python-matplotlib python-tk feh
info SUCCESS "installed matplotlib, and tk"

time sudo pip install redis
info SUCCESS "INSTALLed redis"
sudo pip install pyserial
info SUCCESS "installed pyserial"

#wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/adafruit-pitft.sh


time sudo /bin/bash configure_sys.sh
info SUCCESS "SYSTEM CONGIFURED installing PITFT ... then restart"
#install touch drivers this will cause a reboot
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/adafruit-pitft.sh
chmod +x adafruit-pitft.sh
time sudo apt-get -y install lightdm
info SUCCESS "installed lightdm" #loginmanager
sudo ./adafruit-pitft.sh
