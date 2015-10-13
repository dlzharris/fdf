"""
Module: functions.py
Provides the functions necessary for data manipulations and verification
of data used in KiWQM Field Data Formatter to generate a valid
import file for KiWQM.

Author: Daniel Harris
Title: Data & Procedures Officer
Organisation: DPI Water
Date modified: 13/10/2015

Functions:
check_file_validity: check the validity of the instrument file
load_instrument_file: load the instrument file to memory
load_manual_entry: prepare an empty dictionary for manual data entry
parse_time_from_string: format a time string
parse_date_from_string: format a date string
get_sampling_time: get the sampling time from a group of samples
get_sampling_number: generate the sampling number for a sample
get_fraction_number: generate the field fraction number for a sample
get_new_dict_key: update the dictionary key to a friendlier version
get_parameter_unit: get the parameter code for a variable
get_column_title: get the display name for a required field
get_parameter_name: get the display name for a parameter
check_data_completeness: check that required fields are not empty
check_data_zero_values: check that parameter values are not zero
prepare_dictionary: transform the data to parameter-oriented format
write_to_csv: write the data to a dictionary for import to KiWQM
"""
import csv
import copy
import datetime
from itertools import islice
import re
import globals


def check_file_validity(instrument_file, instrument_type):
    """
    Check the validity of the user-selected input file for the selected instrument
    :param instrument_file: Open instrument file object
    :param instrument_type: The instrument from which the file was obtained (str)
    :return: Boolean indicating the validity of the file (True for valid, False for invalid)
    """
    # File validity check for Hydrolab instruments:
    if instrument_type in globals.hydrolab_instruments:
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
    Read the provided csv file, parses and loads the file to memory
    :param instrument_file: The csv file to be loaded
    :param instrument_type: The instrument from which the file was obtained
    :return: List of dictionaries, with each dictionary representing a
    different measurement point
    """
    # File readings procedure for Hydrolab instruments:
    if instrument_type in globals.hydrolab_instruments:
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
            # Find the end of the data set in the file. First, initialise the counter to
            # beginning of data set.
            n = data_start_row
            for line in in_list[data_start_row:]:
                # Find if we have reached the end of the data
                if "Recovery" in line or "Power" in line:
                    break
                else:
                    n += 1
            # Return to beginning of file
            f.seek(0)
            # Generate a new iterator from the instrument file that contains only the headers
            # and data
            d = islice(f, data_start_row, n)
            # Create the reader object to parse data into dictionaries and the data container list
            reader = csv.DictReader(d, delimiter=',', skipinitialspace=True, quotechar='"', fieldnames=parameters)
            data = []
            # Change the keys to our standard key values and remove items that are not relevant
            for line in reader:
                new_line = {}
                for item in line:
                    try:
                        new_line[get_new_dict_key(item)] = line[item]
                    except KeyError:
                        pass
                # Format the date and time correctly
                new_line['date'] = parse_date_from_string(new_line['date'], date_idx)
                new_line['sample_time'] = parse_time_from_string(new_line['sample_time'])
                # Add the extra items we'll need access to later on
                new_line['event_time'] = ""
                new_line['sampling_number'] = ""
                new_line['replicate_number'] = ""
                new_line['sample_cid'] = ""
                new_line['sample_matrix'] = ""
                new_line['sample_type'] = ""
                new_line['mp_number'] = ""
                new_line['location_id'] = ""
                new_line['station_number'] = ""
                new_line['calibration_record'] = ""
                new_line['sampling_officer'] = ""
                new_line['sample_collected'] = ""
                new_line['depth_lower'] = ""
                new_line['sampling_comment'] = ""
                new_line['sampling_instrument'] = ""
                new_line['gauge_height'] = ""
                new_line['turbidity'] = ""
                # Add the new updated dictionary to our list
                data.append(new_line)
    # If the format for the instrument data file was not found, make the data list None
    else:
        data = None
    # Return the list
    return data


def load_manual_entry(number_lines):
    """
    Create a dictionary with empty items for use in the manual entry screen.
    :param number_lines:
    :return:
    """
    empty_data = []
    for i in range(1, number_lines):
        new_line = {
            'checked': "",
            'mp_number': "",
            'station_number': "",
            'sampling_number': "",
            'date': "",
            'sample_time': "",
            'location_id': "",
            'sample_cid': "",
            'replicate_number': "",
            'sample_matrix': "",
            'sample_type': "",
            'collection_method': "",
            'calibration_record': "",
            'sampling_instrument': "",
            'sampling_officer': "",
            'event_time': "",
            'sample_collected': "",
            'depth_upper': "",
            'depth_lower': "",
            'do': "",
            'do_sat': "",
            'ph': "",
            'temp_c': "",
            'conductivity_uncomp': "",
            'turbidity': "",
            'water_depth': "",
            'gauge_height': "",
            'sampling_comment': ""}
        empty_data.append(new_line)
    return empty_data


def parse_time_from_string(time_string):
    """
    Take a string that stores time information (in any format) and parse it
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
    seconds = "00"  # This strips out the seconds component. To keep the seconds, use time_digits[4:6]
    # Concatenate time components with delimiter
    time_string = hours + delimiter + minutes + delimiter + seconds
    return time_string


