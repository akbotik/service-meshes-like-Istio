package at.ac.univie.iot.simulator;

import at.ac.univie.iot.configuration.Sensor;
import at.ac.univie.iot.data.ESensor;
import at.ac.univie.iot.data.GeneratorParameters;
import at.ac.univie.iot.data.SensorData;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Calendar;
import java.util.Date;
import java.util.Random;

import static at.ac.univie.iot.data.GeneratorParameters.*;

/**
 * Generates a reasonable temperature sensor data.
 * Anomaly frequency is defined in {@link GeneratorParameters}
 */
@Component
public class TemperatureSimulator implements ISimulator {

    @Override
    public double getRandomAverageValueForOneMonth(Date currentDate) {
        int currentMonth = getMonthFromDate(currentDate);
        return MONTH_TO_AVERAGE_TEMPERATURE.get(currentMonth);
    }

    @Override
    public double getRandomAverageValueForOneDay(double avgValueForCurrentMonth) {
        double randomTemperature;
        if (shouldGenerateAnomaly(TEMPERATURE_ANOMALY_FREQUENCY)) {
            int randomAnomaly = ANOMALY.get(new Random().nextInt(ANOMALY.size()));
            randomTemperature = generateRandomValue(avgValueForCurrentMonth + randomAnomaly,
                    TEMPERATURE_RANGE_FOR_ONE_DAY);
        } else {
            randomTemperature = generateRandomValue(avgValueForCurrentMonth, TEMPERATURE_RANGE_FOR_ONE_DAY);
        }
        return randomTemperature;
    }

    @Override
    public SensorData simulate(Sensor sensor, double avgValueForOneDay, long currentHourInMs) {
        double randomTemperature = generateRandomValue(avgValueForOneDay, TEMPERATURE_RANGE_FOR_ONE_HOUR);
        return new SensorData(sensor.getId(), sensor.getType(),
                LocalDateTime.ofInstant(Instant.ofEpochMilli(currentHourInMs), ZoneId.of(UTC_ZONE)),
                randomTemperature);
    }

    private int getMonthFromDate(Date currentDate) {
        Calendar calendar = Calendar.getInstance();
        calendar.setTime(currentDate);
        return calendar.get(Calendar.MONTH);
    }

    @Override
    public ESensor getSimulatorName() {
        return ESensor.TEMPERATURE;
    }

}
