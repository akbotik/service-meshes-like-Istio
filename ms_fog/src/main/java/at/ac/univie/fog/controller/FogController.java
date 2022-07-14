package at.ac.univie.fog.controller;

import at.ac.univie.fog.aggregator.IAggregator;
import at.ac.univie.fog.data.AggregatedData;
import at.ac.univie.fog.data.SensorData;
import at.ac.univie.fog.repository.FogRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadPoolExecutor;

@Component
public class FogController {

    private static Logger logger = LoggerFactory.getLogger(FogController.class.getName());

    @Autowired
    FogRepository fogRepository;

    @Autowired
    public DataHandler dataHandler;

    private Set<SensorData> sensorDataSet;
    private Set<LocalDate> aggregatedDates;
    private ThreadPoolExecutor executor;

    @Autowired
    public FogController() {
       sensorDataSet = ConcurrentHashMap.newKeySet();
       aggregatedDates = ConcurrentHashMap.newKeySet();
       executor = (ThreadPoolExecutor) Executors.newFixedThreadPool(10);
    }

    public void onDataReceived(SensorData sensorData) {
        executor.execute(() -> {
            aggregateData(sensorData);
        });
    }

    /**
     *  Injects the aggregation strategy of the fog computing defined in the configuration file.
     *  If events for the whole interval are received, the aggregated data is sent to MS ML.
     */
    private void aggregateData(SensorData sensorData) {
        // if sensor data was already saved, do not process it again
        if (aggregatedDates.contains(sensorData.getTimestamp().toLocalDate())) {
            return;
        }
        // find the strategy based on config
        IAggregator aggregator = dataHandler.findAggregator();

        this.sensorDataSet.add(sensorData);

        // get all data for current day/month/year
        List<SensorData> dataForInterval = dataHandler.getDataForCurrentInterval(sensorData, this.sensorDataSet);
        // number of sensors, that sent data to Fog
        long distinctSensors = dataHandler.getDistinctSensorNumber(dataForInterval);
        // get hours between event time and the next day/month/year
        long hoursForInterval = dataHandler.getHoursForCurrentInterval(sensorData);

        if ((distinctSensors * hoursForInterval) == dataForInterval.size()) {
            aggregatedDates.add(sensorData.getTimestamp().toLocalDate());
            double aggregatedValue = aggregator.aggregate(dataForInterval);
            AggregatedData aggregatedData = dataHandler.getAggregatedData(sensorData.getTimestamp(), aggregatedValue);
            dataForInterval.forEach(this.sensorDataSet::remove);
            logger.info("Saving to database: {}", aggregatedData);
            saveData(aggregatedData);
        }
    }

    /**
     * Use UDP socket to the aggregated send data to MS ML.
     */
    private void saveData(AggregatedData aggregatedData) {
        fogRepository.save(aggregatedData);
    }

}
