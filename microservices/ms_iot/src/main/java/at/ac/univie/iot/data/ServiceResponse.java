package at.ac.univie.iot.data;

public class ServiceResponse {

    private String error;
    private String errorMsg;
    private String status;

    public ServiceResponse(String error, String errorMsg, String status) {
        this.error = error;
        this.errorMsg = errorMsg;
        this.status = status;
    }

    public ServiceResponse() {}

    public String getError() {
        return error;
    }

    public void setError(String error) {
        this.error = error;
    }

    public String getErrorMsg() {
        return errorMsg;
    }

    public void setErrorMsg(String errorMsg) {
        this.errorMsg = errorMsg;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }
}
