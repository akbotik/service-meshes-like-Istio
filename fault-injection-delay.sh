kubectl apply -f istio/ingress.yaml
kubectl apply -f istio/fault-injection-delay.yaml
sleep 5;
curl --location --request POST 'http://localhost/api/predict?predictionModel=Prophet' \
--header 'Content-Type: application/json' \
--data-raw '{
    "type": "PRESSURE",
    "date": "1971-01-07",
    "accuracy": "HIGH"
}'
curl --location --request POST 'http://localhost/api/predict' \
--header 'Content-Type: application/json' \
--data-raw '{
    "type": "PRESSURE",
    "date": "1971-01-07",
    "accuracy": "HIGH"
}'