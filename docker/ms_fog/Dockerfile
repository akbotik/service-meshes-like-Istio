FROM openjdk:11
WORKDIR /usr/app/ms_fog
COPY ./ ./
CMD ["java", "-jar", "ms_fog.jar", "--aggregationMode=MIN", "--server.port=8080", "--spring.datasource.url=jdbc:postgresql://postgres:5432/postgres"]