ARG BASE_IMAGE=ubuntu:20.04
FROM $BASE_IMAGE AS base

MAINTAINER "Giacomo Nodjoumi <giacomo.nodjoumi@hyranet.info>"

ENV DEBIAN_FRONTEND=noninteractive

# Install Python and its tools

RUN apt update && apt install --no-install-recommends -y 	\
apt-transport-https \
    ca-certificates \
    curl \
    gnupg2 \
    locales \
    nano \
    software-properties-common \
    sudo \
    tzdata \
    vim \
    wget \
    git 							\
    build-essential 				\
    curl 							\
    libgl1-mesa-dev 				\
    libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

#RUN echo 'alias python=python3.9' >> ~/.bashrc
#RUN echo 'alias pip=pip3' >> ~/.bashrc

#ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
#ENV C_INCLUDE_PATH=/usr/include/gdal

RUN pip3 --no-cache-dir install 	\
	setuptools 						\
    jupyterlab \
    geopandas \
    numpy 							\
  	opencv-python					\
  	opencv-contrib-python			\
  	pandas							\
  	psutil           \
    pysis							\
  	rasterio						\
  	scikit-image					\
  	scikit-learn					\
  	scipy 							\
  	tqdm							\
    spectral \
    && rm -rf /var/lib/apt/lists/*

ARG UID=1000
ARG GID=100
ARG PASSWORD=123456
RUN useradd -m -d /home/user -u $UID -g $GID -s /bin/bash user 		\
    && su - user -c 'ln -s /mnt/data /home/user/data' 				\
    && echo "user:$PASSWORD" | chpasswd

ADD PyISIS-Parallel /home/user/PyISIS-Parallel
RUN chmod +x /home/user/PyISIS-Parallel/jupyter.sh
WORKDIR /home/user/
USER user
