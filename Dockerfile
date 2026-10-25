# syntax=docker/dockerfile:1
ARG BASE_IMAGE=lscr.io/linuxserver/webtop:ubuntu-xfce@sha256:278797c03b62454aaf05cd1fdeb35dbdc822846855020f9e5233f508a89980d9
FROM ${BASE_IMAGE}

USER root
COPY releases.lock.json /opt/craft-suite/releases.lock.json
COPY scripts/install-releases.py /tmp/install-releases.py
COPY scripts/verify-installed.py /tmp/verify-installed.py
RUN python3 /tmp/install-releases.py /opt/craft-suite/releases.lock.json /tmp/craft-packages \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
         /tmp/craft-packages/*.deb vulkan-tools mesa-utils \
    && python3 /tmp/verify-installed.py /opt/craft-suite/releases.lock.json /tmp/craft-packages \
    && rm -rf /tmp/craft-packages /tmp/install-releases.py /tmp/verify-installed.py /var/lib/apt/lists/*

COPY scripts/craft-start /usr/local/bin/craft-start
COPY scripts/craft-shared-files.py /usr/local/bin/craft-shared-files.py
COPY root/etc/xdg/autostart/craft-suite.desktop /etc/xdg/autostart/craft-suite.desktop
RUN chmod 755 /usr/local/bin/craft-start
# rfd dialogs in the Craft applications use the desktop portal on Linux.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
         xdg-desktop-portal xdg-desktop-portal-gtk \
    && rm -rf /var/lib/apt/lists/*
ENV CRAFT_APP=artcraft-launcher
LABEL org.opencontainers.image.title="Craft Suite" \
      org.opencontainers.image.description="Craft creative applications with a browser desktop and server GPU access"
