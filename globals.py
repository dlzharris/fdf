# Global constants
LABORATORY = "Field Measurement"
DATA_SOURCE = "Field Data"
# List of available instruments
INSTRUMENTS = ["Hydrolab DS5", "Hydrolab MS4", "Hydrolab MS5"]
DEFAULT_INSTRUMENT = "Hydrolab DS5"
# List of available field officers
FIELD_STAFF = ["Andy Wise", "Sarah McGeoch"]
# List of available sample types
SAMPLE_TYPES = ["P", "RE", "DU", "TR", "QR", "QB", "QT"]
# List of available matrices
MATRIX_TYPES = ["ST", "SG", "GB", "GP", "PR"]
# Boolean values
BOOLEAN = ["Yes", "No"]
# List of available parameters
PARAMETERS = ["conductivity_uncomp", "do", "do_sat", "gauge_height",
              "ph", "temp_c", "turbidity", "water_depth"]

# Instrument names as variables
hydrolab_instruments = ["Hydrolab DS5", "Hydrolab MS4", "Hydrolab MS5"]

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
    'parameter',
    'value',
    'units']

