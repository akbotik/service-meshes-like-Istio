FROM python:latest
WORKDIR /usr/app/ms_anomaly_detection
COPY ./ ./
RUN pip install -r requirements.txt
CMD ["python", "ms_anomaly_detection.py"]