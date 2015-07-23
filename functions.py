# functions.py: functions required for field data import gui
import os
import csv
import codecs
import datetime
from itertools import islice
import re

# Global constants
LABORATORY = "Field Measurement"
DATA_SOURCE = "Field Data"
# List of available instruments
INSTRUMENTS = ["Hydrolab DS5", "Hydrolab MS4", "Hydrolab MS5"]
# List of available field officers
FIELD_STAFF = ["Andy Wise", "Sarah McGeoch"]
# Instrument names as variables
hydrolab_instruments = ["Hydrolab DS5", "Hydrolab MS4", "Hydrolab MS5"]


# TODO: Check file validity function
# Check validity of the instrument file
def check_file_validity(instrument, instrument_type):
    return


def load_instrument_file(instrument_file, instrument_type):
    """
    Reads the provided csv file, parses and loads the file to memory
    :param instrument_file: The csv file to be loaded
    :param instrument_type: The instrument from which the file was obtained
    :return: List of dictionaries, with each dictionary representing a
    different measurement point
    """
    # File readings procedure for Hydrolab instruments:
    if instrument_type in hydrolab_instruments:
        # Set the header and data start rows
        header_start_row = 5
        data_start_row = 8
        # Open the file
        with open(instrument_file, "rb") as f:
            # Read the file into a list for initial interrogation and processing. We will
            # read the data portion into a dictionary further below.
            in_list = list(f.readlines())
            # The hydrolab data headers are made up of two rows: one for the parameter and one
            # for the unit. Because temperature is reported more than once in different units,
            # we need to parse temperature with the respective unit (deg celsius or fahrenheit)
            # to make it unique.
            parameters = in_list[header_start_row].replace('"', '').split(',')
            units = in_list[header_start_row + 1].replace('"', '').split(',')
            for i, j in enumerate(parameters):
                if j == "Temp":
                    temp_match = re.search('[CF]', units[i])
                    parameters[i] = "Temp" + temp_match.group()
            # Find the end of the data set in the file. First, initialise the counter
            n = 0
            for line in in_list:
                n += 1
                # Find if we have reached the end of the data
                if "Recovery" in line:
                    break
            # Return to beginning of file
            f.seek(0)
            # Generate a new iterator from the instrument file that contains only the headers
            # and data
            d = islice(f, data_start_row, n - 1)
            # Create the reader object to parse data into dictionaries
            reader = csv.DictReader(d, delimiter=',', skipinitialspace=True, quotechar='"', fieldnames=parameters)
            # Skip the first line, which only contains the units
            reader.next()
            data = []
            # Add each remaining line to a list
            for line in reader:
                data.append(line)
    else:
        data = None
    # Return the list
    return data


def get_sampling_time(sample_set, station, sample_date):
    """
    Finds the sampling time for a set of samples collected at the same station
    on a given date. The sampling time is different from the sample time and
    is used in KiWQM to collect related samples into a group (depth profiles or
    primary and replicate samples).
    :param sample_set: The entire set of field data from the instrument as a
    dictionary, with extra metadata such as station already added in.
    :param station: String of the station number to be queried
    :param sample_date: String of the date used for the query
    :return: The sampling time used to identify samplings in KiWQM.
    """
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
    :return: The sampling number used to identify the sample in KiWQM
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


def get_fraction_number(field_dict):
    """
    Return the fraction number for the field sample.
    :param field_dict: Dictionary created from data imported from the instrument file.
    :return: The fraction number used to identify the results as field results (as opposed
    to lab results) in KiWQM.
    """
    # Set the delimiter to be used in the fraction number
    fraction_delimiter = "_"
    # Get the sampling number and strip out the matrix code from the end
    # Using 9 as the starting point for str.find allows us to skip over the first hyphen.
    sampling_number = get_sampling_number(field_dict)
    delimiter_position = sampling_number.find("-", 9)
    # Create the fraction number in form STATION#-DDMMYY_(CID+LOCATION ID)_F
    fraction_number = sampling_number[:delimiter_position] + fraction_delimiter + str(field_dict['CID']) +\
        str(field_dict['Location ID']) + fraction_delimiter + "F"
    return fraction_number


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
