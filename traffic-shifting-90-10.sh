kubectl apply -f istio/ingress.yaml
kubectl apply -f istio/traffic-shifting-90-10.yaml
sleep 5;
for i in {1..20}; \
do sleep 0.1; \
curl --location --request POST 'http://localhost/api/predict' \
--header 'Content-Type: application/json' \
--data-raw '{
    "type": "PRESSURE",
    "date": "1971-01-07",
    "accuracy": "HIGH"
}'; \
done