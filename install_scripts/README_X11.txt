this package install x11 using the following commands

```bash
sudo apt-get -y install --no-install-recommends xserver-xorg
sudo apt-get -y install --no-install-recommends xinit
sudo apt-get -y install --no-install-recommends x11-xserver-utils
```
then to trigger our desktop environment we add the following to the bottom of our ~/.bashrc file

```bash
if [[ $(tty) = /dev/tty1 ]]; then # check if this is the "main screen"
    echo "STARTING ALTIMETER UI"
    exec xinit # fork shell to our ui
fi
```

but before we can use the software we need to setup ~/.xinitrc which lets the system know what software to run
we will create .xinitrc with the following content (`apt install feh before this step if you want the splash screen`)
```bash
# show spash screen
/usr/bin/feh --bg-tile  /home/pi/python_altimeter_pkg/src/gui/resources/spash2.gif
cd /home/pi
bash start-altimeter-gui.sh
# if our software crashes it will reboot
# you can find the logfiles in /logfiles
```

we also need to tell it how to start the X-server by creating ~/.xserverrc

```bash
#!/bin/sh
echo "START XSERVER!"
exec sudo /usr/lib/xorg/Xorg :0 -seat seat0 -nolisten tcp vt7 -novtswitch -s 0 dpms
```


finally we run the adafruit-pitft-setup.sh script to install the screen software

