package at.ac.univie.iot.data;

import java.util.HashMap;
import java.util.Map;

/**
 * Parameters used to generate reasonable sensor data.
 */
public class GeneratorParameters {

    public static final double HOUR_IN_MS = 3600000;

    public static final int MIN_RANGE = 1;

    // PRESSURE
    public static final double AVG_PRESSURE_IN_hPA = 1013.25;
    // pressure deviation, not anomaly
    public static final int PRESSURE_RANGE_FOR_ONE_DAY = 15;
    public static final int PRESSURE_RANGE_FOR_ONE_HOUR = 3;
    // anomaly
    public static final int PRESSURE_ANOMALY = 100;
    // how often anomaly should occur
    public static final int PRESSURE_ANOMALY_FREQUENCY = 50;

    // TEMPERATURE
    // temperature deviation, not anomaly
    public static final int TEMPERATURE_RANGE_FOR_ONE_DAY = 10;
    public static final int TEMPERATURE_RANGE_FOR_ONE_HOUR = 1;
    // anomaly
    public static final int TEMPERATURE_ANOMALY = -100;
    // how often anomaly should occur
    public static final int TEMPERATURE_ANOMALY_FREQUENCY = 30;

    // avg temperature for each month in celsius
    public static final Map<Integer, Double> MONTH_TO_AVERAGE_TEMPERATURE = new HashMap<>() {{
        put(0, -30.0);
        put(1, -20.0);
        put(2, -10.0);
        put(3, 10.0);
        put(4, 20.0);
        put(5, 25.0);
        put(6, 35.0);
        put(7, 30.0);
        put(8, 15.0);
        put(9, 0.0);
        put(10, -15.0);
        put(11, -20.0);
    }};

    public static final String ROUNDING = "%.2f";

}
