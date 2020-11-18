# added for python_altimeter_package
if [[ $(tty) = /dev/tty1 ]]; then
    echo "STARTING ALTIMETER UI"
    exec xinit
    # exec sudo xinit;
else
    echo "NO UI START!"
fi
# end section for python_altimeter_package
