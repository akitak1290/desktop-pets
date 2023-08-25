import os
from pathlib import Path

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
ASSETS_DIR = os.path.join(Path(__file__).absolute().parent.parent, 'assets')