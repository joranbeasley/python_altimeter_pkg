sudo apt-get update
sudo apt-get install git
cd /home/pi
git clone https://github.com/joranbeasley/python_altimeter_pkg.git
cd python_altimeter_pkg/install_scripts
sed -i "s/time sudo apt-get git/time sudo apt-get git/" install_xorg.sh
sudo bash install_xorg.sh
