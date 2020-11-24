STARTDIR=`pwd`
PACKAGENAME=python_altimeter_pkg
#REPONAME=python_altimeter_pkg
#REVISION=1
#REVISION=`svn info svn+ssh://subversion@10.10.1.42/usr/source_control/svn/repos/$REPONAME/ |  awk '/Revision:/ { print $2 }'`
#REVISION=1861
VERSION=1.0
#VERSION=`cd src/scriboxapp/;python -c "import version;print version.version"`
ARCHITECTURE=all
PACKAGEDIR=${PACKAGENAME}_${VERSION}_${ARCHITECTURE}
echo "Building package $PACKAGENAME..."
#echo "version='$VERSION'" > src/scriboxapp/version.py

# Compile version of CSS files from LESS files
# Plantpoint
# Theme
# Grodan
# Theme

TARGET=/tmp/$PACKAGEDIR/BUILD
mkdir -p $TARGET

rm -rf $TARGET
cp -rf ../../python_altimeter_pkg $TARGET
cd $TARGET
# exit 0
P1=install_scripts/SYSTEM/home/pi/python_altimeter_pkg
mkdir -p $P1
cp -rf src $P1

mv install_scripts/SYSTEM/etc/fstab $P1/usb_fstab

cd install_scripts

mv SYSTEM python_altimeter_pkg
chmod 0775 python_altimeter_pkg/DEBIAN/postinst  #make DEBIAN dir and initial control file
chmod 0775 python_altimeter_pkg/DEBIAN/preinst  #make DEBIAN dir and initial control file
INSTALLEDSIZE=`du python_altimeter_pkg | tail -n 1 | awk '{print $1}'`

sed -i "s/VERSION/$VERSION/g" python_altimeter_pkg/DEBIAN/control
sed -i "s/INSTALLEDSIZE/$INSTALLEDSIZE/g" python_altimeter_pkg/DEBIAN/control
sed -i "s/ARCHITECTURE/$ARCHITECTURE/g" python_altimeter_pkg/DEBIAN/control
sed -i "s/PACKAGE/$PACKAGE/g" python_altimeter_pkg/DEBIAN/control

dpkg-deb -b target
