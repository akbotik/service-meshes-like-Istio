package at.ac.univie.iot.simulator;

import at.ac.univie.iot.data.ESensor;

/**
 * Factory Pattern.
 */
public class SimulatorFactory {

    public ISimulator findSimulator(ESensor sensorType) {
        switch (sensorType) {
            case TEMPERATURE: return new TemperatureSimulator();
            case PRESSURE: return new PressureSimulator();
        }
        return null;
    }

}
