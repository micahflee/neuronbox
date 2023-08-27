#!/bin/bash

FFMPEG_TAG=n6.0

# This script builds all of the dependendencies for the desktop app, including:
# - the frontend web interface
# - ffmpeg from source
# - uses cx_freeze to freeze the python app into an executable

# Make sure a virtual environment is activated
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo "Please activate a virtual environment before running this script."
    exit 1
fi

# Build the frontend
cd frontend
npm install
npm run build
cd ..

# Make sure the resources directory exists
if [[ ! -d "resources" ]]; then
    mkdir resources
fi

# Build ffmpeg

# You need the following dependencies:
# - macOS: brew install yasm pkg-config
# - Linux: sudo apt-get install -y build-essential yasm pkg-config

if [[ ! -d "build" ]]; then
    mkdir build
fi

cd build
if [[ ! -d "ffmpeg" ]]; then
    git clone https://git.ffmpeg.org/ffmpeg.git
fi
cd ffmpeg
git fetch
git checkout ${FFMPEG_TAG}

# Import ffmpeg signing key and verify the git tag
gpg --keyserver keyserver.ubuntu.com --recv 0xDD1EC9E8DE085C629B3E1846B18E8928B3948D64
git tag -v ${FFMPEG_TAG}
if [[ $? -ne 0 ]]; then
    echo "Failed to verify the git tag for ffmpeg."
    exit 1
fi

# Compile
./configure
if [[ "$OSTYPE" == "darwin"* ]]; then
    make -j$(sysctl -n hw.logicalcpu)
else
    make -j$(nproc)
fi
cd ../..

# Copy the ffmpeg binary to the resources directory
cp build/ffmpeg/ffmpeg resources/ffmpeg

# Freeze backend.py
pyinstaller --distpath resources --noconfirm backend.spec
