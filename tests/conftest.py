import sys
import os

# Add docs directory to sys.path so we can import 'lib' from there
# this allows us to test the code that is actually deployed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../docs')))