def parse_date_from_string(date_string, date_idx):
    """
    Take a string that stores date information and parse it to the format DD/MM/YY
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
    day = date_digits[day_idx[0]:day_idx[1] + 1]
    month = date_digits[month_idx[0]:month_idx[1] + 1]
    year = date_digits[year_idx[0]:year_idx[1] + 1]
    # Concatenate date components with delimiter
    date_string = day + delimiter + month + delimiter + year
    return date_string


def get_sampling_time(sample_set, station, sample_date):
    """
    Find the sampling time for a set of samples collected at the same station
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
    sample_times = [datetime.datetime.strptime(parse_time_from_string(s['sample_time']), '%H:%M:%S')
                    for s in sample_set if s['station_number'] == station and s['date'] == sample_date]
    # Find the earliest time and convert it to a string
    sampling_time = min(sample_times).strftime('%H:%M:%S')
    return sampling_time


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
    station = field_dict['station_number']
    try:
        date = datetime.datetime.strptime(field_dict['date'], '%d/%m/%y').strftime(date_format)
    except ValueError:
        date = datetime.datetime.strptime(field_dict['date'], '%d%m%y').strftime(date_format)
    matrix = field_dict['sample_matrix']
    sample_type = field_dict['sample_type']
    # Create the sampling number in format STATION#-DDMMYY[-MATRIX]
    if matrix in ["SED", "PDMS"]:
        sampling_number = sampling_delimiter.join([station, date, matrix])
    elif sample_type in ["QR", "QB", "QT"]:
        sampling_number = sampling_delimiter.join([station, date, sample_type])
    else:
        sampling_number = sampling_delimiter.join([station, date])
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
    sampling_number = field_dict['sampling_number']
    try:
        delimiter_position = sampling_number.index("-", 9)
    except ValueError:
        delimiter_position = None
    # Create the fraction number in form STATION#-DDMMYY_(CID+LOCATION ID)_F
    fraction_number = sampling_number[:delimiter_position] + fraction_delimiter + str(field_dict['sample_cid']) +\
        str(field_dict['location_id']) + fraction_delimiter + "F"
    return fraction_number


def get_new_dict_key(key):
    """
    Generate a new "friendly" dictionary key for the variables loaded in load_instrument_file.
    :param key: The original dictionary key
    :return: The new dictioanry key
    """
    new_keys = {
        "Date": "date",
        "Time": "sample_time",
        "TempC": "temp_c",
        "TempF": "temp_f",
        "Dep25": "depth_upper",
        "LDO%": "do_sat",
        "LDO": "do",
        "pH": "ph",
        "SpCond": "conductivity_uncomp",
        "IBVSvr4": "internal_voltage",
        "BPSvr4": "barometric_pressure",
        "PYC": "pyc",
        "PYCV": "pyc_v",
        "CHL": "chlorophyll_a",
        "CHLV": "chlorophyll_a_v"}
    return new_keys[key]


def get_parameter_unit(key):
    """
    Get the unit code as used in KiWQM for use in prepare_dictionary.
    :param key: The variable name.
    :return: The unit code for the variable.
    """
    units = {
        "conductivity_uncomp": "MISC",
        "do": "MGL",
        "do_sat": "WISKI_PSAT",
        "gauge_height": "M",
        "ph": "SCAL",
        "temp_c": "DEGC",
        "turbidity": "NTU",
        "water_depth": "M"}
    return units[key]


def get_column_title(key):
    """
    Get the column title used in the GUI ObjectListView based on the
    original dictionary key. Used in check_data_completeness to
    tell the user which required columns have been left empty.
    """
    titles = {
        'mp_number': "MP#",
        'station_number': "Station#",
        'date': "Date",
        'sample_matrix': "Matrix",
        'sample_type': "Sample type",
        # 'sampling_reason',
        'sampling_officer': "Sampling officer",
        'location_id': "Loc#",
        'sample_cid': "Seq#",
        'sample_time': "Time",
        'depth_upper': "Depth (upper)"}
    return titles[key]


def get_parameter_name(key):
    """
    Get the display name of the dictionary key. Used in
    check_data_zero_values to tell the user which parameters have
    values of zero.
    """
    param_names = {
        "do": "DO (mg/L)",
        "do_sat": "DO (% sat)",
        "ph": "pH",
        "temp_c": "Temp (deg C)",
        "conductivity_uncomp": "EC (uS/cm)",
        "turbidity": "Turbidity (NTU)"}
    return param_names[key]


def get_replicate_number(rep_code):
    """
    Get the replicate number used in KiWQM based on the sample type code.
    """
    replicate_numbers = {
        "P": 0,
        "RE": 1,
        "DU": 1,
        "TR": 2,
        "QR": 0,
        "QB": 0,
        "QT": 0}
    return replicate_numbers[rep_code]


