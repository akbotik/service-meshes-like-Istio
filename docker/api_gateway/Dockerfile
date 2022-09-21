FROM python:latest
WORKDIR /usr/app/api_gateway
COPY ./ ./
RUN pip install -r requirements.txt
CMD ["python", "api_gateway.py"]