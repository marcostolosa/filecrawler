FROM ubuntu:jammy
MAINTAINER Helvio Junior <helvio_junior@hotmail.com>

USER root

SHELL ["/bin/bash", "-xo", "pipefail", "-c"]

# Generate locale C.UTF-8
ENV LANG C.UTF-8
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Update and install dependencies
RUN apt update \
  && apt upgrade -y \
  && apt install -yqq --no-install-recommends \
      git \
      gcc \
      python3 \
      python3-pip \
      python3-dev \
      build-essential \
      libssl-dev \
      libffi-dev\
      python3-setuptools \
      unzip \
      default-jre \
      default-jdk \
      libmagic-dev \
      curl \
      wget \
      gpg \
      vim \
      jq \
  && apt clean all \
  && apt autoremove

RUN echo FileCrawler > /etc/hostname

WORKDIR /tmp
ENV GIT_SSL_NO_VERIFY="true"
RUN python3 -m pip install -U pip && \
    git clone https://github.com/helviojunior/filecrawler.git installer && \
    VER=$(curl -s "https://raw.githubusercontent.com/chrismattmann/tika-python/master/tika/tika.py" | grep 'TIKA_VERSION' | grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' || echo '2.6.0') && \
    SERVER_HASH=$(curl -s "http://search.maven.org/remotecontent?filepath=org/apache/tika/tika-server-standard/$VER/tika-server-standard-$VER.jar.sha1") && \
    wget -nv -O "./installer/filecrawler/libs/bin/tika-server.jar" "http://search.maven.org/remotecontent?filepath=org/apache/tika/tika-server-standard/$VER/tika-server-standard-$VER.jar" && \
    echo "${SERVER_HASH} ./installer/filecrawler/libs/bin/tika-server.jar" | sha1sum -c - && \
    VER=$(curl -s  "https://api.github.com/repos/skylot/jadx/tags" | jq -r '.[0].name' | grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}') && \
    wget -nv -O "/tmp/jadx.zip" "https://github.com/skylot/jadx/releases/download/v$VER/jadx-$VER.zip" && \
    unzip -o /tmp/jadx.zip -d /tmp/ && \
    FILE=$(find /tmp/ -name "jadx*.jar") && \
    mv "$FILE" "./installer/filecrawler/libs/bin/jadx.jar" && \
    VER=$(curl -s  "https://api.github.com/repos/iBotPeaches/Apktool/tags" | jq -r '.[0].name' | grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}') && \
    wget -nv -O "/tmp/apktool.jar" "https://github.com/iBotPeaches/Apktool/releases/download/v$VER/apktool_$VER.jar" && \
    mv "/tmp/apktool.jar" "./installer/filecrawler/libs/bin/" && \
    python3 -m pip install -U installer/ && \
    filecrawler -h  && \
    mkdir -p /u01/ && mkdir /u02/ && chmod -R 777 /u0{1,2}/ && \
    ln -s /u01/ /root/.filecrawler && \
    rm -rf /tmp/*

WORKDIR /u02/

ENTRYPOINT ["filecrawler"]
