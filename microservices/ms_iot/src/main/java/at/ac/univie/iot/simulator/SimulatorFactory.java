package at.ac.univie.iot.simulator;

import at.ac.univie.iot.data.ESensor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;

/**
 * Factory Pattern.
 */
@Component
public class SimulatorFactory {

    private Map<ESensor, ISimulator> simulators;

    @Autowired
    public SimulatorFactory(Set<ISimulator> strategySet) {
        createSimulator(strategySet);
    }

    private void createSimulator(Set<ISimulator> strategySet) {
        simulators = new HashMap<>();
        strategySet.forEach(s -> simulators.put(s.getSimulatorName(), s));
    }

    public ISimulator findSimulator(ESensor sensorType) {
        return simulators.get(sensorType);
    }

}
