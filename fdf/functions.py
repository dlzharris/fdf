"""
Module: functions.py
Provides the functions necessary for data manipulations and verification
of data used in KiWQM Field Data Formatter to generate a valid
import file for KiWQM.

Author: Daniel Harris
Title: Data & Procedures Officer
Organisation: DPI Water
Date modified: 13/12/2016

External dependencies: dateutil

Exceptions:
DatetimeError: Custom exception for date and time format errors
ValidityError: Custom exception for file format errors

Functions:
check_file_validity: check the validity of the instrument file
get_column_number: get the column number for the table instance of a
    parameter or metadata field
get_fraction_number: generate the field fraction number for a sample
get_mga_coordinates: get the MGA94 easting and northing from lat/lon coordinates
get_new_dict_key: update the dictionary key to a friendlier version
get_replicate_number: get the replicate number corresponding to the sample type
get_sampling_time: get the sampling time for a group of samples
load_instrument_file: load the instrument file to memory
lord2lorl: transform data from a list of dictionaries to a list of lists
lorl2lord: transform data from a list of lists to a list of dictionaries
parse_datetime_from_string: parse a datetime object from a string representation
prepare_dictionary: transform the data set to a list of dictionaries
resource_path: get absolute path to resource for PyInstaller
write_to_csv: write the data to a csv file for import to KiWQM
"""

# Standard library imports
import codecs
import copy
import csv
import datetime
from itertools import islice
import os
import re
import sys

# Related third party imports
import chardet
from dateutil.parser import parse
from utm import from_latlon

# Local application imports
from settings import app_config, column_config, station_list

__author__ = 'Daniel Harris'
__date__ = '09 March 2017'
__email__ = 'daniel.harris@dpi.nsw.gov.au'
__status__ = 'Production'
__version__ = '1.0.1'


###############################################################################
# Custom exception classes
###############################################################################
class DatetimeError(Exception):
    """
    Custom exception for date format errors
    """
    pass


class ValidityError(Exception):
    """
    Custom exception for file format errors
    """
    pass


###############################################################################
# Helper functions
###############################################################################
def check_file_validity(instrument_file, file_source):
    """
    Checks the validity of the user-selected input file for the selected instrument
    :param instrument_file: Open instrument file object
    :param file_source: The instrument from which the file was obtained (str)
    :return: Boolean indicating the validity of the file (True for valid, False for invalid)
    """
    try:
        in_file = instrument_file.readlines()
    except UnicodeError:
        raise ValidityError

    # File validity check for Hydrolab instruments:
    if file_source in app_config['sources']['hydrolab']:
        valid_test_1 = True if "Log File Name" in in_file[0] else False
        valid_test_2 = True if "Setup" in in_file[1] else False
        valid_test_3 = True if "Setup" in in_file[2] else False
        valid_test_4 = True if "Recovery" in in_file[len(in_file) - 2] else False
        # If all tests pass (True) then the file is valid, otherwise it is invalid
        if all([valid_test_1, valid_test_2, valid_test_3, valid_test_4]):
            file_valid = True
        else:
            file_valid = False

    # File validity check for YSI instruments:
    elif file_source in app_config['sources']['ysi']:
        if file_source == 'EXO (KOR file)':
            file_valid = True if "KOR Export File" in in_file[0] else False
        elif file_source == 'EXO (instrument)':
            if 'sep' in in_file[0]:
                file_valid = True if "Date" in in_file[1] else False
            else:
                file_valid = True if "Date" in in_file[0] else False

    # If the instrument type is not found in the available instruments, then
    # the file is invalid.
    else:
        file_valid = False

    # Raise an exception if the file is not valid
    if not file_valid:
        raise ValidityError
    else:
        return file_valid


