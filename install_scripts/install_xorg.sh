# install x-server
if git -v; then
  echo "GIT ALREADY INSTALLED!"
else
  time sudo apt-get -y install git
fi
time sudo apt-get -y install --no-install-recommends xserver-xorg
time sudo apt-get -y install --no-install-recommends xinit
time sudo apt-get -y install python-setuptools python-pip python-tk redis-server
time sudo apt-get -y install --no-install-recommends x11-xserver-utils

time sudo apt-get -y install python-matplotlib
time sudo pip install redis
#wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/adafruit-pitft.sh


sudo ./configure_sys.sh

echo "INSTALL PITFT ... then restart"
#install touch drivers this will cause a reboot
# sudo /bin/bash adafruit-pitft-setup.sh -c1 -r1 -m2
