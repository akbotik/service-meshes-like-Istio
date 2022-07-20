package at.ac.univie.iot.simulator;

import at.ac.univie.iot.configuration.Sensor;
import at.ac.univie.iot.data.ESensor;
import at.ac.univie.iot.data.SensorData;
import org.springframework.stereotype.Service;

import java.util.Date;
import java.util.Random;

import static at.ac.univie.iot.data.GeneratorParameters.MIN_RANGE;

/**
 * Concrete simulator classes implement abstract
 * methods defined by the ISimulator interface.
 * It is used when the client does not know
 * in advance which concrete products would be created.
 */
@Service
public interface ISimulator {

    SensorData simulate(Sensor sensor, double avgValueForOneDay, long currentHourInMs);

    double getRandomAverageValueForOneDay(double avgValueForCurrentMonth);

    double getRandomAverageValueForOneMonth(Date currentDate);

    ESensor getSimulatorName();

    default int getRandomNumber(int min, int max) {
        return (int) ((Math.random() * (max - min + MIN_RANGE)) + min);
    }

    default double generateRandomValue(double randomValue, int valueDeviation) {
        double minValue = randomValue - valueDeviation;
        double maxValue = randomValue + valueDeviation;
        return minValue + (maxValue - minValue) *
                new Random().nextDouble();
    }

    default boolean shouldGenerateAnomaly(int anomalyFrequency) {
        int randomNumber = getRandomNumber(MIN_RANGE, anomalyFrequency);
        return randomNumber == MIN_RANGE;
    }

}
