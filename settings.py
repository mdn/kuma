"""
This is just a legacy file to support the new style
settings organization under the old SCL3 deployment
platform.
"""
import os
import platform

CHIEF_REMOTE_HOSTNAME = os.environ.get("CHIEF_REMOTE_HOSTNAME", None)

if CHIEF_REMOTE_HOSTNAME is None:
    # for when the code runs on the webheads after deploy
    IS_STAGE = "stage" in platform.node()
else:
    # when the code runs on the admin node during deploy
    IS_STAGE = CHIEF_REMOTE_HOSTNAME == "developer.allizom.org"

if IS_STAGE:
    from kuma.settings.stage import *  # noqa
else:
    from kuma.settings.prod import *  # noqa