def load_instrument_file(instrument_file, file_source, date_format):
    """
    Read the provided csv file, parses and loads the file to memory
    :param instrument_file: The csv file to be loaded
    :param file_source: The instrument from which the file was obtained
    :return: List of dictionaries, with each dictionary representing a
    different measurement point or time
    """
    if file_source == '':
        raise ValidityError

    # Set the header and data start rows and file encoding
    if file_source in app_config['sources']['hydrolab']:
        header_start_row = 5
        data_start_row = 8
        encoding = 'latin-1'
    elif file_source in app_config['sources']['ysi']:
        if file_source == 'EXO (KOR file)':
            header_start_row = 22
            data_start_row = 23
            encoding = 'latin-1'
        elif file_source == 'EXO (instrument)':
            header_start_row = 0
            data_start_row = 1
            encoding = 'utf16'

    charset = chardet.detect(open(instrument_file, "rb").read())
    encoding = charset['encoding']
    bom = u'\ufeff'  # Byte Order Mark for utf16-le

    with codecs.open(instrument_file, "rb", encoding=encoding) as f:
        # Check the validity of the file
        try:
            check_file_validity(f, file_source)
        except ValidityError:
            raise ValidityError

        # Rewind the file head
        f.seek(0)

        # Read the file into a list for initial interrogation and processing. We will
        # read the data portion into a dictionary further below.
        in_list = list(f.readlines())

        # In EXO with updated firmware (Current March 2017), some data files contain
        # an extra line with the separator value. We check if this is the case and
        # increment the header start row.
        if file_source == 'EXO (instrument)' and 'sep' in in_list[0]:
            separator = in_list[0][in_list[0].find('=') + 1]
            header_start_row += 1
        else:
            separator = ','

        parameters = in_list[header_start_row].replace('"', '').replace(bom, '').replace('\r\n', '').split(separator)

        if file_source in app_config['sources']['hydrolab']:
            # The hydrolab data headers are made up of two rows: one for the parameter and one
            # for the unit. Because temperature is reported more than once in different units,
            # we need to parse temperature with the respective unit (deg celsius or fahrenheit)
            # to make it unique.
            units = in_list[header_start_row + 1].replace('"', '').split(',')
            for i, j in enumerate(parameters):
                if j == "Temp":
                    temp_match = re.search('[CF]', units[i])
                    parameters[i] = "Temp" + temp_match.group()
            # Double check the beginning of the data set: it will be row 8, or row 9 if a
            # power loss description is in row 8.
            if "Power" in in_list[data_start_row]:
                data_start_row += 1

        elif file_source in app_config['sources']['ysi']:
            if file_source == 'EXO (KOR file)':
                # Parse out parameter names from potentially
                # ambiguous parameters.
                for i, j in enumerate(parameters):
                    p = j.split(' ', 1)

                    if p[0] == "Time":
                        if p[1] == "(HH:MM:SS)":
                            parameters[i] = "Time"
                        else:
                            parameters[i] = "TimeFraction"
                        continue

                    elif p[0] == "Temp":
                        temp_match = re.search('[CF]', j)
                        parameters[i] = "Temp" + temp_match.group()
                        continue

                    elif p[0] == "ODO":
                        if p[1] == "% sat":
                            parameters[i] = "ODO%"
                        elif p[1] == "mg/L":
                            parameters[i] = p[0]
                        else:
                            parameters[i] = "ODO_EU"
                        continue

                    elif p[0] == "pH":
                        try:
                            if p[1] == "mV":
                                parameters[i] = "pHmV"
                        except IndexError:
                            parameters[i] = p[0]
                        continue

                    elif p[0] == "ORP":
                        if p[1] == "mV":
                            parameters[i] = p[0]
                        else:
                            parameters[i] = "ORPRaw"
                        continue

                    elif p[0] == "DEP":
                        parameters[i] = "Depth"
                    else:
                        parameters[i] = p[0]

            elif file_source == 'EXO (instrument)':
                # Parse out parameter names from potentially
                # ambiguous parameters.
                degree_sign = u'\N{DEGREE SIGN}'
                for i, j in enumerate(parameters):
                    p = j.split(' ', 1)

                    if degree_sign in p[0]:
                        temp_match = re.search('[CF]', j)
                        parameters[i] = "Temp" + temp_match.group()
                        continue

                    elif p[0] == "DO":
                        if p[1] == "%":
                            parameters[i] = "ODO%"
                        elif p[1] == "mg/L":
                            parameters[i] = "ODO"
                        else:
                            parameters[i] = "ODO_EU"
                        continue

        # If the format for the instrument data file was not found,
        # make the data list None
        else:
            return None

        # Find the end of the data set in the file. First, initialise the counter to
        # beginning of data set.
        n = data_start_row
        for line in in_list[data_start_row:]:
            # Find if we have reached the end of the data
            if '\x00' in line:
                break
            else:
                n += 1
        # Return to beginning of file
        f.seek(0)
        # Generate a new iterator from the instrument file that contains only the headers
        # and data
        d = islice(f, data_start_row, n)
        # Strip any trailing commas (generated in Excel) from the end of the line)
        ls = []
        conductivity_is_compensated = False
        for i in d:
            i = i.replace(",\r\n", "")
            i = i.replace(u'\xb0', "")
            # Find if Hydrolab is using compensated or uncompensated conductivity
            if "~" in i:
                conductivity_is_compensated = True
            ls.append(i)
        # Create the reader object to parse data into dictionaries and the data container list
        reader = csv.DictReader(
            ls, delimiter=',', skipinitialspace=True,
            quotechar='"', fieldnames=parameters, restval=u""
        )
        # Initialise the data container
        data = []
        # Grab the date format
        dt_dayfirst = True if date_format[:2] == 'dd' else False
        dt_yearfirst = True if date_format[:2] == 'YY' else False
        # Change the keys to our standard key values and remove items that are not relevant
        for line in reader:
            try:
                sample_dt = parse_datetime_from_string(line['Date'], line['Time'], dt_dayfirst, dt_yearfirst)
            except DatetimeError:
                continue

            # Initialise the dictionary for the line of data
            new_line = {}

            # Populate the dictionary with the data from the data file
            for item in line:
                try:
                    new_line[get_new_dict_key(item)] = float(line[item])
                    if all([file_source in app_config['sources']['hydrolab'],
                            conductivity_is_compensated, item == "SpCond"]):
                        new_line['conductivity_uncomp'] = new_line.pop('conductivity_comp')
                except ValueError:
                    try:
                        new_line[get_new_dict_key(item)] = line[item]
                    except (KeyError, TypeError):
                        pass
                except (KeyError, TypeError):
                    pass

            # Set the instrument
            if 'EXO' in file_source:
                new_line['sampling_instrument'] = 'EXO'
            elif 'Hydrolab' in file_source:
                new_line['sampling_instrument'] = file_source
            else:
                new_line['sampling_instrument'] = ""

            # Format the date and time correctly
            new_line['date'] = sample_dt.strftime(app_config['datetime_formats']['date']['display'])
            new_line['sample_time'] = sample_dt.strftime(app_config['datetime_formats']['time']['display'])

            # Update station number
            try:
                # Change station number to a string if it has been coerced to a float
                try:
                    new_line['station_number'] = str(int(new_line['station_number']))
                except ValueError:
                    pass
                if new_line['station_number'].split(' ', 1)[0] in station_list:
                    station_number = new_line['station_number'].split(' ', 1)[0]
                else:
                    station_number = ""
            except KeyError:
                station_number = ""
            new_line['station_number'] = station_number

            # Update sampler name
            try:
                sampling_officer_column = get_column_number('sampling_officer')
                if new_line['sampling_officer'] in column_config[sampling_officer_column]['list_items']:
                    sampling_officer = new_line['sampling_officer']
                else:
                    sampling_officer = ""
            except KeyError:
                sampling_officer = ""
            new_line['sampling_officer'] = sampling_officer

            # Update sample location coordinates
            try:
                new_line['easting'], new_line['northing'], new_line['map_zone'] = \
                    get_mga_coordinates(new_line['latitude'], new_line['longitude'])
            except KeyError:
                pass

            # Add the extra items we'll need access to later on
            for item in column_config:
                if column_config[item]['name'] not in new_line:
                    new_line[column_config[item]['name']] = ""

            # Add the new updated dictionary to our list
            data.append(new_line)

    # Return the list
    return data


