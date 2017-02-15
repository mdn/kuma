#!/bin/bash

MY_BRANCH=$(git rev-parse --abbrev-ref HEAD)
PROJECT_ROOT=$(git rev-parse --show-toplevel)

if [ "${MY_BRANCH}" = "master" ]; then
    echo "Can't create demo instance from master branch"
    exit 1
fi

grep '^[a-z0-9-]*[a-z0-9]$' <<< $MY_BRANCH > /dev/null
if [ $? -ne 0 ]; then
    echo "Invalid valid branch name"
    echo "Branch name must be an acceptable Dies application name which uses the following regex:"
    echo "^[a-z0-9-]*[a-z0-9]$"
    echo "Note: \"mdn-demo-\" is automatically prepended to the branch name during deployment."
    exit 1
fi


YAML_FILE="${PROJECT_ROOT}/Jenkinsfiles/${MY_BRANCH}.yml"

cat << EOF > ${YAML_FILE}
pipeline:
  enabled: true
  script: demo
EOF

echo "Created ${YAML_FILE}"
git add "${YAML_FILE}"

echo "Perform a git commit and push for the instance to be created."
