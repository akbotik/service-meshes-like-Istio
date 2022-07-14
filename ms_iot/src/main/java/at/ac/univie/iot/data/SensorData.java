package at.ac.univie.iot.data;

import java.time.LocalDateTime;

/**
 * Sensor data sent to Fog.
 */
@lombok.Data
@lombok.AllArgsConstructor
public class SensorData {
    private int sensorId;
    private ESensor sensorType;
    private LocalDateTime timestamp;
    private double sensorValue;
}
