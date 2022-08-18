package at.ac.univie.iot;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import at.ac.univie.iot.simulator.ISimulator;
import at.ac.univie.iot.simulator.PressureSimulator;

class IotApplicationTests {

    @Test
    public void generatedRange_shouldReturnValueBetweenRange() {
        ISimulator simulator = new PressureSimulator();
        double generatedRange = simulator.getRandomNumber(10, 100);
        Assertions.assertTrue(generatedRange >= 10 && generatedRange <= 100);
    }

    @Test
    public void generatedRandomValueWithDeviation_shouldBeInRange() {
        ISimulator simulator = new PressureSimulator();
        for (int i = 0; i < 100; ++i) {
            double generatedRange = simulator.generateRandomValue(10, 2);
            Assertions.assertTrue(generatedRange >= 8 && generatedRange <= 12);
        }
    }

    @Test
    public void shouldGenerateAnomaly() {
        ISimulator simulator = new PressureSimulator();
        // in 100 of cases anomaly must be generated
        boolean generatedRange = simulator.shouldGenerateAnomaly(1);
        Assertions.assertTrue(generatedRange);
    }

}
