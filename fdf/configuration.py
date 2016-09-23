import yaml

# Set up global configurations
app_config = yaml.load(open('app_config.yaml').read())
column_config = yaml.load(open('column_config.yaml').read())
station_list = yaml.load(open('station_list.yaml').read())