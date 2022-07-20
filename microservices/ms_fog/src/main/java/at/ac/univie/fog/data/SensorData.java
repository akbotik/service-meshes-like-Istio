package at.ac.univie.fog.data;

import java.time.LocalDateTime;
import java.util.Objects;

/**
 * Sensor data received from MS Fog.
 */
public class SensorData {

    private int sensorId;
    private ESensor sensorType;
    private LocalDateTime timestamp;
    private double sensorValue;

    public SensorData(int sensorId, ESensor sensorType, LocalDateTime timestamp, double sensorValue) {
        this.sensorId = sensorId;
        this.sensorType = sensorType;
        this.timestamp = timestamp;
        this.sensorValue = sensorValue;
    }

    public int getSensorId() {
        return sensorId;
    }

    public ESensor getSensorType() {
        return sensorType;
    }

    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    public double getSensorValue() {
        return sensorValue;
    }

    @Override
    public String toString() {
        return "SensorData(" +
                "sensorId=" + sensorId +
                ", sensorType=" + sensorType +
                ", timestamp=" + timestamp +
                ", sensorValue=" + sensorValue +
                ')';
    }

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
