#!/bin/bash

# Exit script on any error
set -e

echo "=== Updating system packages ==="
sudo apt update
sudo apt upgrade -y

echo "=== Installing necessary applications ==="
sudo apt install -y xdotool scrot
sudo add-apt-repository ppa:mozillateam/ppa -y
sudo apt-get install -y --no-install-recommends libreoffice firefox-esr

echo "=== Installing Xfce desktop environment ==="
sudo apt install -y xfce4 xfce4-goodies

echo "=== Installing TigerVNC Server ==="
sudo apt install -y tigervnc-standalone-server tigervnc-common

echo "=== Setting up VNC password ==="
echo "Please create a VNC password when prompted"
vncpasswd

echo "=== Creating VNC startup file ==="
mkdir -p ~/.vnc
cat > ~/.vnc/xstartup << 'EOF'
#!/bin/sh

unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS

[ -x /etc/vnc/xstartup ] && exec /etc/vnc/xstartup
[ -r $HOME/.Xresources ] && xrdb $HOME/.Xresources

export XKL_XMODMAP_DISABLE=1
startxfce4
EOF

echo "=== Making startup file executable ==="
chmod +x ~/.vnc/xstartup

echo "=== Starting VNC Server ==="
tigervncserver -xstartup /usr/bin/startxfce4 -SecurityTypes VncAuth,TLSVnc -geometry 1024x768 -localhost no :1

echo "=== VNC Server setup complete! ==="
echo "You can connect to your VNC server at $(hostname -I | awk '{print $1}'):5901"
