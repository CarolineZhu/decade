#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

if os.environ['DECADE_IP'] and os.environ['DECADE_PORT']:
    import pydevd
    pydevd.settrace(os.environ['DECADE_IP'], port=int(os.environ['DECADE_PORT']), stdoutToServer=True, stderrToServer=True)
