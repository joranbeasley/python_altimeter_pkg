/usr/bin/feh --bg-tile  /home/pi/python_altimeter_pkg/src/gui/resources/splash2.gif
sudo systemctl start altimeter
while true
do
   tail -f /dev/null & wait
done
