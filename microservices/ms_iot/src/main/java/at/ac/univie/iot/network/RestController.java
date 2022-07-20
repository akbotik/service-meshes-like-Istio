package at.ac.univie.iot.network;


import at.ac.univie.iot.configuration.Sensor;
import at.ac.univie.iot.controller.IotController;
import at.ac.univie.iot.data.ServiceResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@org.springframework.web.bind.annotation.RestController
@RequestMapping(value = "/v1")
public class RestController {

    @Autowired
    private IotController controller;

    private long generatorStartDay = 31536000000L;

    @PostMapping(value = "/generateSensorData", consumes = "application/json", produces = "application/json")
    public ResponseEntity<ServiceResponse> generateSensorData(@RequestBody Sensor sensor, @RequestParam int requestDuration) {
        //System.out.println(sensor.getId() + " // " + sensor.getType() + " // " + requestDuration);
        long end = System.currentTimeMillis() + requestDuration;
        controller.setSensor(sensor);
        generatorStartDay = controller.generateData(end, generatorStartDay);
        ServiceResponse serviceResponse = new ServiceResponse("", "", "OK");
        return new ResponseEntity<>(serviceResponse, HttpStatus.OK);
    }

}
