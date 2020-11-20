# EASY INSTALLATION
run the following command
```bash
curl https://raw.githubusercontent.com/joranbeasley/python_altimeter_pkg/master/install_scripts/wget_installer.sh | sudo sh
```
this will automate all of the below steps making your life much easier!!

# Install It The Hard way

***before begining** ensure you have cloned this repo into*
 `/home/pi/python_altimeter_pkg`
 
 ```bash
cd /home/pi
git clone https://github.com/joranbeasley/python_altimeter_pkg.git
cd python_altimeter_pkg/install_scripts 
```
this package install x11 using the following commands

```bash
sudo apt-get -y install --no-install-recommends xserver-xorg
sudo apt-get -y install --no-install-recommends xinit
sudo apt-get -y install --no-install-recommends x11-xserver-utils
```
then unfortunately we must also install `lightdm` or i could not get the touch coordinates to work correctly

```bash
sudo apt-get -y install lightdm
```

we need to install a bunch more packages

```bash
sudo apt-get -y install python-setuptools python-pip  redis-server
sudo apt-get -y install python-matplotlib python-tk feh
```
once all that is installed we need to install some pip packages

```bash
pip install pyserial
pip install redis
```

We then need to configure a couple of directories

```bash
sudo mkdir /logfiles # where logfiles are stored
sudo chmod 777 /logfiles
sudo mkdir /mnt/USB # mountpoint for usb
```

make sure that the code is installed at /home/pi/python_altimeter_pkg !!!!!

copy over the executables and set their permissions

```bash
sudo cp -rf /home/pi/python_altimeter_pkg/install_scripts/SYSTEM/home/pi/start-altimeter-gui SYSTEM/home/pi/start-serial-monitor /home/pi/
sudo chmod +x /home/pi/start-altimeter-gui
sudo chmod +x /home/pi/start-serial-monitor
sudo chown pi:pi /home/pi/start-altimeter-gui
sudo chown pi:pi /home/pi/start-serial-monitor
sudo chmod 777 /home/pi/start-serial-monitor
sudo chmod 777 /home/pi/start-altimeter-gui
```

copy over the .xsession file that is needed to start our xenvironment

```bash
sudo cp -rf SYSTEM/home/pi/.xsession /home/pi/
sudo chown pi:pi /home/pi/.xsession
```

copy over our startup services and enable them (do not enable altimeter, that is manually called)
```bash
sudo cp -rf /home/pi/python_altimeter_pkg/install_scripts/SYSTEM/etc/systemd/* /etc/systemd/
sudo systemctl enable ser-mon
sudo systemctl enable fbsplash0
sudo systemctl enable fbsplash1
sudo systemctl daemon-reload
```

copy over our udev rules to mount our devices and provide known names

```bash
sudo cp -rf /home/pi/python_altimeter_pkg/install_scripts/SYSTEM/etc/udev/* /etc/udev/
```

add our fstab rules to mount our usb at /mnt/USB

```bash
cat /home/pi/python_altimeter_pkg/install_scripts/SYSTEM/etc/fstab |sudo tee -a /etc/fstab
```

setup the proper resolution 320x240 

```bash
sudo sed -i "s/#* *framebuffer_width=.*/framebuffer_width=320/g" /boot/config.txt
sudo sed -i "s/#* *framebuffer_height=.*/framebuffer_height=240/g" /boot/config.txt
```

finally we run the adafruit-pitft-setup.sh script to install the screen software
and replace the autologin user BEFORE reboot (it will default to root instead of pi)

```bash
sudo sed -i "s/autologin-user=root/autologin-user=pi/" /etc/lightdm/lightdm.conf
sudo reboot # once we reboot everything will be up and running
```

