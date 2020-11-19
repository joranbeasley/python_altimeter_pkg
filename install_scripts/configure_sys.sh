function info() {
    system="$1"
    group="${system}"
    shift
    FG="1;34m"
    BG="40m"
    echo -e "[\033[${FG}\033[${BG}${system}\033[0m] $*"
}
info CONFIG "SETTING RESOLUTION 320x240"
#force resolution
sudo cp /boot/config.txt /boot/config_txt.bak
sudo sed -i "s/#* *framebuffer_width=.*/framebuffer_width=320/g" /boot/config.txt
sudo sed -i "s/#* *framebuffer_height=.*/framebuffer_height=240/g" /boot/config.txt

# set x-server startup command included extra `-s 0 dpms` from default in order to disable sleep
# echo "DISABLE SLEEP"
# sudo sed -i "s/#xserver-command=/usr/lib/xorg/Xorg :0 -seat seat0 -auth /var/run/lightdm/root/:0 -nolisten tcp vt7 -novtswitch -s 0 dpms"

## INSTALL PACKAGE FILES
info CONFIG "INSTALLING PACKAGE FILES"
if grep -q "# added for python_altimeter_pkg" /etc/fstab; then
   info CONFIG "already added first delete it"
   sudo sed -i -e "/# added for python_altimeter_pkg/,/#end section for python_altimeter_pkg/d" /etc/fstab
fi
info CONFIG "setup fstab"
cat SYSTEM/etc/fstab |sudo tee -a /etc/fstab
cat /etc/fstab
info CONFIG "copy udev rules"
sudo cp -rf SYSTEM/etc/udev/* /etc/udev/
info CONFIG "copy systemd services"
sudo cp -rf SYSTEM/etc/systemd/* /etc/systemd/
sudo systemctl enable ser-mon
sudo systemctl enable fbsplash0
sudo systemctl enable fbsplash1

info CONFIG "copy .xsession"
sudo cp -rf SYSTEM/home/pi/.xinitrc SYSTEM/home/pi/.xsession /home/pi/
info CONFIG "copy start-altimeter-gui and start-serial-monitor executables"
sudo cp -rf SYSTEM/home/pi/start-altimeter-gui SYSTEM/home/pi/start-serial-monitor /home/pi/
sudo chmod +x /home/pi/start-altimeter-gui
sudo chmod +x /home/pi/start-serial-monitor
sudo chmod 777 /home/pi/start-serial-monitor
sudo chmod 777 /home/pi/start-altimeter-gui

sudo cp -rf SYSTEM/home/pi/.tmux.conf  /home/pi/


#info CONFIG "fix bashrc"
#if grep -q "# added for python_altimeter_pkg" /home/pi/.bashrc; then
#   info CONFIG "already added first delete it from bash rc"
#   sed -i -e "/# added for python_altimeter_pkg/,/#end section for python_altimeter_pkg/d" /home/pi/.bashrc
#fi
#
#cat SYSTEM/home/pi/.bashrc >> /home/pi/.bashrc


# /usr/lib/xorg/Xorg :0 -seat seat0 -auth /var/run/lightdm/root/:0 -nolisten tcp vt7 -novtswitch -s 0 dpms
#create logfile folder
info CONFIG "CREATE Logfiles Directory"
sudo mkdir /logfiles
sudo chmod 777 /logfiles
