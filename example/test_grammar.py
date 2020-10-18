import sys,logging,os
import os.path

sys.path.append("..")
from GLRParser.main import *
interact(os.path.join("..", "GLRParser", "grm", "main.grmc"))