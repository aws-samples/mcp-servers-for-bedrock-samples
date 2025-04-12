#!/bin/bash

# 设置SSH密码
echo "vnc_user:${SSH_PASSWORD:-vncpassword}" | chpasswd

# 启动SSH服务
/usr/sbin/sshd

# 设置环境变量
export XDG_RUNTIME_DIR=/tmp/runtime-vnc_user
mkdir -p $XDG_RUNTIME_DIR
chmod 700 $XDG_RUNTIME_DIR

# 切换到vnc_user用户运行VNC
su - vnc_user -c "
# 设置VNC密码
mkdir -p ~/.vnc
echo \"${VNC_PASSWORD:-vncpassword}\" | vncpasswd -f > ~/.vnc/passwd
chmod 600 ~/.vnc/passwd

# 清理所有旧的VNC服务器进程
vncserver -kill :1 >/dev/null 2>&1 || :
rm -rf /tmp/.X1-lock /tmp/.X11-unix/X1 >/dev/null 2>&1 || :

# 启动VNC服务器
vncserver :1 -geometry \"${VNC_RESOLUTION}\" -depth 24 -localhost no

echo \"VNC Server started on port 5901\"
echo \"Use a VNC viewer to connect to \$(hostname -I | awk '{print \$1}'):5901\"
echo \"SSH access available on port 22, username: vnc_user\"
"

# 保持容器运行
tail -f /home/vnc_user/.vnc/*:1.log
