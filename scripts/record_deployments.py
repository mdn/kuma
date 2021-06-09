#!/usr/bin/env python
from __future__ import print_function, unicode_literals

import os
import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from datetime import datetime

import requests
from requests.auth import HTTPBasicAuth


# API keys and IDs are set with environment variables rather than on the
# command line, to avoid displaying the key in logs
NR_API_KEY_NAME = "NEW_RELIC_API_KEY"
NR_APP_IDS_NAME = "NEW_RELIC_APP_IDS"
SC_API_KEY_NAME = "SPEEDCURVE_API_KEY"
SC_SIDE_ID_NAME = "SPEEDCURVE_SITE_ID"

# URL patterns to compare two commits
app_compare = {
    "kuma": "https://github.com/mdn/kuma/compare/%s...%s",
    "kumascript": "https://github.com/mdn/kumascript/compare/%s...%s",
}


def deploy_all(
    app,
    nr_api_key=None,
    nr_app_ids=None,
    sc_api_key=None,
    sc_site_id=None,
    from_tag=None,
    to_tag=None,
    verbose=False,
):
    """
    Send deployments to New Relic and SpeedCurve as specified.

    Return is True for success, False for errors.

    Keyword Arguments:
    app: The name of the app, kuma or kumascript
    nr_api_key: A New Relic Admin API key, or None
    nr_app_ids: A list of New Relic application IDs (can be empty)
    sc_api_key: A SpeedCurve API key, or None
    sc_site_id: A SpeedCurve site ID, or None
    from_tag: Commit hash for what was deployed, or None
    to_tag: Commit hash for what is now deployed, or None
    verbose: Print status and responses
    """
    # Create deployment parameters
    if to_tag:
        revision = to_tag
    else:
        ts = datetime.now().replace(microsecond=0)
        revision = ts.isoformat()

    if to_tag and from_tag:
        from_sub_tag = from_tag[:7]
        to_sub_tag = to_tag[:7]
        compare_url = app_compare[app] % (from_sub_tag, to_sub_tag)
        description = compare_url
    else:
        description = None

    # Send New Relic deployments
    passed = True
    count = 0
    nr_app_ids = nr_app_ids or []
    for app_num, app_id in enumerate(nr_app_ids):
        response = deploy_newrelic(app_id, nr_api_key, revision, description)
        if response.status_code == 201:
            success = "SUCCESS"
            count += 1
        else:
            success = "FAILURE"
            passed = False
        if verbose:
            safer_id = "%s_APP_ID_%d" % (app.upper(), app_num)
            content = response.text.replace(app_id, safer_id)
            print(
                "%s (%s): Deployment to New Relic application %s %d: %s"
                % (success, response.status_code, app, app_num, content)
            )

    # Send SpeedCurve deployments
    if sc_api_key and sc_site_id and app == "kuma":
        response = deploy_speedcurve(sc_site_id, sc_api_key, revision, description)
        in_progress = "Deploy already in progress"
        if response.status_code == 200:
            success = "SUCCESS"
            count += 1
        elif response.status_code == 403 and in_progress in response.text:
            # Ignore this error
            success = "IN PROGRESS"
            count += 1
        else:
            success = "FAILURE"
            passed = False
        if verbose:
            safer_id = "SITE_ID_0"
            content = response.text.replace(sc_site_id, safer_id)
            print(
                "%s (%s): Deployment to SpeedCurve site ID %s: %s"
                % (success, response.status_code, sc_site_id, content)
            )

    return bool(count and passed)


def deploy_newrelic(app_id, api_key, revision, description=None):
    """
    Create a deployment in New Relic, categorizing performance.

    https://docs.newrelic.com/docs/apm/new-relic-apm/maintenance/record-deployments

    Keyword Arguments:
    app_id - The application ID, a 8-digit number
    api_key - A New Relic admin API key
    revision - The commit hash or deployment timestamp
    description - A description such as a GitHub comparison URL, or None
    """
    assert app_id, "New Relic Application ID is empty."
    assert api_key, "New Relic API Key is empty."
    url = "https://api.newrelic.com/v2/applications/%s/deployments.json" % app_id
    deployment = {"revision": revision}
    if description:
        deployment["description"] = description

    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    payload = {"deployment": deployment}
    response = requests.post(url, json=payload, headers=headers)
    return response


def deploy_speedcurve(site_id, api_key, note, detail=None):
    """
    Create a deployment in SpeedCurve, kicking off testing.

    https://api.speedcurve.com/#add-a-deploy

    Keyword Arguments:
    site_id - The site ID, a 3- to 6-digit number
    api_key - A SpeedCurve admin API key
    note - The commit hash or deployment timestamp
    detail - A description such as a GitHub comparison URL, or None
    """
    assert site_id, "SpeedCurve Site ID is empty."
    assert api_key, "SpeedCurve API Key is empty."
    url = "https://api.speedcurve.com/v1/deploys"
    payload = {"site_id": site_id, "note": note}
    if detail:
        payload["detail"] = detail

    auth = HTTPBasicAuth(api_key, "x")
    response = requests.post(url, data=payload, auth=auth)
    return response


def get_parser():
    """Create an argument parser."""
    epilog = (
        "Sensitve parameters are read from environment variables, to avoid\n"
        "appearing in logs:\n\n"
        "%s: New Relic API Key\n"
        "%s: New Relic Application ID(s) (8-digit number(s), space separated)\n"
        "%s: SpeedCurve API Key\n"
        "%s: SpeedCurve Site ID (5-digit number)\n"
    ) % (NR_API_KEY_NAME, NR_APP_IDS_NAME, SC_API_KEY_NAME, SC_SIDE_ID_NAME)
    parser = ArgumentParser(
        description="Record a deployment in New Relic",
        formatter_class=RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    parser.add_argument(
        "-a",
        "--app",
        help="Which application is being deployed",
        choices=["kuma", "kumascript"],
        default="kuma",
    )
    parser.add_argument(
        "-f", "--from", dest="from_tag", help="Existing commit at start of deployment"
    )
    parser.add_argument("-t", "--to", help="Commit at the end of deployment")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print responses (obfuscating IDs)"
    )
    return parser


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    from_tag = args.from_tag
    to_tag = args.to
    app = args.app
    nr_api_key = os.environ.get(NR_API_KEY_NAME)
    raw_nr_app_ids = os.environ.get(NR_APP_IDS_NAME, "")
    sc_api_key = os.environ.get(SC_API_KEY_NAME)
    sc_site_id = os.environ.get(SC_SIDE_ID_NAME)

    # Split by commas or whitespace
    nr_app_ids = raw_nr_app_ids.replace(",", " ").split()

    show_help = False
    if nr_app_ids and not nr_api_key:
        show_help = True
        print("*** The environment variable %s is not set. ***" % NR_API_KEY_NAME)
    if sc_site_id and not sc_api_key:
        show_help = True
        print("*** The environment variable %s is not set. ***" % SC_API_KEY_NAME)

    if not (nr_app_ids or sc_site_id):
        show_help = True
        print(
            "*** Neither New Relic application IDs %s or a SpeedCuve"
            "site ID %s is set. ***" % (NR_APP_IDS_NAME, SC_SIDE_ID_NAME)
        )
    if show_help:
        print("")
        parser.print_help()
        sys.exit(1)

    success = deploy_all(
        app,
        nr_api_key,
        nr_app_ids,
        sc_api_key,
        sc_site_id,
        from_tag,
        to_tag,
        verbose=True,
    )
    if not success:
        sys.exit(1)
