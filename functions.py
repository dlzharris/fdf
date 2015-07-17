# functions.py: functions required for field data import gui
import os
import csv
import datetime

# Global constants
LABORATORY = "Field Measurement"
DATA_SOURCE = "Field Data"
# List of available instruments
INSTRUMENTS = ["Hydrolab DS5"]
# List of available field officers
FIELD_STAFF = ["Andy Wise", "Sarah McGeoch"]

# Check validity of the instrument file
def check_file_validity(instrument):
    return

def get_sampling_time(sample_set, station, sample_date):
    # sample_set is a dictionary of samples extracted from the csv
    # with extra attributes
    sample_times = [datetime.datetime.strptime(parse_time_from_string(['Time']), '%H:%M:%S')
                    for s in sample_set if s['Station'] == station and s['Date'] == sample_date]
    # Find the earliest time and convert it to a string
    sampling_time = min(sample_times).strftime('%H:%M:%S')
    return sampling_time

def parse_time_from_string(time_string):
    """
    Takes a string that stores time information (in any format) and parses it
    to the format HH:MM:SS.
    :param time_string: The string that contains time information
    :return: Formatted time string as HH:MM:SS
    """
    # Filter out the digits from the time string"
    time_digits = filter(str.isdigit, time_string)
    # Ensure two-digits used for hour
    if len(time_digits) < 6:
        time_digits = "".join(['0', time_digits])
    # Extract the time components
    hours = time_digits[:2]
    minutes = time_digits[2:4]
    seconds = time_digits[4:6]
    # Concatenate time components with colons
    time_string = hours + ':' + minutes + ':' + seconds
    return time_string

def get_sampling_number(field_dict):
    """
    Return a new sampling number
    :param field_dict: Dictionary created from data imported from the instrument file
    :return: the sampling number used to identify the sample in KiWQM
    """
    # Set the date format and delimiter for the sampling number
    date_format = '%d%m%y'
    sampling_delimiter = "-"
    # Get the required parts of the sampling number from the field_dict
    station = field_dict['Station']
    try:
        date = datetime.datetime.strptime(field_dict['Date'], '%d/%m/%y').strftime(date_format)
    except ValueError:
        date = datetime.datetime.strptime(field_dict['Date'], '%d%m%y').strftime(date_format)
    matrix = field_dict['Matrix']
    # Create the sampling number in format STATION#-DDMMYY-MATRIX
    sampling_number = sampling_delimiter.join([station, date, matrix])
    return sampling_number

def get_fraction_number:
    return

def write_to_csv(data_list, out_file, fieldnames_list):
    """
    Write entire data dictionary to a csv file
    :param data_list: List of dictionaries to be written. Each dictionary
        represents one line of data to be written
    :param out_file: File object to be written to
    :param fieldnames_list: List of fieldnames to be used when writing
    :return: No return value
    """
    writer = csv.DictWriter(out_file, delimiter=',', extrasaction='ignore',
                            fieldnames=fieldnames_list)
    writer.writeheader()
    writer.writerows(data_list)
    return None