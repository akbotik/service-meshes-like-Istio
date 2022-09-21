package at.ac.univie.iot.data;

@lombok.Data
@lombok.AllArgsConstructor
public class ServiceResponse {

    private String error;
    private String errorMsg;
    private String status;

}
