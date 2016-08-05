#!/bin/bash
# Copyright (c) 2003-2014, CKSource - Frederico Knabben. All rights reserved.
# For licensing, see http://ckeditor.com/license

# Build CKEditor for Kuma.
# Based on https://github.com/ckeditor/ckeditor-presets/blob/master/build.sh

CKEDITOR_VERSION="4.5.7"

CKBUILDER_VERSION="1.7.2"
CKBUILDER_URL="http://download.cksource.com/CKBuilder/$CKBUILDER_VERSION/ckbuilder.jar"

# Plugin versions
DESCRIPTION_LIST_VERSION="e365ac622a995d535266c22f0c44b743f8fffa14"
SCAYT_VERSION="release.4.8.4.0"
WSC_VERSION="release.4.8.4.0"


set -e

echo "CKEditor Builder"
echo "========================"

target="../build"


echo ""
echo "Pulling down CKEditor from GitHub..."
rm -rf ckeditor/
git clone -b $CKEDITOR_VERSION --single-branch --depth=1 https://github.com/ckeditor/ckeditor-dev.git ckeditor
rm -rf ckeditor/.git


# User the ckeditor-dev commit hash as the revision.
cd ckeditor/
rev=`git rev-parse --verify --short HEAD`
cd ..

PROGNAME=$(basename $0)
MSG_UPDATE_FAILED="Warning: The attempt to update ckbuilder.jar failed. The existing file will be used."
MSG_DOWNLOAD_FAILED="It was not possible to download ckbuilder.jar."

function error_exit
{
	echo "${PROGNAME}: ${1:-"Unknown Error"}" 1>&2
	exit 1
}

function command_exists
{
	command -v "$1" > /dev/null 2>&1;
}

function download_plugin
{
	echo "downloading $1 plugin, version $2"
	rm -rf plugins/$1
	git clone $3 plugins/$1
	cd plugins/$1
	git checkout $2
	cd -
	rm -rf plugins/$1/.git
}

# Move to the script directory.
cd $(dirname $0)

# Download/update ckbuilder.jar
mkdir -p ckbuilder/$CKBUILDER_VERSION
cd ckbuilder/$CKBUILDER_VERSION
if [ -f ckbuilder.jar ]; then
	echo "Checking/Updating CKBuilder..."
	if command_exists curl ; then
	curl -O -R -z ckbuilder.jar $CKBUILDER_URL || echo "$MSG_UPDATE_FAILED"
	else
	wget -N $CKBUILDER_URL || echo "$MSG_UPDATE_FAILED"
	fi
else
	echo "Downloading CKBuilder..."
	if command_exists curl ; then
	curl -O -R $CKBUILDER_URL || error_exit "$MSG_DOWNLOAD_FAILED"
	else
	wget -N $CKBUILDER_URL || error_exit "$MSG_DOWNLOAD_FAILED"
	fi
fi
cd ../..



echo ""
echo "Copying extra plugins..."

download_plugin "descriptionlist" $DESCRIPTION_LIST_VERSION "https://github.com/Reinmar/ckeditor-plugin-descriptionlist.git"

download_plugin "scayt" $SCAYT_VERSION "https://github.com/WebSpellChecker/ckeditor-plugin-scayt.git"

download_plugin "wsc" $WSC_VERSION "https://github.com/WebSpellChecker/ckeditor-plugin-wsc.git"

cp -r plugins/* ckeditor/plugins/


echo ""
echo "Deleting $target..."
rm -rf $target


# Run the builder.
echo ""
echo "Building the package..."

java -jar ckbuilder/$CKBUILDER_VERSION/ckbuilder.jar --build ckeditor $target \
	-s --version="$CKEDITOR_VERSION" --revision $rev --build-config build-config.js --overwrite --no-tar --no-zip "$@"


echo "Removing added plugins..."
cd ckeditor
git clean -d -f -f
cd ..


echo ""
echo "Build created into the \"$target\" directory."
echo ""
