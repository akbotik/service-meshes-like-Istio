package at.ac.univie.fog.data;

import java.time.LocalDateTime;
import java.util.Objects;

/**
 * Sensor data received from IoT.
 */
@lombok.Value
public class SensorData {

    int sensorId;
    ESensor sensorType;
    LocalDateTime timestamp;
    double sensorValue;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        SensorData sensorData = (SensorData) o;
        return getSensorId() == sensorData.getSensorId() &&
                Objects.equals(getTimestamp(), sensorData.getTimestamp());
    }

    @Override
    public int hashCode() {
        return Objects.hash(getSensorId(), getTimestamp());
    }
}
