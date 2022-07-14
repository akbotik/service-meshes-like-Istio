package at.ac.univie.fog.aggregator;

import at.ac.univie.fog.data.EAggregationMode;
import at.ac.univie.fog.data.SensorData;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.NoSuchElementException;

@Component
public class AvgAggregator implements IAggregator {

    @Override
    public EAggregationMode getAggregatorName() {
        return EAggregationMode.AVG;
    }


    @Override
    public double aggregate(List<SensorData> sensorDataList) {
        if (sensorDataList == null || sensorDataList.size() == 0) throw new NoSuchElementException();
        double valuesSum = sensorDataList.stream().map(SensorData::getSensorValue).reduce(0.0, Double::sum);
        return valuesSum / sensorDataList.size();
    }

}
