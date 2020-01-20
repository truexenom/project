import configparser
import os

FILE_PATH = os.path.abspath(__file__)
CONFIG_DIR = os.path.abspath(
    os.path.join(FILE_PATH, os.pardir, os.pardir)
)

config = configparser.ConfigParser()
try:
    config.read_file(open(os.path.join(CONFIG_DIR, 'config.ini')))
except FileNotFoundError:
    print('No config.ini found in{}.'.format(CONFIG_DIR))
    raise