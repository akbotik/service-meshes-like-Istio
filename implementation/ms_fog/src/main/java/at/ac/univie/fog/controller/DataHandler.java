package at.ac.univie.fog.controller;

import at.ac.univie.fog.aggregator.AggregatorFactory;
import at.ac.univie.fog.aggregator.IAggregator;
import at.ac.univie.fog.data.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

@Component
@Slf4j
public class DataHandler {

    @Value("${dataType}")
    private ESensor dataType;

    @Value("${aggregationMode}")
    private EAggregationMode aggregationMode;

    @Value("${aggregationInterval}")
    private EAggregationInterval aggregationInterval;

    @Autowired
    private AggregatorFactory aggregatorFactory;

    private static final short HOURS_IN_DAY = 24;

    public IAggregator findAggregator() {
        return aggregatorFactory.findAggregator(aggregationMode);
    }

    public List<SensorData> getDataForCurrentInterval(SensorData sensorData, Set<SensorData> sensorDataSet) {
        switch (aggregationInterval) {
            case DAY: return sensorDataSet.stream().filter(
                    e -> e.getTimestamp().toLocalDate().isEqual(sensorData.getTimestamp().toLocalDate())).collect(Collectors.toList());
            case MONTH: return sensorDataSet.stream()
                    .filter(e -> e.getTimestamp().getYear() == sensorData.getTimestamp().getYear())
                    .filter(e -> e.getTimestamp().getMonth().equals(sensorData.getTimestamp().getMonth()))
                    .collect(Collectors.toList());
            case YEAR: return sensorDataSet.stream().filter(
                    e -> e.getTimestamp().getYear() == (sensorData.getTimestamp().getYear())).collect(Collectors.toList());
        }
        return new ArrayList<>();
    }

    public long getDistinctSensorNumber(List<SensorData> dataForInterval) {
        Set<Integer> set = new HashSet<>(dataForInterval.size());
        return dataForInterval.stream().filter(p -> set.add(p.getSensorId())).count();
    }

    public long getHoursForCurrentInterval(SensorData sensorData) {
        LocalDateTime dataTs = sensorData.getTimestamp();
        switch (aggregationInterval) {
            case YEAR:
                LocalDateTime nextYear = dataTs.plusYears(1);
                return ChronoUnit.HOURS.between(dataTs.withDayOfYear(1), nextYear.withDayOfYear(1));
            case MONTH:
                LocalDateTime nextMonth = dataTs.plusMonths(1);
                return ChronoUnit.HOURS.between(dataTs.withDayOfMonth(1), nextMonth.withDayOfMonth(1));
            default: return HOURS_IN_DAY;
        }
    }

    public AggregatedData getAggregatedData(LocalDate timestamp, double aggregatedValue) {
        return new AggregatedData(dataType, aggregationMode, aggregationInterval,
                timestamp, aggregatedValue);
    }

    @PostConstruct
    private void log() {
        log.info("Aggregation mode: {}. Aggregation interval: {}. Data type {}.",
                aggregationMode.name(), aggregationInterval.name(), dataType.name());
    }

}