def lord2lorl(lord, colkeys):
    """
    Converts a list of dicts where each dict is a row (lord) to
    a list of lists where each inner list is a row (lorl).
    Adapted from tabular.py package, available from
    http://www.saltycrane.com/blog/2007/12/tabular-data-structure-conversion-in-python/
    :param lord: list of dictionaries to be parsed
    :param colkeys: list of column keys
    """
    lists = [[row[key] for key in colkeys if key in row] for row in lord]
    return lists


def lorl2lord(lorl, colkeys):
    """
    Converts a list of lists where each inner list is a row (lorl) to
    a list of dicts where each dict is a row (lord).
    Adapted from tabular.py package, available from
    http://www.saltycrane.com/blog/2007/12/tabular-data-structure-conversion-in-python/
    :param lorl: list of lists to be parsed
    :param colkeys: list of column keys
    """
    return [dict(zip(colkeys, row)) for row in lorl]


def get_column_number(column_name):
    """
    Gets the column number for a given column name
    :param column_name: Name of column as defined in column_config.yaml
    :return: Integer representing the column number (from left to right) as
    it appears in the table instance.
    """
    return [k for k, v in column_config.iteritems() if v['name'] == column_name][0]


def get_fraction_number(field_dict):
    """
    Return the fraction number for the field sample.
    :param field_dict: Dictionary created from data imported from the instrument file.
    :return: The fraction number used to identify the results as field results (as opposed
    to lab results) in KiWQM.
    """
    # Set the delimiter to be used in the fraction number
    fraction_delimiter = "_"
    # Get the sampling number and strip out the matrix code from the end if it is there
    # Using 9 as the starting point for str.index allows us to skip over the first hyphen.
    sampling_number = field_dict['sampling_number']
    try:
        delimiter_position = sampling_number.index("-", 9)
    except ValueError:
        delimiter_position = None
    # Create the fraction number in form STATION#-DDMMYY_(CID+LOCATION ID)_F
    fraction_number = sampling_number[:delimiter_position] \
                      + fraction_delimiter \
                      + str(field_dict['sample_cid']) \
                      + str(field_dict['location_id']) \
                      + fraction_delimiter \
                      + "F"
    return fraction_number


