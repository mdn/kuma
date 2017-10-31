#!/bin/bash
set -eo pipefail

# Required environment variables if using --stage:
# BRANCH_NAME, BUILD_NUMBER

# defaults and constants
NICK="jenkins"
CHANNEL="#mdndev"
SERVER="irc.mozilla.org:6697"
BLUE_BUILD_URL="https://ci.us-west.moz.works/blue/organizations/jenkins/mdn_multibranch_pipeline"
BLUE_BUILD_URL="${BLUE_BUILD_URL}/detail/${BRANCH_NAME/\//%2f}/${BUILD_NUMBER}/pipeline"
# colors and styles: values from the following links
# http://www.mirc.com/colors.html
# http://stackoverflow.com/a/13382032
RED=$'\x034'
YELLOW=$'\x038'
GREEN=$'\x039'
BLUE=$'\x0311'
BOLD=$'\x02'
NORMAL=$'\x0F'

# parse cli args
while [[ $# -gt 1 ]]; do
    key="$1"
    case $key in
        --stage)
            STAGE="$2"
            shift # past argument
            ;;
        --status)
            STATUS="$2"
            shift # past argument
            ;;
        -m|--message)
            MESSAGE="$2"
            shift # past argument
            ;;
        --irc_nick)
            NICK="$2"
            shift # past argument
            ;;
        --irc_server)
            SERVER="$2"
            shift # past argument
            ;;
        --irc_channel)
            CHANNEL="$2"
            shift # past argument
            ;;
    esac
    shift # past argument or value
done

if [[ -n "$STATUS" ]]; then
    STATUS=$(echo "$STATUS" | tr '[:lower:]' '[:upper:]')
    case "$STATUS" in
      'SUCCESS')
        STATUS_COLOR="🎉 ${BOLD}${GREEN}"
        ;;
      'SHIPPED')
        STATUS_COLOR="🚢 ${BOLD}${GREEN}"
        ;;
      'WARNING')
        STATUS_COLOR="⚠️ ${BOLD}${YELLOW}"
        ;;
      'FAILURE')
        STATUS_COLOR="🚨 ${BOLD}${RED}"
        ;;
      *)
        STATUS_COLOR="✨ $BLUE"
        ;;
    esac
    STATUS="${STATUS_COLOR}${STATUS}${NORMAL}: "
fi

if [[ -n "$STAGE" ]]; then
    MESSAGE="${STATUS}${STAGE}:"
    MESSAGE="$MESSAGE Branch ${BOLD}${BRANCH_NAME}${NORMAL} build #${BUILD_NUMBER}: ${BLUE_BUILD_URL}"
elif [[ -n "$MESSAGE" ]]; then
    MESSAGE="${STATUS}${MESSAGE}"
else
    echo "Missing required arguments"
    echo
    echo "Usage: irc-notify.sh [--stage STAGE]|[-m MESSAGE]"
    echo "Optional args: --status, --irc_nick, --irc_server, --irc_channel"
    exit 1
fi

if [[ -n "$BUILD_NUMBER" ]]; then
    NICK="${NICK}-${BUILD_NUMBER}"
fi

(
  echo "NICK ${NICK}"
  echo "USER ${NICK} 8 * : ${NICK}"
  sleep 5
  echo "JOIN ${CHANNEL}"
  echo "NOTICE ${CHANNEL} :${MESSAGE}"
  echo "QUIT"
) | openssl s_client -connect "$SERVER" > /dev/null 2>&1
