FROM ros:jazzy
ARG USERNAME=USERNAME
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Delete user if it exists in container (e.g Ubuntu Noble: ubuntu)
RUN if id -u $USER_UID ; then userdel `id -un $USER_UID` ; fi

# Create the user
RUN groupadd --gid $USER_GID $USERNAME && \
    useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

RUN apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y \
    # espeak \
    # i2c-tools \
    # libsdl2-dev \
    # libsdl2-mixer-dev \
    # libttspico-utils \
    # portaudio19-dev \
    # python3-pillow \
    # python3-pyserial \
    # raspi-config \
    # sox \
    docker-compose-v2 \
    docker.io \
    python3-gpiozero \
    python3-pip \
    python3-pyaudio \
    python3-rpi-lgpio \
    python3-smbus \
    python3-smbus2 \
    python3-spidev \
    python3-twisted \
    python3-watchdog \
    ros-jazzy-ackermann-msgs \
    vim 

ENV SHELL=/bin/bash
#ENV GPIOZERO_PIN_FACTORY=lgpio

RUN usermod -a -G kvm,i2c,sgx $USERNAME
RUN ln -s /dev/gpiochip0 /dev/gpiochip4 

USER $USERNAME
WORKDIR /home/$USERNAME
COPY .bashrc . 
CMD ["/bin/bash"]