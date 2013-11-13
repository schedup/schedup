import sys
import os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "../google-api-python-client-1.2"))

from schedup.base import app
import schedup.views

