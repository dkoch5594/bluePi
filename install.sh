#!/bin/bash

# install.sh
# david koch
# 11/26/2017
# commands for installing bluePi from scratch
# source: https://www.raspberrypi.org/forums/viewtopic.php?p=619713#p619713

# variables
installdir=$(pwd)
pa_ver_req=5.0
be_ver_req=5.23
install_pa=false
install_be=false

# update system pachages
echo 'Updating system packages'
sudo apt-get update
sudo apt-get -y upgrade

# install dependencies
echo 'Installing missing PulseAudio and Bluez dependencies
# Below line is found in source document at top of file
# sudo apt-get install -y libusb-dev libdbus-1-dev libglib2.0-dev libudev-dev libical-dev libreadline-dev libltdl-dev libsamplerate0-dev libsndfile1-dev libasound2-dev libavahi-client-dev libspeexdsp-dev liborc-0.4-dev intltool libtdb-dev libssl-dev libjson0-dev libsbc-dev libcap-dev

# libjson0-dev has been deprecated in Raspbian Stretch
# source: https://github.com/emersonmello/doorlock_raspberrypi/issues/1
# Replacing libjson0-dev with libjson-c-dev
sudo apt-get install -y libusb-dev libdbus-1-dev libglib2.0-dev libudev-dev libical-dev libreadline-dev libltdl-dev libsamplerate0-dev libsndfile1-dev libasound2-dev libavahi-client-dev libspeexdsp-dev liborc-0.4-dev intltool libtdb-dev libssl-dev libjson-c-dev libsbc-dev libcap-dev

# removing problematic library
sudo apt-get remove -y libpulse0

# check if PulseAudio is installed
pa_loc=$(which pulseaudio)
if [ -z $pa_loc ]
then
	echo 'PuleAudio is not installed'
	$install_pa=true
else
	pa_ver=$(pulseaudio --version)
	# Version Checking code
	# Source: https://stackoverflow.com/questions/4023830/how-to-compare-two-strings-in-dot-separated-version-format-in-bash
	if [ $pa_ver == $pa_ver_req ]
	then
		echo 'Required version of PulseAudio is installed'
	else
		local IFS=.
		if ((10#${pa_ver[i]} > 10#${pa_ver_req[i]}))
		then
			echo 'Installed PulseAudio version is greater than that required'
		fi
		if ((10#${pa_ver[i]} < 10#${pa_ver_req[i]}))
		then
			echo 'Installed PulseAudio version is insufficient'
			$install_pa=true
		fi
	fi
fi

# Install PulseAudio if required
if [ $install_pa = true ]
then
	echo 'Installing PulseAudio 5.0'
	echo 'You my wish to upgrade after the install'
	cd ~
	wget : http://freedesktop.org/software/pulseaudio/releases/pulseaudio-5.0.tar.xz
	tar xvf pulseaudio-5.0.tar.xz
	cd pulseaudio-5.0/
	./configure --prefix=/usr --sysconfdir=/etc --localstatedir=/var --disable-bluez4 --disable-rpath --with-module-dir=/usr/lib/pulse/modules
	make
	sudo make install
	echo 'Creating pulse and audio users to run PulseAudio in system-wide mode
	sudo addgroup --system pulse
	sudo adduser --system --ingroup pulse --home /var/run/pulse pulse
	sudo addgroup --system pulse-access
	sudo adduser pulse audio
	echo 'Adding root to pulse-access group'
	sudo adduser root pulse-access
	

