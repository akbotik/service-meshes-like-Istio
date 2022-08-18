package at.ac.univie.fog.network;

import at.ac.univie.fog.controller.FogController;
import at.ac.univie.fog.data.ESensor;
import at.ac.univie.fog.data.SensorData;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;

@org.springframework.web.bind.annotation.RestController
@RequestMapping(value = "/v1")
public class RestController {

    // TODO: Move to other class

    @Autowired
    public FogController controller;

    @Value("${dataType}")
    private ESensor dataType;

    /**
     * Aggregates sensor data from IoT according to a configured data type.
     *
     * @param sensorData the sensor data for one hour
     * @return the status "OK", if sensor data can be aggregated
     */
    @PostMapping("/aggregateSensorData")
    public ResponseEntity<String> aggregateSensorData(@RequestBody SensorData sensorData) {
        if (sensorData.getSensorType() != dataType) {
            return new ResponseEntity<>("NOK", HttpStatus.BAD_REQUEST);
        }
        controller.onDataReceived(sensorData);
        return new ResponseEntity<>("OK", HttpStatus.OK);
    }

}
