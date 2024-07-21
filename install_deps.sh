#! /bin/bash
set -e

echo Installing protoc
mkdir -p protoc && \
	cd protoc && \
	wget https://github.com/protocolbuffers/protobuf/releases/download/v24.3/protoc-24.3-linux-x86_64.zip && \
	unzip protoc-24.3-linux-x86_64.zip -d protoc && \
        sudo mv protoc/bin/protoc /usr/local/bin/protoc && \
	cd ../ && sudo rm -rf protoc

echo installing protolinters

mkdir protolint_install
cd protolint_install && \
	wget https://github.com/yoheimuta/protolint/releases/download/v0.27.0/protolint_0.27.0_Linux_x86_64.tar.gz && \
	tar -xvf protolint_0.27.0_Linux_x86_64.tar.gz && \
	sudo mv protolint /usr/local/bin/protolint && \
	sudo rm -rf ../protolint_install

echo Done!
