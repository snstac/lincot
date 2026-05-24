#!/bin/bash
echo "Installing Debian package build dependencies"
apt update -qq
apt install -y dpkg-dev
