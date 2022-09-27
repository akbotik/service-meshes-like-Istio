kubectl apply -f istio/ingress.yaml
kubectl apply -f istio/traffic-shifting-0-100.yaml
sleep 5;
curl --location --request POST 'http://localhost/api/predict?predictionModel=Prophet' \
--header 'Content-Type: application/json' \
--data-raw '{
    "type": "PRESSURE",
    "date": "1971-01-07",
    "accuracy": "HIGH"
}'