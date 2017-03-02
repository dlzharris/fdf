import codecs
import functions
# Local application imports
from settings import app_config, column_config, station_list
from functions import ValidityError

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
    elif file_source in app_config['sources']['hanna']:
        pass
    elif file_source in app_config['sources']['ysi']:
        if file_source == 'EXO (KOR file)':
            header_start_row = 22
            data_start_row = 23
            encoding = 'latin-1'
        elif file_source == 'EXO (instrument)':
            header_start_row = 0
            data_start_row = 1
            encoding = 'utf16'

    with codecs.open(instrument_file, "rb", encoding=encoding) as f:
        # Check the validity of the file
        try:
            functions.check_file_validity(f, file_source)
        except ValidityError:
            raise ValidityError

        # Rewind the file head
        f.seek(0)

        # Read the file into a list for initial interrogation and processing. We will
        # read the data portion into a dictionary further below.
        in_list = list(f.readlines())
        parameters = in_list[header_start_row].replace('"', '').replace('\r\n', '').split(',')

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
            new_line['easting'], new_line['northing'], new_line['map_zone'] = \
                get_mga_coordinates(new_line['latitude'], new_line['longitude'])

            # Add the extra items we'll need access to later on
            for item in column_config:
                if item['name'] not in new_line:
                    new_line[column_config['name']] = ""

            dic = {new_line[column_config['name']]:"" for item in column_config}



            new_line['event_time'] = ""
            new_line['sampling_number'] = ""
            new_line['replicate_number'] = ""
            new_line['sample_cid'] = ""
            new_line['sample_matrix'] = ""
            new_line['sample_type'] = ""
            new_line['mp_number'] = ""
            new_line['location_id'] = ""
            new_line['collection_method'] = ""
            new_line['calibration_record'] = ""
            new_line['station_visited'] = ""
            new_line['sample_collected'] = ""
            new_line['depth_lower'] = ""
            new_line['sampling_comment'] = ""
            new_line['turbidity_instrument'] = ""
            new_line['gauge_height'] = ""
            new_line['turbidity'] = ""
            new_line['water_depth'] = ""
            if 'barometric_pressure' not in new_line:
                new_line['barometric_pressure'] = ""
            if 'conductivity_comp' not in new_line:
                new_line['conductivity_comp'] = ""
            if 'conductivity_uncomp' not in new_line:
                new_line['conductivity_uncomp'] = ""
            if 'easting' not in new_line:
                new_line['easting'] = ""
            if 'northing' not in new_line:
                new_line['northing'] = ""
            if 'map_zone' not in new_line:
                new_line['map_zone'] = ""
            if 'latitude' not in new_line:
                new_line['latitude'] = ""
            if 'longitude' not in new_line:
                new_line['longitude'] = ""

            # Add the new updated dictionary to our list
            data.append(new_line)

    # Return the list
    return data