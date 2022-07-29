YEAR = 'YEAR'
MONTH = 'MONTH'
DAY = 'DAY'

TEMPERATURE = 'TEMPERATURE'
PRESSURE = 'PRESSURE'

PRESSURE_RANGE = (980.0, 1030.0)

TEMPERATURE_MONTHLY = {
    1: -30.0,
    2: -20.0,
    3: -10.0,
    4: 10.0,
    5: 20.0,
    6: 25.0,
    7: 35.0,
    8: 30.0,
    9: 15.0,
    10: 0.0,
    11: -15.0,
    12: -20.0
}

TEMPERATURE_DEVIATION = 11


def get_pressure_thresholds():
    low, high = PRESSURE_RANGE
    thresholds = {'low': low, 'high': high}
    return thresholds


def get_temperature_thresholds_for_month(month):
    temperature_range = (TEMPERATURE_MONTHLY.get(month) - TEMPERATURE_DEVIATION,
                         TEMPERATURE_MONTHLY.get(month) + TEMPERATURE_DEVIATION)
    low, high = temperature_range
    thresholds = {'low': low, 'high': high}
    return thresholds


def get_temperature_thresholds_for_year():
    sorted_temperature = sorted(TEMPERATURE_MONTHLY.values())
    temperature_range = (sorted_temperature[0] - TEMPERATURE_DEVIATION,
                         sorted_temperature[-1] + TEMPERATURE_DEVIATION)
    low, high = temperature_range
    thresholds = {'low': low, 'high': high}
    return thresholds
