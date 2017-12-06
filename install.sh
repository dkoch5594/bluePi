#!/bin/bash

# install.sh
# david koch
# 11/26/2017
# commands for installing bluePi from scratch
# source: https://www.raspberrypi.org/forums/viewtopic.php?p=619713#p619713

# variables
installdir=$(pwd)
pa_ver_req=5.0
pa_ver_latest=11.1
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
	pa_ver=$(pulseaudio --version | sed 's/pulseaudio //')
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
	echo "Installing PulseAudio ${pa_ver_latest}"
	cd ~
	
	# Below line retrieves code for minimum required version according to source document at the top of the file
	# Making this code on latest libraries fails
	# wget : http://freedesktop.org/software/pulseaudio/releases/pulseaudio-5.0.tar.xz
	# Below line retrieves latest source code according to variable at top of file
	# How to detect updates and get newer code?
	wget : "https://freedesktop.org/software/pulseaudio/releases/pulseaudio-${pa_ver_latest}.tar.xz"
	
	# Need to verify download file using .sha1 file for downloaded file
	wget : "https://freedesktop.org/software/pulseaudio/releases/pulseaudio-${pa_ver_latest}.tar.xz.sha1"
	if [ $(sha1sum pulseaudio-${pa_ver_latest}.tar.xz) != $(cat pulseaudio-${pa_ver_latest}.tar.xz.sha1) ]
	then
		echo 'Download was corrupted, aborting install'
		exit 0
	else
		echo 'Verified download integrity'
	fi

	echo 'Extracting archive...'
	tar xvf "pulseaudio-${pa_ver_latest}.tar.xz"
	
	echo "Configuring and installing PulseAudio ${pa_ver_latest}"
	cd "pulseaudio-${pa_ver_latest}/"
	./configure --prefix=/usr --sysconfdir=/etc --localstatedir=/var --disable-bluez4 --disable-rpath --with-module-dir=/usr/lib/pulse/modules
	make
	sudo make install
	echo "PulseAudio ${pa_ver_latest} installed" 
fi

# Client should have PulseAudio installed at this point
# Create necessary groups whether or not PulseAudio installed for bluePi
# Need to check for existing groups/users

if [ -z $(cat /etc/group | grep 'pulse') ]
then
	echo "Creating pulse system group"
	sudo addgroup --system pulse
else
	echo "pulse system group exists"
	# What if pulse group is not system level?
fi
if [ -z $(cat /etc/passwd | grep 'pulse') ]
then
	echo "Creating pulse user"
	sudo adduser --system --ingroup pulse --home /var/run/pulse pulse
else
	echo "pulse user already exists"
fi
if [ -z $(cat /etc/group | grep 'pulse-access') ]
then
	echo "Creating pulse-access group"
	sudo addgroup --system pulse-access
else
	echo "pulse-access group already exists"
fi
if [ -z $(cat /etc/group | grep "audio.*pulse") ]
then
	echo "Adding user pulse to to group audio"
	sudo adduser pulse audio
else
	echo "User pulse is already in group audio"
fi
if [ -z $(cat /etc/group | grep "pulse-access.*root") ]
then
	echo 'Adding root to pulse-access group'
	sudo adduser root pulse-access
else
	echo "User root is alrady in group pulse-access"
fi

# Make a backup of the pulse daemon conf file
sudo cp /etc/pulse/daemon.conf /etc/pulse/daemon.conf.bak

# **BELOW COMMANDS NEED TESTING**
# Use sed to reconfigure pulse audio daemon conf file
cat /etc/pulse/daemon.conf | sed "s/resample-method = speex-float-3/; &\nresample-method = speex-fixed-3/"

# Use sed to modify the pulse system.pa file
cat /etc/pulse/system.pa | sed "s/load-module module-udev-detect/#&\n& tsched=0/"

# Add code to load bluetooth-discover module
echo "\n" >> /etc/pulse/system.pa
echo "Below code added from source: https://www.raspberrypi.org/forums/viewtopic.php?p=619713#p619713" >> /etc/pulse/system.pa
echo "### Automatically load driver modules for Bluetooth hardware" >> /etc/pulse/system.pa
echo ".ifexists module-bluetooth-discover.so" >> /etc/pulse/system.pa
echo "    load-module module-bluetooth-discover" >> /etc/pulse/system.pa
echo "endif" >> /etc/pulse/system.pa

echo "Finished instaling and configurng PulseAudio ${pa_ver_latest}"