def get_mga_coordinates(latitude, longitude):
    """
    Return the easting, northing and map zone in MGA94 system for
    a given set of latitude and longitude coordinates. Note that
    the from_latlon function returns four values - we are only
    returning three.
    :param latitude: Latitude as GDA94
    :param longitude: Longitude as GDA94
    :return: Tuple as (easting, northing, map_zone)
    """
    return from_latlon(latitude, longitude)[:3]


def get_new_dict_key(key):
    """
    Generate a new "friendly" dictionary key for the variables loaded in load_instrument_file.
    :param key: The original dictionary key
    :return: The new dictionary key
    """
    new_keys = {
        "Date": "date",  # hydrolab & YSI
        "Time": "sample_time",  # hydrolab & YSI
        "TempC": "temp_c",  # hydrolab & YSI
        "TempF": "temp_f",  # hydrolab & YSI
        "Dep25": "depth_upper",  # hydrolab
        "LDO%": "do_sat",  # hydrolab
        "LDO": "do",  # hydrolab
        "pH": "ph",  # hydrolab & YSI
        "SpCond": "conductivity_comp",  # hydrolab & YSI
        "IBVSvr4": "internal_voltage",  # hydrolab
        "BPSvr4": "barometric_pressure",  # hydrolab
        "PYC": "pyc",  # hydrolab
        "PYCV": "pyc_v",  # hydrolab
        "CHL": "chlorophyll_a",  # hydrolab
        "CHLV": "chlorophyll_a_v",  # hydrolab
        "TDS": "tds",  # YSI
        "ODO%": "do_sat",  # YSI
        "ODO": "do",  # YSI
        "ORP": "orp",  # YSI
        "Depth": "depth_upper",  # YSI
        "Baro": "barometric_pressure",  # YSI
        "Site": "station_number",  # YSI
        "User ID": "sampling_officer",  # YSI
        "SPC-uS/cm": "conductivity_comp",  # YSI
        "C-uS/cm": "conductivity_uncomp",  # YSI
        "DEP m": "depth_upper",  # YSI
        "mmHg": "barometric_pressure",  # YSI
        "Lat": "latitude",  # YSI
        "Lon": "longitude"  # YSI
    }
    return new_keys[key]


def get_replicate_number(rep_code):
    """
    Get the replicate number used in KiWQM based on the sample type code.
    """
    replicate_numbers = {
        "P": 0,
        "R": 1,
        "D": 1,
        "T": 2,
        "QR": 0,
        "QB": 0,
        "QT": 0}
    return replicate_numbers[rep_code]


def get_sampling_time(sample_set, station, sample_date, date_format):
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
    dt_dayfirst = True if date_format[:2] == 'dd' else False
    dt_yearfirst = True if date_format[:2] == 'YY' else False
    sample_times = [parse_datetime_from_string(s['date'], s['sample_time'], dt_dayfirst, dt_yearfirst)
                    for s in sample_set if s['station_number'] == station and s['date'] == sample_date]
    # Find the earliest time and convert it to a string
    sampling_time = min(sample_times).strftime(app_config['datetime_formats']['time']['export_event'])
    return sampling_time


def parse_datetime_from_string(date, time, dayfirst=True, yearfirst=False):
    """
    Wrapper function for dateutil.parser.parse.
    Takes a date string and time string (in any format) and parses it into a
    datetime object.
    :param date_string: String containing date information
    :param time_string: String containing time information
    :return: Datetime object containing date and time information
    """
    try:
        datetime_concat = " ".join([str(date), str(time)])
        dt = parse(datetime_concat, dayfirst=dayfirst, yearfirst=yearfirst, default=None)
    except (ValueError, TypeError):
        raise DatetimeError
    return dt


