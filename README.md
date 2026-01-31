# Service Meshes like Istio

A [bachelor thesis](/thesis/Aitbayeva_thesis.pdf) project demonstrating the implementation of a microservices architecture with Istio service mesh capabilities.

## Overview

This project showcases a microservices system with Istio service mesh integration, featuring traffic management, fault injection, load balancing, request routing, and observability patterns. It includes multiple interconnected microservices processing IoT data for prediction and anomaly detection.

## Architecture

The system consists of the following microservices:

- **API Gateway**: Entry point for all external requests
- **MS IoT**: Internet of Things data ingestion service
- **MS Prediction**: Machine learning prediction service
- **MS Prediction Advanced**: Advanced prediction algorithms
- **MS Anomaly Detection**: Real-time anomaly detection service
- **MS Analytics**: Data analytics service
- **MS Fog**: Fog computing and aggregation service
- **Application Runner**: Runs data generation and simu-
lates common client activity

## Technology Stack

### Container & Orchestration
- Docker (20.10.17)
- Kubernetes (v1.24.3)
- minikube (v1.26.1)
- kubectl (v1.25.0)

### Service Mesh
- Istio (v1.15.0)

### Backend

#### Java
- **Version**: 11
- **Build Tool**: Apache Maven
- **Framework**: Spring Boot
- **Library**: Project Lombok

#### Python
- **Version**: 3.10
- **Framework**: Flask

### Machine Learning
- Scikit-learn
- Prophet
- Darts
- Anomaly Detection Toolkit (ADTK)

### Database
- PostgreSQL

### Monitoring & Observability
- Prometheus
- Kiali
- Grafana

## Project Structure

```
.
├── docker/              # Docker configurations for each microservice
├── implementation/      # Source code for microservices
├── kubernetes/          # Kubernetes deployment manifests
│   ├── deployments-v1/  # Initial deployment version
│   └── deployments-v2/  # Updated deployment version
├── istio/               # Istio configuration files
├── diagrams/            # Architecture and design diagrams
├── thesis/              # Thesis document and related files
├── postman/             # API testing collections
└── scripts              # Deployment and management scripts
```

## Features

### Traffic Management
- **Ingress**: Configure ingress gateway for external traffic control
- **Request Routing**: Route traffic based on request properties
- **Traffic Shifting**: Gradually shift traffic between versions
- **Load Balancing**: Distribute requests across services
- **Mirroring**: Mirror traffic to secondary services

### Fault Tolerance
- **Fault Injection**: Inject delays and aborts for resilience testing
- **Retry Policies**: Automatic retry mechanisms
- **Timeouts**: Request timeout management

### Observability
- **Service Mesh Visibility**: Kiali dashboards for real-time mesh topology and traffic visualization
- **Metrics**: Prometheus integration for performance monitoring
- **Dashboards**: Custom dashboards for metrics analysis

## Testing

Use the included Postman collections to test the APIs.

## Deployment Versions

### V1 - Initial Deployment
Basic Kubernetes deployment without traffic splitting

### V2 - Advanced Deployment
Enhanced deployment with multiple versions for traffic shifting and canary deployments

## System Diagrams

Architecture and design diagrams are available in the `diagrams/` directory:
- System architecture overview
- System sequence diagrams
- Microservice-specific activity and class diagrams

## License

This project is part of a bachelor thesis at the University of Vienna.

## Project Status

This project represents completed thesis work demonstrating Istio service mesh capabilities with a production-like microservices architecture.
