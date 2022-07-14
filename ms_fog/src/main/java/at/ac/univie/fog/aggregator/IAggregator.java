package at.ac.univie.fog.aggregator;

import at.ac.univie.fog.data.EAggregationMode;
import at.ac.univie.fog.data.SensorData;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public interface IAggregator {

    EAggregationMode getAggregatorName();

    double aggregate(List<SensorData> sensorDataList);

}
