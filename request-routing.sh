kubectl apply -f istio/request-routing.yaml
sleep 5;
echo "Waiting 30 seconds till there is enough sensor data..."
curl --location --request POST 'http://localhost/v1/generateSensorData?requestDuration=30000' \
--header 'Content-Type: application/json' \
--data-raw '{
    "id": 1,
    "type": "PRESSURE"
}'
curl --location --request POST 'http://localhost/v1/detectAnomaly' \
--header 'Content-Type: application/json' \
--data-raw '{
    "type": "PRESSURE"
}'
curl --location --request POST 'http://localhost/v1/predict' \
--header 'Content-Type: application/json' \
--data-raw '{
    "type": "PRESSURE",
    "date": "1971-01-07",
    "accuracy": "HIGH"
}'
curl --location --request POST 'http://localhost/v1/assessPredictions' \
--header 'Content-Type: application/json' \
--data-raw '{
    "predictions": [
        {
            "aggregation_interval": "DAY",
            "aggregation_mode": "MIN",
            "data_type": "PRESSURE",
            "date": "1971-01-01",
            "predicted_value": 1007.3210722543249
        },
        {
            "aggregation_interval": "DAY",
            "aggregation_mode": "MIN",
            "data_type": "PRESSURE",
            "date": "1971-01-01",
            "predicted_value": 1015.3134745555662
        },
        {
            "aggregation_interval": "DAY",
            "aggregation_mode": "MIN",
            "data_type": "PRESSURE",
            "date": "1971-01-01",
            "predicted_value": 1030.4862869542915
        }
    ]
}'
curl --location --request POST 'http://localhost/v1/getAccuratePrediction' \
--header 'Content-Type: application/json' \
--data-raw '{
    "predictions": [
        {
            "aggregation_interval": "DAY",
            "aggregation_mode": "MIN",
            "data_type": "PRESSURE",
            "date": "1971-01-01",
            "predicted_value": 1007.3210722543249
        },
        {
            "aggregation_interval": "DAY",
            "aggregation_mode": "MIN",
            "data_type": "PRESSURE",
            "date": "1971-01-01",
            "predicted_value": 1015.3134745555662
        },
        {
            "aggregation_interval": "DAY",
            "aggregation_mode": "MIN",
            "data_type": "PRESSURE",
            "date": "1971-01-01",
            "predicted_value": 1030.4862869542915
        }
    ]
}'
curl --location --request DELETE 'http://localhost/v1/getValidPredictions' \
--header 'Content-Type: application/json' \
--data-raw '{
    "predictions": [
        {
            "aggregation_interval": "DAY",
            "aggregation_mode": "MIN",
            "data_type": "PRESSURE",
            "date": "1971-01-01",
            "predicted_value": 1007.3210722543249
        },
        {
            "aggregation_interval": "DAY",
            "aggregation_mode": "MIN",
            "data_type": "PRESSURE",
            "date": "1971-01-01",
            "predicted_value": 1015.3134745555662
        },
        {
            "aggregation_interval": "DAY",
            "aggregation_mode": "MIN",
            "data_type": "PRESSURE",
            "date": "1971-01-01",
            "predicted_value": 1030.4862869542915
        }
    ]
}'