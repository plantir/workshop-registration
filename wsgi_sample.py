# -*- coding: utf-8 -*-
# This file is for PythonAnywhere deployment.
# Copy its contents into the WSGI file that PythonAnywhere creates for you
# (Web tab -> click the /var/log/...wsgi link), replacing USERNAME with your
# PythonAnywhere username in TWO places (path below and nothing else).
# Full step-by-step guide: see "راهنمای انتشار آنلاین.md"

import sys

path = '/home/USERNAME/workshop-registration'
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application
