#!/bin/bash
#
# Run selenium-based function tests against Kuma. Usage:
# Default, test against running development environment):
#   scripts/run_functional_tests.sh
# Run just one test against development environment
#   scripts/run_functional_tests.sh tests/functional/test_home.py::test_footer_displays
# Run just in Chrome
#   BROWSERS=chrome scripts/run_functional_tests.sh
# Run against stage.mdn.moz.works
#   BASE_URL=https://stage.mdn.moz.works scripts/run_functional_tests.sh

#
# Configuration
#

# DEBUG_SCRIPT: 1 to show commands as Bash processes and executes them
DEBUG_SCRIPT=${DEBUG_SCRIPT:-0}
if [[ "$DEBUG_SCRIPT" != "0" ]]; then
    echo "*** Being verbose..."
    set -v
    set -x
fi

# PYTEST_ARGS: Arguments to pytest, i.e. what to run
PYTEST_ARGS="${@}"
if [ -z "$PYTEST_ARGS" ]; then
    PYTEST_ARGS="tests/functional -m \"not login\" -vv --reruns=1"
fi

# PROJECT_NAME: Added to names as flavor, should match your source checkout name
PROJECT_NAME=${PROJECT_NAME:-kuma}

# BASE_URL: Protocol + domain to test against, such as https://stage.mdn.moz.works
BASE_URL=${BASE_URL:-http://web:8000}

# TEST_DEV: Test against the local development environment
TEST_DEV=${TEST_DEV:-unset}
if [[ "$TEST_DEV" == "unset" ]]; then
    if [[ "$BASE_URL" == "http://web:8000" ]]; then
        TEST_DEV=1
    else
        TEST_DEV=0
    fi
fi

# Link parameters for development environment
if [[ "$TEST_DEV" == "0" ]]; then
    NETWORK_DEV=""
    LINK_DEV=""
else
    NETWORK_DEV="--network ${PROJECT_NAME}_default"
    LINK_DEV="--link ${PROJECT_NAME}_web_1:web"
fi

# SELENIUM_TAG: Docker image tag, see https://hub.docker.com/r/selenium/hub/tags/
SELENIUM_TAG=${SELENIUM_TAG:-2.48.2}

# SELENIUM_HUB: 1 to test with Selenium Hub / Node, somewhat like Jenkins
SELENIUM_HUB=${SELENIUM_HUB:-0}

# BROWSERS: Which browsers to test against
BROWSERS=${BROWSERS:-chrome firefox}

# SELENIUM_LOGS: 1 to print the docker logs of Selenium containers
SELENIUM_LOGS=${SELENIUM_LOGS:-0}

# PAUSE: 1 to pause before shutting down Selenium containers, to debug
PAUSE=${PAUSE:-0}

# TRACE_GECKODRIVER: 1 to make geckodriver output debug info, needed for bugs
TRACE_GECKODRIVER=${TRACE_GECKODRIVER:-1}

# FIREFOX_ENV, CHROME_ENV: Extra docker commands for these images
# Recommended on:
# https://github.com/SeleniumHQ/docker-selenium/blob/master/README.md#running-the-images
#FIREFOX_ENV=${FIREFOX_ENV:- --shm-size 2g}
#CHROME_ENV=${CHROME_ENV:- -v /dev/shm:/dev/shm}
FIREFOX_ENV=${FIREFOX_ENV:-}
CHROME_ENV=${CHROME_ENV:-}
if [ "$TRACE_GECKODRIVER" != "0" ]; then
    FIREFOX_ENV="$FIREFOX_ENV --env DRIVER_LOGLEVEL=trace"
fi

# SAVE_RESULTS: Create pytest-selenium HTML output, with logs and screenshots
# RESULTS_DIR: The directory to put the HTML report
SAVE_RESULTS=${SAVE_RESULTS:-1}
if [[ "$SAVE_RESULTS" != "0" ]]; then
    NOW=`date +%Y%m%d_%H%M`
    RESULTS_DIR=${RESULTS_DIR:-test_results/functional_$NOW}
    mkdir -p "$RESULTS_DIR"
fi

#
# Configuration complete
#

# Clean up
find . \( -name \*.pyc -o -name \*.pyo -o -name __pycache__ \) -prune -exec rm -rf {} +


(
    set -e  # On error, go to the end of this section
    echo "*** Building integration tests image..."
    docker build -t kuma-integration-tests:latest --pull=true \
        -f docker/images/integration-tests/Dockerfile .

    # Start Selenium Hub, if requested
    if [[ "$SELENIUM_HUB" != "0" ]]; then
        echo "*** Running hub..."
        docker run -d --name "selenium-hub-${PROJECT_NAME}" -p 4444:4444 \
            ${NETWORK_DEV} "selenium/hub:${SELENIUM_TAG}"
    fi

    # Start Standalone Dockerized or Selenium Node browsers
    for browser in $BROWSERS; do
        if [[ "$browser" == "firefox" ]]; then
            BROWSER_ENV=$FIREFOX_ENV
        elif [[ "$browser" == "chrome" ]]; then
            BROWSER_ENV=$CHROME_ENV
        else
            BROWSER_ENV=
        fi
        if [[ "$SELENIUM_HUB" == "0" ]]; then
            echo "*** Running dockerized ${browser}..."
            docker run -d --name "selenium-${browser}-${PROJECT_NAME}" \
                ${BROWSER_ENV} ${LINK_DEV} ${NETWORK_DEV}\
                "selenium/standalone-${browser}:${SELENIUM_TAG}"
        else
            echo "*** Running node ${browser}..."
            if [[ ${SELENIUM_TAG:0:1} == "2" ]]; then
                # Selenium 2 expects link env variables
                # https://docs.docker.com/compose/link-env-deprecated/
                HUB_ENV="--env HUB_PORT_4444_TCP_ADDR=hub"
                HUB_ENV+=" --env HUB_PORT_4444_TCP_PORT=4444"
            else
                HUB_ENV=
            fi

            docker run -d --name "selenium-node-${browser}-${PROJECT_NAME}" \
                ${NETWORK_DEV} ${LINK_DEV} \
                --link "selenium-hub-${PROJECT_NAME}:hub" \
                ${BROWSER_ENV} ${HUB_ENV}\
                "selenium/node-${browser}:${SELENIUM_TAG}"
        fi
    done
)
if [ $? -eq 0 ]; then
    # Run the integration tests for each browser
    for browser in $BROWSERS; do

        # Set results folder
        if [[ "$SAVE_RESULTS" == "0" ]]; then
            RESULTS_MOUNT=""
            RESULTS_HTML=""
        else
            mkdir "${RESULTS_DIR}/${browser}"
            RESULTS_MOUNT="-v $PWD/${RESULTS_DIR}/${browser}:/results"
            RESULTS_HTML="--html=/results/pytest.html"
        fi

        # Set hub name
        if [[ "SELENIUM_HUB" == "0" ]]; then
            HUB_NAME="selenium-${browser}-${PROJECT_NAME}"
        else
            HUB_NAME="selenium-hub-${PROJECT_NAME}"
        fi

        # Setup pytest command
        cmd="pytest"
        cmd+=" --driver Remote --capability browserName ${browser}"
        cmd+=" --host hub"
        cmd+=" --base-url=${BASE_URL}"
        cmd+=" ${RESULTS_HTML} ${PYTEST_ARGS}"

        echo "*** Running integration tests against ${browser}..."
        docker run -it \
            --link "${HUB_NAME}:hub" \
            ${LINK_DEV} ${NETWORK_DEV} ${RESULTS_MOUNT} \
            kuma-integration-tests:latest sh -c "$cmd"
    done
fi

# Print Selenium logs if requested
if [[ "$SELENIUM_LOGS" != "0" ]]; then
    if [[ "$SELENIUM_HUB" == "0" ]]; then
        for browser in ${BROWSERS}; do
            echo "*** Logs for selenium-${browser}-${PROJECT_NAME}"
            docker logs "selenium-${browser}-${PROJECT_NAME}"
        done
    else
        echo "*** Logs for selenium-hub-${PROJECT_NAME}"
        docker logs "selenium-hub-${PROJECT_NAME}"
        for browser in ${BROWSERS}; do
            echo "*** Logs for selenium-node-${browser}-${PROJECT_NAME}"
            docker logs "selenium-node-${browser}-${PROJECT_NAME}"
        done
    fi
fi

# Save Selenium logs if requested
if [[ "$SAVE_RESULTS" != "0" ]]; then
    if [[ "$SELENIUM_HUB" == "0" ]]; then
        for browser in ${BROWSERS}; do
            docker logs "selenium-${browser}-${PROJECT_NAME}" &>  "${RESULTS_DIR}/${browser}/selenium.log"
        done
    else
        docker logs "selenium-hub-${PROJECT_NAME}" &> "${RESULTS_DIR}/hub.log"
        for browser in ${BROWSERS}; do
            docker logs "selenium-node-${browser}-${PROJECT_NAME}" &> "${RESULTS_DIR}/${browser}/node.log"
        done
    fi
fi

if [[ "$PAUSE" != "0" ]]; then
    read -p "Pausing. To remove selenium images, press [ENTER]: "
fi

echo "*** Shutting down dockerized browsers..."
if [[ "$SELENIUM_HUB" == "0" ]]; then
    for browser in ${BROWSERS}; do
        docker stop "selenium-${browser}-${PROJECT_NAME}"
        docker rm --volumes "selenium-${browser}-${PROJECT_NAME}"
    done
else
    for browser in ${BROWSERS}; do
        docker stop "selenium-node-${browser}-${PROJECT_NAME}"
        docker rm --volumes "selenium-node-${browser}-${PROJECT_NAME}"
    done
    docker stop "selenium-hub-${PROJECT_NAME}"
    docker rm --volumes "selenium-hub-${PROJECT_NAME}"
fi

if [[ "$SAVE_RESULTS" != "0" ]]; then
    echo "*** Test results in ${RESULTS_DIR}"
fi
