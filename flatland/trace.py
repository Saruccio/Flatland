# File: trace.py
# Date: 05-10-2019
# Author: Saruccio Culmone
#
"""
An attempt to implement a logging module shared among all others
"""

import logging

# create logger
logger = logging.getLogger('vspace')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

# 'application' code
# logger.debug('debug TEST message')
# logger.info('info TEST message')
# logger.warning('warn TEST message')
# logger.error('error TEST message')
# logger.critical('critical TEST message')
