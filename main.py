
import sys
import os 
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append( project_root)


from src.email_agent import *
from utils.utils import *

config = load_config('./config/config.yaml')
print(config['Login'])
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          


