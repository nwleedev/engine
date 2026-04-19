#!/usr/bin/env python3
"""
Plugin version bump script.

Usage:
  bump_version.py <plugin> <major|minor|patch|x.y.z>
  bump_version.py <plugin> --check
  bump_version.py --check-all
"""
import argparse
import json
import re
import sys
from pathlib import Path
