"""
デバッグエントリポイント
"""

import argparse
import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from parser.debugger.interpreter_debugger import debug_interpreter  # noqa: E402
from parser.debugger.prompter_debugger import debug_prompter, print_yamldict  # noqa: E402
from parser.debugger.the_world_debugger import debug_tw_interpreter  # noqa: E402

parser = argparse.ArgumentParser(
    prog="debug_worker.py",
    description="Debugger for parsing.",
    epilog="ex: python debug_worker.py -m TW",
)
parser.add_argument("-p", "--prompter", action="store_true", help="Prompter")
parser.add_argument("-y", "--yaml", type=str, help="Print normarized YAML")
parser.add_argument("-i", "--interpreter", choices=["W", "T"], default="T", help="Interpreter")
args = parser.parse_args()


if args.prompter:
    debug_prompter()
elif args.yaml:
    print_yamldict(args.yaml)
elif args.interpreter:
    target = args.interpreter
    if target == "W":
        debug_tw_interpreter()
    elif target == "T":
        debug_interpreter()