def check_data_completeness(data_list):
    """
    Check the data entered by the user for completeness. This is used
    to alert the user to the presence of any required fields that have
    empty values prior to exporting.
    :param data_list: The list of dictionaries to be checked.
    :return: A list of column titles of incomplete fields.
    """
    # Create container for list of incomplete required fields
    incomplete_fields = []
    # Loop through required fields and check each item in the field for completeness
    for field in globals.REQUIRED_FIELDS:
        # Extract the values with the given key
        column = (i[field] for i in data_list)
        for item in column:
            # If we have an incomplete item in a required field
            # add the item to our incomplete list and
            if item == "":
                incomplete_fields.append(get_column_title(field))
                break
            else:
                pass
    return incomplete_fields


def check_data_zero_values(data_list):
    """
    Check the data entered by the user for any variable with a value
    of zero. This is used to alert the user to the presence of these
    values prior to exporting.
    :param data_list: The list of dictionaries to be checked.
    :return: A list of column titles with zero values.
    """
    # Create container for list of incomplete required fields
    zero_value_fields = []
    # Loop through required fields and check each item in the field for completeness
    for field in globals.NON_ZERO_FIELDS:
        # Extract the values with the given key
        column = (i[field] for i in data_list)
        for item in column:
            # If we have an incomplete item in a required field
            # add the item to our incomplete list.
            if item == "0":
                zero_value_fields.append(get_parameter_name(field))
                break
            else:
                pass
    return zero_value_fields


def prepare_dictionary(data_list):
    """
    Transform the orientation of the field data to "parameter oriented"
    as used in KiWQM. The original dictionary orientation is one sample
    per list entry, while the new orientation is one sample value per
    list entry.
    :param data_list: The list of dictionaries to be transformed.
    :return: A list of dictionaries containing data in "parameter
    oriented" format.
    """
    # Create the container for the parameter-oriented data
    data_list_param_oriented = []
    # Set the datetime format for the entry datetime
    dt_format = '%Y-%m-%d %H:%M:%S'
    # Each item in the list is a single dictionary representing a single sample
    for sample in data_list:
        # Get the sampling event time and replicate number
        sample['event_time'] = get_sampling_time(data_list, sample['station_number'], sample['date'])
        sample['replicate_number'] = get_replicate_number(sample['sample_type'])
        # Assign the static fraction information to the sample
        sample['fraction_lab_shortname'] = "FLD"                                         # Static text
        sample['fraction_data_source'] = "Field Data"                                    # Static text
        sample['fraction_number'] = get_fraction_number(sample)                          # Calculated value
        sample['fraction_entry_datetime'] = datetime.datetime.now().strftime(dt_format)  # Current time
        # If more than one replicate per sampling, increment replicate number on export
        rep_depth_tolerance = 0.15
        min_depth = float(sample['depth_upper']) - rep_depth_tolerance
        max_depth = float(sample['depth_upper']) + rep_depth_tolerance
        reps_in_sampling = [r['sample_time'] for r in data_list
                            if r['sampling_number'] == sample['sampling_number']
                            and r['sample_type'] == sample['sample_type']
                            and min_depth <= float(r['depth_upper']) <= max_depth]
        if len(reps_in_sampling) > 1:
            sorted(reps_in_sampling, key=lambda x: x[0])
            sample_idx = reps_in_sampling.index(sample['sample_time'])
            sample['replicate_number'] += sample_idx
        # Transform the data to paremeter-oriented
        for param in globals.PARAMETERS:
            # Store sample metadata for reuse. We use deepcopy here so we create
            # a new object from the sample data.
            sample_param_oriented = copy.deepcopy(sample)
            try:
                # Create dictionary items for parameter, value and unit
                sample_param_oriented["parameter"] = param
                sample_param_oriented["value"] = sample_param_oriented.pop(param)
                sample_param_oriented["units"] = get_parameter_unit(param)
                # If the value is empty, skip to the next value
                if sample_param_oriented["value"] != "":
                    # Add the dictionary to the parameter-oriented container
                    data_list_param_oriented.append(sample_param_oriented)
                else:
                    pass
            # If the parameter wasn't found in the list, skip to the next one
            except KeyError:
                pass
    return data_list_param_oriented


def write_to_csv(data_list, out_filepath, fieldnames_list):
    """
    Write a list of data dictionaries to a csv file
    :param data_list: List of dictionaries to be written. Each dictionary
        represents one line of data to be written
    :param out_file: File object to be written to
    :param fieldnames_list: List of fieldnames to be used when writing
    :return: No return value
    """
    with open(out_filepath, 'wb') as f:
        writer = csv.DictWriter(f, delimiter=',', extrasaction='ignore',
                                fieldnames=fieldnames_list)
        writer.writeheader()
        writer.writerows(data_list)
    return None
