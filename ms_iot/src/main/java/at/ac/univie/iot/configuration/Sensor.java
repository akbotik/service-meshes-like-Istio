package at.ac.univie.iot.configuration;

import at.ac.univie.iot.data.ESensor;

/**
 * Sensor configuration.
 */
@lombok.Value
public class Sensor {
    int id;
    ESensor type;
}
