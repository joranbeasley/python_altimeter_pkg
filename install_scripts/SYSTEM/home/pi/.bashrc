# added for python_altimeter_pkg
if [[ $(tty) = /dev/tty1 ]]; then
    echo "STARTING ALTIMETER UI"
    exec xinit
    # exec sudo xinit;
fi
# end section for python_altimeter_pkg
