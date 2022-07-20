package at.ac.univie.fog.aggregator;

import at.ac.univie.fog.data.EAggregationMode;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;

@Component
public class AggregatorFactory {

    private Map<EAggregationMode, IAggregator> aggregators;

    @Autowired
    public AggregatorFactory(Set<IAggregator> strategySet) {
        createAggregator(strategySet);
    }

    private void createAggregator(Set<IAggregator> strategySet) {
        aggregators = new HashMap<>();
        strategySet.forEach(s -> aggregators.put(s.getAggregatorName(), s));
    }

    public IAggregator findAggregator(EAggregationMode aggregatorType) {
        return aggregators.get(aggregatorType);
    }

}
