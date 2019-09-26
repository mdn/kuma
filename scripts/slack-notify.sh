#!/bin/bash

usage() {
    echo -en "Usage: $0 --stage <stage> --message <message> --status <status> \n\n"
    echo -en "Options: \n"
    echo -en "  --debug     Debug basically sets set -x in bash \n"
    echo -en "  --message   Slack message to send\n"
    echo -en "  --stage     Job stage \n"
    echo -en "  --status    Job status\n"
    echo -en "  --hook      Slack incoming webhook url\n"
}

return_status() {
	local STATUS=$1

	if [[ -n "$STATUS" ]]; then
        STATUS=$(echo "$STATUS" | tr '[:lower:]' '[:upper:]')
        case "$STATUS" in
        'SUCCESS')
            STATUS_PREFIX=":tada:"
            COLOR="good"
        ;;
        'SHIPPED')
            STATUS_PREFIX=":ship:"
            COLOR="good"
        ;;
        'WARNING')
            STATUS_PREFIX=":warning:"
            COLOR="warning"
        ;;
        'FAILURE')
            STATUS_PREFIX=":rotating_light:"
            COLOR="danger"
        ;;
        *)
            STATUS_PREFIX=":sparkles:"
            COLOR="good"
        ;;
        esac
        STATUS="${STATUS_PREFIX} *${STATUS}* "
        echo "STATUS=${STATUS}"
        echo "COLOR=${COLOR}"
    fi
}


while [ "$1" != "" ]; do
    case $1 in
    -h | --help )
        usage
        exit 0
    ;;
    -x | --setx | --debug )
        set -x
    ;;
    --stage )
        STAGE="${2}"
        shift
    ;;
    --status )
        STATUS=$(return_status "${2}" | grep "STATUS" | sed 's/.*=//')
        COLOR=$(return_status "${2}" | grep "COLOR" | sed 's/.*=//')
        shift
    ;;
    --hook )
        HOOK="${2}"
        shift
    ;;
    -m | --message)
        MESSAGE="${2}"
        shift
    ;;
    esac
    shift
done

if [[ -n "$STAGE" ]]; then
    MESSAGE="${STATUS}${STAGE}"
elif [[ -n "$MESSAGE" ]]; then
    MESSAGE="${STATUS}${MESSAGE}"
else
    usage
    exit 1
fi

if [ -z "${HOOK}" ]; then
    echo "[ERROR]: --hook or webhook is not set"
    exit 1
fi

read -r -d '' payload <<EOF
{
    "attachments": [
        {
            "color": "${COLOR}",
            "title": "${JOB_NAME} Build #${BUILD_NUMBER}",
            "title_link": "${RUN_DISPLAY_URL}",
            "text": "${MESSAGE}",
            "footer": "Slack incoming webhook",
            "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
            "ts": $(date +%s)
        }
    ]
}
EOF

status_code=$(curl \
    --write-out "%{http_code}" \
    --silent \
    -o /dev/null \
    -X POST \
    -H 'Content-type: application/json' \
    --data "${payload}" "${HOOK}")

echo "${status_code}"
