"""
Module: globals.py
Defines the global constants and lists used in the KiWQM Field Data
Formatter application.

Title: Data & Procedures Officer
Organisation: DPI Water
Date modified: 13/10/2015
"""
# Splash screen image
SPLASH_FN = "../img/splash_screen_scribus_02.jpg"

# Global constants
LABORATORY = "Field Measurement"
DATA_SOURCE = "Field Data"

# List of available instruments
INSTRUMENTS = ["Hydrolab DS5", "Hydrolab MS4", "Hydrolab MS5"]
TURBIDITY_INSTRUMENT = ["HACH Tubiditimeter 2100P", "HACH Tubiditimeter 2100Q"]
DEFAULT_INSTRUMENT = "Hydrolab DS5"
DEFAULT_TURB_INSTRUMENT = "HACH Tubiditimeter 2100P"

# List of available sample types
SAMPLE_TYPES = ["P", "R", "D", "T", "QR", "QB", "QT"]

# List of available matrices
MATRIX_TYPES = ["ST", "SG", "GB", "GP", "PR"]

# Boolean values
BOOLEAN = ["Yes", "No"]

# List of available parameters
PARAMETERS = ["conductivity_uncomp", "conductivity_comp", "do", "do_sat", "gauge_height",
              "ph", "temp_c", "turbidity", "water_depth"]

# List of available field officers
FIELD_STAFF = ["Alison Lewis",
               "Andy Wise",
               "Claire Evans",
               "Dan Poflotski",
               "Dane Clarke",
               "Darice Pepper",
               "David Donnelly",
               "Gerhard Schulz",
               "Gordon Honeyman",
               "James Hitchcock",
               "Jane Rowlands",
               "Maxine Rowley",
               "Michael Rowe",
               "Monika Muschal",
               "Sarah McGeoch",
               "Skye Taylor",
               "Sue Botting",
               "Tracy Fulford",
               "Warwick Mawhinney"]

# List of available measuring program numbers
MP_NUMBERS = ["MP406",
              "MP409",
              "MP418",
              "MP420",
              "MP424",
              "MP430",
              "MP433",
              "MP479",
              "MP514",
              "MP516",
              "MP639",
              "MP676",
              "MP699",
              "MP709",
              "MP720",
              "MP721"]

# Instrument names as variables
HYDROLAB_INSTRUMENTS = ["Hydrolab DS5", "Hydrolab MS4", "Hydrolab MS5"]

# Required fields for export
REQUIRED_FIELDS = [
    'mp_number',
    'station_number',
    'date',
    'sample_matrix',
    'sample_type',
    # 'sampling_reason',
    'sampling_instrument',
    'sampling_officer',
    'location_id',
    'sample_cid',
    'sample_time',
    'depth_upper']

# Non-zero fields
NON_ZERO_FIELDS = [
    "conductivity_uncomp",
    "conductivity_comp",
    "do",
    "do_sat",
    "ph",
    "temp_c",
    "turbidity"]

# CSV Properties
FIELDNAMES = [
    'mp_number',
    'station_number',
    'sampling_number',
    'date',
    'event_time',
    'sample_matrix',
    'sample_type',
    'calibration_record',
    'sampling_reason',
    'sampling_officer',
    'sampling_comment',
    'location_id',
    'sample_cid',
    'replicate_number',
    'sample_time',
    'depth_upper',
    'depth_lower',
    'sample_collected',
    'fraction_lab_shortname',    # Static text
    'fraction_data_source',      # Static text
    'fraction_number',           # Calculated value
    'fraction_entry_datetime',   # Current time (datetime.now)
    'method',
    'parameter',
    'value',
    'units',
    'device']

COPY_DOWN_FIELDS = [
    'Measuring Program',
    'Station',
    'Date',
    'Location #',
    'Sample #',
    'Matrix',
    'Sample Type',
    'Instrument',
    'Sampling Officer']

COPY_DOWN_CODES = {
    'Measuring Program': 'mp_number',
    'Station': 'station_number',
    'Date': 'date',
    'Location #': 'location_id',
    'Sample #': 'sample_cid',
    'Matrix': 'sample_matrix',
    'Sample Type': 'sample_type',
    'Instrument': 'sampling_instrument',
    'Sampling Officer': 'sampling_officer'}
