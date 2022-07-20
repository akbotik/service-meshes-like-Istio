package at.ac.univie.iot.simulator;

import at.ac.univie.iot.configuration.Sensor;
import at.ac.univie.iot.data.ESensor;
import at.ac.univie.iot.data.SensorData;
import at.ac.univie.iot.data.GeneratorParameters;

import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Date;

import static at.ac.univie.iot.data.GeneratorParameters.*;

/**
 * Generates and publishes pressure data beginning 1970-01-01.
 * Average pressure is generated hourly.
 * Anomaly frequency is defined in {@link GeneratorParameters}
 */
public class PressureSimulator implements ISimulator {

    private final String UTC_ZONE = "UTC";

    @Override
    public SensorData simulate(Sensor sensor, double avgValueForOneDay, long currentHourInMs) {
        double randomPressure = generateRandomValue(avgValueForOneDay, PRESSURE_RANGE_FOR_ONE_HOUR);
        return new SensorData(sensor.getId(), sensor.getType(),
                LocalDateTime.ofInstant(Instant.ofEpochMilli(currentHourInMs), ZoneId.of(UTC_ZONE)),
                randomPressure);
    }

    @Override
    public double getRandomAverageValueForOneDay(double avgValueForCurrentMonth) {
        double randomPressure;
        if (shouldGenerateAnomaly(PRESSURE_ANOMALY_FREQUENCY)) {
            randomPressure = generateRandomValue(AVG_PRESSURE_IN_hPA + PRESSURE_ANOMALY,
                    PRESSURE_RANGE_FOR_ONE_DAY);
        } else {
            randomPressure = generateRandomValue(AVG_PRESSURE_IN_hPA, PRESSURE_RANGE_FOR_ONE_DAY);
        }
        return randomPressure;
    }

    @Override
    public double getRandomAverageValueForOneMonth(Date currentDate) {
        return 0;
    }

    @Override
    public ESensor getSimulatorName() {
        return ESensor.PRESSURE;
    }

}
