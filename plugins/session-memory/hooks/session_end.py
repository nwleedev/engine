#!/usr/bin/env python3
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import narration_pipeline

try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)
narration_pipeline.run("SessionEnd", payload)
sys.exit(0)
