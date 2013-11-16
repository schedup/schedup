import sys
import os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "../packages"))

from schedup.base import app
import schedup.views

