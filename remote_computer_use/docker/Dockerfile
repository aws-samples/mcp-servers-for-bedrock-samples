FROM ubuntu:24.04

# 避免交互式提示
ENV DEBIAN_FRONTEND=noninteractive

# 安装必要的软件包
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y sudo apt-utils software-properties-common && \
    apt-get install -y xdotool scrot && \
    # 添加Mozilla PPA
    add-apt-repository ppa:mozillateam/ppa -y || true && \
    apt-get update && \
    # 安装所需应用
    apt-get install -y --no-install-recommends firefox-esr galculator libreoffice xpdf && \
    # 安装Xfce桌面环境
    apt-get install -y xfce4 xfce4-goodies dbus-x11 && \
    # 安装TigerVNC和SSH服务器
    apt-get install -y tigervnc-standalone-server tigervnc-common openssh-server openssh-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /var/run/sshd

# 创建非root用户
RUN useradd -m -s /bin/bash vnc_user && \
    echo "vnc_user ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# 配置SSH服务器
RUN echo "PermitRootLogin no" >> /etc/ssh/sshd_config && \
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config && \
    echo "X11Forwarding yes" >> /etc/ssh/sshd_config

# 切换到非root用户
USER vnc_user
WORKDIR /home/vnc_user

# # 创建用于显示应用的桌面目录
# RUN mkdir -p /home/vnc_user/Desktop

# # 创建桌面快捷方式
# RUN echo "[Desktop Entry]\n\
# Type=Application\n\
# Name=Firefox ESR\n\
# Comment=Web Browser\n\
# Exec=firefox-esr %u\n\
# Icon=firefox-esr\n\
# Terminal=false\n\
# Categories=Network;WebBrowser;\n\
# StartupNotify=true\n\
# X-GNOME-Autostart-enabled=true\n\
# X-XFCE-Source=file:/home/vnc_user/Desktop/firefox.desktop" > /home/vnc_user/Desktop/firefox.desktop && \
#     \
#     echo "[Desktop Entry]\n\
# Type=Application\n\
# Name=Galculator\n\
# Comment=Scientific Calculator\n\
# Exec=galculator\n\
# Icon=galculator\n\
# Terminal=false\n\
# Categories=Utility;Calculator;\n\
# StartupNotify=true" > /home/vnc_user/Desktop/galculator.desktop && \
#     \
#     echo "[Desktop Entry]\n\
# Type=Application\n\
# Name=LibreOffice\n\
# Comment=Office Suite\n\
# Exec=libreoffice %U\n\
# Icon=libreoffice-startcenter\n\
# Terminal=false\n\
# Categories=Office;\n\
# StartupNotify=true" > /home/vnc_user/Desktop/libreoffice.desktop && \
#     \
#     echo "[Desktop Entry]\n\
# Type=Application\n\
# Name=Xpdf\n\
# Comment=PDF Viewer\n\
# Exec=xpdf %f\n\
# Icon=xpdf\n\
# Terminal=false\n\
# Categories=Viewer;PDF;\n\
# StartupNotify=true" > /home/vnc_user/Desktop/xpdf.desktop && \
#     \
#     chmod +x /home/vnc_user/Desktop/*.desktop

# 创建VNC和SSH配置目录
RUN mkdir -p ~/.vnc ~/.ssh

# 创建运行时目录
RUN mkdir -p /tmp/runtime-vnc_user

# 复制VNC配置文件
COPY --chown=vnc_user:vnc_user xstartup /home/vnc_user/.vnc/xstartup
COPY --chown=vnc_user:vnc_user start_vnc.sh /home/vnc_user/start_vnc.sh

# 设置执行权限
RUN chmod +x ~/.vnc/xstartup && \
    chmod +x ~/start_vnc.sh

# 生成SSH密钥
RUN ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""

# 暴露VNC和SSH端口
EXPOSE 5901 22

# 使用root用户启动服务
USER root
CMD ["/home/vnc_user/start_vnc.sh"]
