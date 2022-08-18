package at.ac.univie.iot.network;

import at.ac.univie.iot.data.SensorData;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

@Component
public class IotNetwork {

    @Autowired
    private RestTemplate restTemplate;

    @Value("${fogUrl}")
    private String fogUrl;

    /**
     * Sends the generated data to Fog.
     *
     * @param sensorData the generated sensor data for one hour
     */
    public void sendData(SensorData sensorData) {
        restTemplate.postForObject(fogUrl, sensorData, String.class);
    }

    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }

}
