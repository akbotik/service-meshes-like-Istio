package at.ac.univie.iot.controller;

import at.ac.univie.iot.configuration.Sensor;
import at.ac.univie.iot.data.SensorData;
import at.ac.univie.iot.network.IotNetwork;
import at.ac.univie.iot.simulator.ISimulator;
import at.ac.univie.iot.simulator.SimulatorFactory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;

import static at.ac.univie.iot.data.GeneratorParameters.HOUR_IN_MS;

@Component
public class IotController {

    private static Logger logger = LoggerFactory.getLogger(IotController.class.getName());

    @Autowired
    private IotNetwork network;

    private Sensor sensor;

    public IotController() { }

    /**
     *  Injects the simulation strategy of the IoT device defined in the configuration file,
     *  which generates reasonable sensor data.
     */
    public long generateData(long stopTime, long startDay) {
        ISimulator simulator = new SimulatorFactory().findSimulator(sensor.getType());
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
//                try {
//                    Thread.sleep(10);
//                } catch (InterruptedException e) {
//                    e.printStackTrace();
//                }
                logger.info("Sending to Fog: {}.", sensorData);
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
