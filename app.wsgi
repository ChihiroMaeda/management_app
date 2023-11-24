import sys

import logging
# To output apache logs
logging.basicConfig(stream = sys.stderr)

sys.path.insert(0, '/var/www/html/managementapp_flask')

from app import app as application