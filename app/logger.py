import os
import logging

# Create the .logs directory if it doesn't exist
if not os.path.exists('.logs'):
    os.makedirs('.logs')

# Set up logging configuration
logging.basicConfig(
    filename='.logs/app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)