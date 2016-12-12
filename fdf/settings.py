import yaml

# Set up global configurations
app_config = yaml.load(open('config/app_config.yaml').read())
column_config = yaml.load(open('config/column_config.yaml').read())
station_list = yaml.load(open('config/station_list.yaml').read())

# Global variable for frozen columns
FROZEN_COLUMNS = 3