def prepare_dictionary(data_list, date_format):
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
    # Parse the sample date and time
    for sample in data_list:
        try:
            dt_dayfirst = True if date_format[:2] == 'dd' else False
            dt_yearfirst = True if date_format[:2] == 'YY' else False
            sample_dt = parse_datetime_from_string(sample['date'], sample['sample_time'], dt_dayfirst, dt_yearfirst)
            sample['date'] = sample_dt.strftime(app_config['datetime_formats']['date']['export'])
            sample['sample_time'] = sample_dt.strftime(app_config['datetime_formats']['time']['export_sample'])
        except DatetimeError:
            raise
    # Each item in the list is a single dictionary representing a single sample
    for sample in data_list:
        # Get the sampling event time
        sample['event_time'] = get_sampling_time(data_list, sample['station_number'], sample['date'], date_format)

        # If no sample or data was collected, prepare a shortened dictionary
        if sample['sample_collected'] == 'NO':
            sample_param_oriented = copy.deepcopy(sample)
            sample_param_oriented["parameter"] = 'no_results_available'
            sample_param_oriented["value"] = True
            sample_param_oriented["units"] = 'SCAL'
            sample_param_oriented["method"] = 'NULL_METHOD'
            # Add the dictionary to the parameter-oriented container
            data_list_param_oriented.append(sample_param_oriented)
            continue

        # Get replicate number
        sample['replicate_number'] = get_replicate_number(sample['sample_type'])

        # Assign the static fraction information to the sample
        sample['fraction_lab_shortname'] = app_config['key_value_settings']['field_fraction_lab_shortname']
        sample['fraction_data_source'] = app_config['key_value_settings']['field_fraction_data_source']
        sample['fraction_number'] = get_fraction_number(sample)
        sample['fraction_entry_datetime'] = datetime.datetime.now().strftime(
            app_config['datetime_formats']['datetime']['fraction']
        )

        # If more than one replicate per sampling, increment replicate number on export
        rep_depth_tolerance = 0.15
        min_depth = float(sample['depth_upper']) - rep_depth_tolerance
        max_depth = float(sample['depth_upper']) + rep_depth_tolerance
        reps_in_sampling = [r['sample_time'] for r in data_list if
                            r['sampling_number'] == sample['sampling_number'] and
                            r['location_id'] == sample['location_id'] and
                            r['sample_type'] == sample['sample_type'] and
                            min_depth <= float(r['depth_upper']) <= max_depth]
        if len(reps_in_sampling) > 1:
            sorted(reps_in_sampling, key=lambda x: x[0])
            sample_idx = reps_in_sampling.index(sample['sample_time'])
            sample['replicate_number'] += sample_idx

        # Format the map zone and positioning method
        if sample['map_zone'] != "":
            sample['map_zone'] = "MGA 94 - Zone %s" % sample['map_zone']
        if (sample['easting'] != "" and sample['northing'] != "")\
                or (sample['latitude'] != "" and sample['longitude'] != ""):
            sample['positioning_method'] = "GPS - Global Positioning System"

        # Transform the data to parameter-oriented
        for param in app_config['parameters']:
            # Store sample metadata for reuse. We use deepcopy here so we create
            # a new object from the sample data.
            sample_param_oriented = copy.deepcopy(sample)
            try:
                # Create dictionary items for parameter, value, unit, device & method
                col_number = get_column_number(param)
                sample_param_oriented["parameter"] = param
                sample_param_oriented["method"] = column_config[col_number]['method']
                sample_param_oriented["value"] = sample_param_oriented.pop(param)
                sample_param_oriented["units"] = column_config[col_number]['unit_code']
                if param == 'turbidity':
                    sample_param_oriented["device"] = sample['turbidity_instrument']
                    # Add ">" sign if turbidity is high
                    # TODO: This could be made more generic if we want > available to other parameters
                    if sample_param_oriented["value"] >= column_config[col_number]['upper_limit']:
                        sample_param_oriented["value"] = ">" + sample_param_oriented["value"]
                else:
                    sample_param_oriented["device"] = sample['sampling_instrument']
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


def resource_path(relative_path):
    """
    Get absolute path to resource. This is necessary for
    bundling PyInstaller exes.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def write_to_csv(data_list, out_filepath, fieldnames_list):
    """
    Write a list of data dictionaries to a csv file
    :param data_list: List of dictionaries to be written. Each dictionary
        represents one line of data to be written
    :param out_filepath: Path to file object to be written to
    :param fieldnames_list: List of fieldnames to be used when writing
    :return: No return value
    """
    with open(out_filepath, 'wb') as f:
        writer = csv.DictWriter(
            f,
            delimiter=',',
            extrasaction='ignore',
            fieldnames=fieldnames_list
        )
        writer.writeheader()
        writer.writerows(data_list)
    return True
