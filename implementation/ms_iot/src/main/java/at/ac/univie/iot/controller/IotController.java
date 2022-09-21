package at.ac.univie.iot.controller;

import at.ac.univie.iot.configuration.Sensor;
import at.ac.univie.iot.data.SensorData;
import at.ac.univie.iot.network.IotNetwork;
import at.ac.univie.iot.simulator.ISimulator;
import at.ac.univie.iot.simulator.SimulatorFactory;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;

import static at.ac.univie.iot.data.GeneratorParameters.HOUR_IN_MS;

@Component
@Slf4j
public class IotController {

    @Autowired
    private SimulatorFactory simulatorFactory;

    @Autowired
    private IotNetwork network;

    private Sensor sensor;

    public IotController() { }

    /**
     * Injects the simulation strategy of the IoT device according to a configured sensor data type.
     * Generates and publishes a stream of simulated sensor values hourly.
     *
     * @param stopTime the time when data generation should be stopped
     * @param startDay the date on which data generation should start
     * @return the date of the last generated sensor data for the future requests
     */
    public long generateData(long stopTime, long startDay) {
        ISimulator simulator = simulatorFactory.findSimulator(sensor.getType());
        Instant previousDay = null;
        long day = startDay;
        for (; System.currentTimeMillis() < stopTime; day += HOUR_IN_MS * 24) {
            Date currentDate = new Date(day);
            Instant currentDay = currentDate.toInstant().truncatedTo(ChronoUnit.DAYS);
            double avgValueForMonth = simulator.getRandomAverageValueForOneMonth(currentDate);
            // new day
            if (!currentDay.equals(previousDay)) {
                double randomValueForOneDay = simulator.getRandomAverageValueForOneDay(avgValueForMonth);
                for (long hour = 0; hour < 24; ++hour) {
                    long currentHourInMs = (long) (day + (hour * HOUR_IN_MS));
                    SensorData sensorData = simulator.simulate(sensor, randomValueForOneDay, currentHourInMs);
                    network.sendData(sensorData);
                    log.info("Sent to Fog: {}.", sensorData);
                }
            }
            previousDay = currentDay;
        }
        return day;
    }

    public Sensor getSensor() {
        return sensor;
    }

    public void setSensor(Sensor sensor) {
        this.sensor = sensor;
    }

}
