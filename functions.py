# functions.py: functions required for field data import gui
import os
import csv
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


def check_file_validity(instrument_file, instrument_type):
    """
    Checks the validity of the user-selected input file for the selected instrument
    :param instrument_file: Open instrument file object
    :param instrument_type: The instrument from which the file was obtained (str)
    :return: Boolean indicating the validity of the file (True for valid, False for invalid)
    """
    # File validity check for Hydrolab instruments:
    if instrument_type in hydrolab_instruments:
        # Read the file into a list for interrogation
        in_file = list(instrument_file.readlines())
        # Perform the validity tests
        valid_test_1 = True if "Log File Name" in in_file[0] else False
        valid_test_2 = True if "Setup" in in_file[1] else False
        valid_test_3 = True if "Setup" in in_file[2] else False
        valid_test_4 = True if "Recovery" in in_file[len(in_file) - 2] else False
        # If all tests pass (True) then the file is valid, otherwise it is invalid
        if all([valid_test_1, valid_test_2, valid_test_3, valid_test_4]):
            file_valid = True
        else:
            file_valid = False
    # If the instrument type is not found in the available instruments, then
    # the file is invalid.
    else:
        file_valid = False
    return file_valid


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
        # Initialise the date format container
        date_idx = []
        # Open the file
        with open(instrument_file, "rb") as f:
            # Check the validity of the file
            # TODO: Can we do this more elegantly with a custom exception?
            if check_file_validity(f, instrument_type) is not True:
                return None
            # Rewind the file head
            f.seek(0)
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
                # Find the order of date components
                if j == "Date":
                    date_day = re.search('D', units[i]).span()
                    date_month = re.search('M', units[i]).span()
                    date_year = re.search('Y', units[i]).span()
                    date_idx = [date_day, date_month, date_year]
            # Double check the beginning of the data set: it will be row 8, or row 9 if a
            # power loss description is in row 8.
            if "Power" in in_list[data_start_row]:
                data_start_row += 1
            # Find the end of the data set in the file. First, initialise the counter
            n = 1
            for line in in_list:
                # Find if we have reached the end of the data
                if "Recovery" in line:
                    break
                else:
                    n += 1
            # Return to beginning of file
            f.seek(0)
            # Generate a new iterator from the instrument file that contains only the headers
            # and data
            d = islice(f, data_start_row, n - 1)
            # Create the reader object to parse data into dictionaries
            reader = csv.DictReader(d, delimiter=',', skipinitialspace=True, quotechar='"', fieldnames=parameters)
            # Skip the first line, which only contains the units
            data = []
            # Remove empty key:value pairs and add each remaining line to a list
            for line in reader:
                del line['']
                line['Date'] = parse_date_from_string(line['Date'], date_idx)
                # TODO: Send time and date to function for formatting
                data.append(line)
    # If the format for the instrument data file was not found, make the data list None
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
    # Set the time component delimiter
    delimiter = ':'
    # Filter out the digits from the time string
    time_digits = filter(str.isdigit, time_string)
    # Ensure two-digits used for hour
    if len(time_digits) < 6:
        time_digits = "".join(['0', time_digits])
    # Extract the time components
    hours = time_digits[:2]
    minutes = time_digits[2:4]
    seconds = time_digits[4:6]
    # Concatenate time components with delimiter
    time_string = hours + delimiter + minutes + delimiter + seconds
    return time_string


def parse_date_from_string(date_string, date_idx):
    """
    Takes a string that stores date information and parses it to the format DD/MM/YY
    :param date_string: The string that contains date information
    :param date_idx: List of tuples that provide the indices of date components
    in the date_digits extracted from the date string
    :return: Formatted date string as DD/MM/YY
    """
    # Set the date component delimiter
    delimiter = '/'
    # Extract the date components
    day_idx = date_idx[0]
    month_idx = date_idx[1]
    year_idx = date_idx[2]
    # Filter out the digits from the date string
    date_digits = filter(str.isdigit, date_string)
    # Extract the date components
    day = date_digits[day_idx[0]:day_idx[1]]
    month = date_digits[month_idx[0]:month_idx[1]]
    year = date_digits[year_idx[0]:year_idx[1]]
    # Concatenate date components with delimiter
    date_string = day + delimiter + month + delimiter + year
    return date_string


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
