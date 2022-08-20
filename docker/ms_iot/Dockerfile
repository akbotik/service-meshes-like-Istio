FROM openjdk:11
WORKDIR /usr/app/ms_iot
COPY ./ ./
CMD ["java", "-jar", "ms_iot.jar", "--fogUrl=http://ms-fog:8080/v1/aggregateSensorData"]