echo -e "\n\nSETTING RESOLUTION 320x240"
#force resolution
sudo cp /boot/config.txt /boot/config_txt.bak
sudo sed -i "s/#* *framebuffer_width=.*/framebuffer_width=320/g" /boot/config.txt
sudo sed -i "s/#* *framebuffer_height=.*/framebuffer_height=240/g" /boot/config.txt

# set x-server startup command included extra `-s 0 dpms` from default in order to disable sleep
# echo "DISABLE SLEEP"
# sudo sed -i "s/#xserver-command=/usr/lib/xorg/Xorg :0 -seat seat0 -auth /var/run/lightdm/root/:0 -nolisten tcp vt7 -novtswitch -s 0 dpms"

## INSTALL PACKAGE FILES
echo -e "\n\nINSTALLING PACKAGE FILES"
if grep -q "# added for python_altimeter_pkg" /etc/fstab; then
   echo "already added first delete it"
   sudo sed -i -e "/# added for python_altimeter_pkg/,/#end section for python_altimeter_pkg/d" /etc/fstab
fi
echo "setup fstab"
cat SYSTEM/etc/fstab |sudo tee -a /etc/fstab
echo "copy udev rules"
sudo cp -rf SYSTEM/etc/udev/* /etc/udev/
echo "copy systemd services"
sudo cp -rf SYSTEM/etc/systemd/* /etc/systemd/

echo "copy .xinitrc and .xserverrc"
ls SYSTEM/home/pi -la
sudo cp -rf SYSTEM/home/pi/.xinitrc SYSTEM/home/pi/.xserverrc /home/pi/
sudo cp -rf SYSTEM/home/pi/start-altimeter-gui.sh SYSTEM/home/pi/start-serial-monitor.sh /home/pi/
sudo chmod +x /home/pi/start-altimeter-gui.sh
sudo chmod +x /home/pi/start-serial-monitor.sh
sudo cp -rf SYSTEM/home/pi/.tmux.conf  /home/pi/
sudo chmod 777 /home/pi/start-serial-monitor.sh
sudo chmod 777 /home/pi/start-altimeter-gui.sh
echo "fix bashrc"
  if grep -q "# added for python_altimeter_pkg" /home/pi/.bashrc; then
   echo "already added first delete it from bash rc"
   sed -i -e "/# added for python_altimeter_pkg/,/#end section for python_altimeter_pkg/d" /home/pi/.bashrc
fi

cat SYSTEM/home/pi/.bashrc >> /home/pi/.bashrc

echo "INSTALL pyserial"
sudo pip install pyserial
# /usr/lib/xorg/Xorg :0 -seat seat0 -auth /var/run/lightdm/root/:0 -nolisten tcp vt7 -novtswitch -s 0 dpms
#create logfile folder
echo "CREATE Logfiles Directory"
sudo mkdir /logfiles
sudo chmod 777 /logfiles
