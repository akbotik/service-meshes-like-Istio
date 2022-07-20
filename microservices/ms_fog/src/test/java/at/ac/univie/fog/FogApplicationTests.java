package at.ac.univie.fog;

import at.ac.univie.fog.aggregator.AvgAggregator;
import at.ac.univie.fog.aggregator.IAggregator;
import at.ac.univie.fog.aggregator.MaxAggregator;
import at.ac.univie.fog.aggregator.MinAggregator;
import at.ac.univie.fog.controller.DataHandler;
import at.ac.univie.fog.data.ESensor;
import at.ac.univie.fog.data.SensorData;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.*;

import static org.junit.jupiter.api.Assertions.assertEquals;

@SpringBootTest
@TestPropertySource(locations="classpath:test.properties")
class FogApplicationTests {

    

    @Autowired
    private DataHandler dataHandler;



    @Test
    public void minAggregatorTest_shouldReturnMinValue() {
        IAggregator aggregator = new MinAggregator();
        double minValue = aggregator.aggregate(events());
        assertEquals(minValue, -12.01);
    }

    @Test
    public void maxAggregatorTest_shouldReturnMaxValue() {
        IAggregator aggregator = new MaxAggregator();
        double minValue = aggregator.aggregate(events());
        assertEquals(minValue, 32.11);
    }

    @Test
    public void avgAggregatorTest_shouldReturnAvgValue() {
        IAggregator aggregator = new AvgAggregator();
        double minValue = aggregator.aggregate(events());
        assertEquals(minValue,  12.196);
    }


    @Test
    public void numberOfHoursInMonth() {
        long numberOfHoursInMonth = dataHandler.getHoursForCurrentInterval(
                new SensorData(1, ESensor.TEMPERATURE, LocalDateTime.now(),2.0));
        assertEquals(744, numberOfHoursInMonth);
    }


    @Test
    public void sensorsThatSentEventsToFog_shouldReturn3() {
        long distinctSensors = dataHandler.getDistinctSensorNumber(events());
        assertEquals(3, distinctSensors);
    }




    @Test
    public void hoursBetweenTwoDays() {
        String now = "2021-12-09 10:30";
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");

        LocalDateTime timeFrom = LocalDateTime.parse(now, formatter);
        LocalDateTime localDateNextMonth = timeFrom.plusDays(1);


        assertEquals(24, ChronoUnit.HOURS.between(timeFrom.withHour(0), localDateNextMonth.withHour(0)));
    }

    @Test
    public void hoursBetweenTwoMonths() {
        String now = "2021-01-09 10:30";
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");

        LocalDateTime timeFrom = LocalDateTime.parse(now, formatter);
        LocalDateTime localDateNextMonth = timeFrom.plusMonths(1);

        assertEquals(744, ChronoUnit.HOURS.between(timeFrom.withDayOfMonth(1), localDateNextMonth.withDayOfMonth(1)));
    }

    @Test
    public void hoursBetweenTwoYears() {
        String now = "2021-12-09 10:30";
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");

        LocalDateTime timeFrom = LocalDateTime.parse(now, formatter);
        LocalDateTime localDateNextMonth = timeFrom.plusYears(1);

        assertEquals(8760, ChronoUnit.HOURS.between(timeFrom.withDayOfYear(1), localDateNextMonth.withDayOfYear(1)));
    }


    private List<SensorData> events() {
        List<SensorData> sensorData = new ArrayList<>();
        sensorData.add(new SensorData(1, ESensor.TEMPERATURE, LocalDateTime.now(), 11.22));
        sensorData.add(new SensorData(2, ESensor.TEMPERATURE, LocalDateTime.now(), 31.01));
        sensorData.add(new SensorData(3, ESensor.TEMPERATURE, LocalDateTime.now(), 7.00));
        sensorData.add(new SensorData(1, ESensor.TEMPERATURE, LocalDateTime.now(), -11.11));
        sensorData.add(new SensorData(1, ESensor.TEMPERATURE, LocalDateTime.now(), 15.3));
        sensorData.add(new SensorData(1, ESensor.TEMPERATURE, LocalDateTime.now(), 20.03));
        sensorData.add(new SensorData(1, ESensor.TEMPERATURE, LocalDateTime.now(), 14.03));
        sensorData.add(new SensorData(1, ESensor.TEMPERATURE, LocalDateTime.now(), 15.44));
        sensorData.add(new SensorData(1, ESensor.TEMPERATURE, LocalDateTime.now(), 17.19));
        sensorData.add(new SensorData(1, ESensor.TEMPERATURE, LocalDateTime.now(), 9.11));
        sensorData.add(new SensorData(1, ESensor.TEMPERATURE, LocalDateTime.now(), 8.49));
        sensorData.add(new SensorData(1, ESensor.TEMPERATURE, LocalDateTime.now(), -12.01));
        sensorData.add(new SensorData(1, ESensor.TEMPERATURE, LocalDateTime.now(), 12.01));
        sensorData.add(new SensorData(1, ESensor.TEMPERATURE, LocalDateTime.now(), 13.12));
        sensorData.add(new SensorData(1, ESensor.TEMPERATURE, LocalDateTime.now(), 32.11));
        return sensorData;
    }

}
