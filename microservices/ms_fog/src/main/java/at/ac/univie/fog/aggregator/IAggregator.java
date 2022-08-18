package at.ac.univie.fog.aggregator;

import at.ac.univie.fog.data.EAggregationMode;
import at.ac.univie.fog.data.SensorData;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * Concrete aggregator classes implement abstract methods defined by the IAggregator interface.
 * It is used when it is not known in advance which aggregation strategy should be injected.
 */
@Service
public interface IAggregator {

    EAggregationMode getAggregatorName();

    double aggregate(List<SensorData> sensorDataList);

}
