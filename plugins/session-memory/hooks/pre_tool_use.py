#!/usr/bin/env python3
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from reentry_guard import exit_if_reentrant
import narration_pipeline

exit_if_reentrant()
try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)
narration_pipeline.run("PreToolUse", payload)
sys.exit(0)
