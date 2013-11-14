#!/bin/bash

CDN=https://developer.cdn.mozilla.net
LOCAL=media

# Given a path relative to the CDN root, download the asset at that path
function download {
  ASSET=$1
  ASSET_FILENAME=`basename $ASSET`
  ASSET_PATH=${ASSET/\/$ASSET_FILENAME/}

  # Create a local directory with the same name as the directory where the asset
  # lives on the CDN
  if [ ! -d $ASSET_PATH ]; then
    mkdir -p $ASSET_PATH
  fi

  # Download the asset
  wget $CDN/$ASSET -O $ASSET_PATH/$ASSET_FILENAME
}

function download_referenced {
  # All additional assets referenced with url()
  REFERENCED=`grep -Pro "url\(.*?\)" $LOCAL | sed -r "s/url\((\"|')?(.*?)(\?.*$|#.*$|\".*$|'.*$|\).*$)/\2/" | sort | uniq`

  while read -r REFERENCE_INFO; do
    REFERENCED_FROM=`echo $REFERENCE_INFO | sed -r "s/(.*?\/?)+\/.*?:.*$/\1/"`
    REFERENCED_FILENAME=`echo $REFERENCE_INFO | sed -r "s/.*?:\/?(.*$)/\1/"`

    # Given the directory that the asset was referenced from and the filename of
    # the asset, get the absolute URL of the asset
    if [[ $REFERENCED_FILENAME == $LOCAL* ]]; then
      ABSOLUTE_URL=$REFERENCED_FILENAME
    else
      ABSOLUTE_URL=$REFERENCED_FROM/$REFERENCED_FILENAME
    fi
    download $ABSOLUTE_URL
  done <<< "$REFERENCED"
}

# Download all assets used by index.html
REQUIRED_ASSETS=`grep "\"media/" index.html | sed -r "s/.*\"(media\/[^\"]*)\".*$/\1/"`
while read -r ASSET; do
  download $ASSET
done <<< "$REQUIRED_ASSETS"

# Download all assets referenced from those assets
download_referenced
