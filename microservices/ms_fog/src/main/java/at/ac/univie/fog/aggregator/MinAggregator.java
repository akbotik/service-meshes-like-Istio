package at.ac.univie.fog.aggregator;

import at.ac.univie.fog.data.EAggregationMode;
import at.ac.univie.fog.data.SensorData;
import org.springframework.stereotype.Component;

import java.util.Comparator;
import java.util.List;
import java.util.NoSuchElementException;

@Component
public class MinAggregator implements IAggregator {

    @Override
    public EAggregationMode getAggregatorName() {
        return EAggregationMode.MIN;
    }

    @Override
    public double aggregate(List<SensorData> sensorDataList) {
        var minValueEvent = sensorDataList.stream().min(Comparator.comparingDouble(SensorData::getSensorValue)).orElseThrow(NoSuchElementException::new);
        return minValueEvent.getSensorValue();
    }

}
