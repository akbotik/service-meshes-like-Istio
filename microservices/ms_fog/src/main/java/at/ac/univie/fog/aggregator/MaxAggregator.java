package at.ac.univie.fog.aggregator;

import at.ac.univie.fog.data.EAggregationMode;
import at.ac.univie.fog.data.SensorData;
import org.springframework.stereotype.Component;

import java.util.Comparator;
import java.util.List;
import java.util.NoSuchElementException;

@Component
public class MaxAggregator implements IAggregator {

    @Override
    public EAggregationMode getAggregatorName() {
        return EAggregationMode.MAX;
    }

    @Override
    public double aggregate(List<SensorData> sensorDataList) {
        SensorData maxValueEvent = sensorDataList.stream().max(Comparator.comparingDouble(SensorData::getSensorValue)).orElseThrow(NoSuchElementException::new);
        return maxValueEvent.getSensorValue();
    }

}
