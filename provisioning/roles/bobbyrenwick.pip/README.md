ansible-pip
===========

An ansible role that ensures pip is installed at the version you specify.
It uses `get-pip.py` to install pip.

Role Variables
--------------

- `pip_download_dest` specifies where `get-pip.py` should be downloaded to. Defaults to `/tmp`
- `pip_version` specifies which version of pip you want to install. Defaults to `None`, to install the latest version.
- `python` specifies what Python executable to use.  Defaults to `python`.
- `pip` specifies what pip executable to check and use.  Defaults to `pip`.
