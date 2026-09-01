#!/usr/bin/env python3
import sys
import os
import subprocess

# Locate emitter.py from package or fallback
emitter_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "agy_traffic_light", "emitter.py"))
if os.path.exists(emitter_path):
    proc = subprocess.Popen([sys.executable, emitter_path] + sys.argv[1:], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
    proc.wait()
    sys.exit(proc.returncode)
else:
    # Direct fallback if installed via pip
    from agy_traffic_light.emitter import main
    main()
