# 🏥 Central Medical Supply Chain Platform

> **COMP464 - Service Oriented Architecture | Team 1**  
> A comprehensive hospital supply chain management system demonstrating **SOA vs Serverless architecture** comparison.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Azure](https://img.shields.io/badge/Azure-Event%20Hubs%20%7C%20Functions-0078D4.svg)](https://azure.microsoft.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://docker.com)
[![SOAP](https://img.shields.io/badge/Protocol-SOAP%201.1-green.svg)](https://www.w3.org/TR/soap/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791.svg)](https://postgresql.org)

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Architecture](#-architecture)
- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [API Documentation](#-api-documentation)
- [Dashboard](#-dashboard)
- [Integration Guide](#-integration-guide)
- [Performance Comparison](#-performance-comparison)
- [Team Information](#-team-information)

---

## 🎯 Project Overview

This project implements a **Central Medical Supply Chain Platform** that acts as the central warehouse system for a network of hospitals. The system processes inventory updates from hospitals, automatically triggers supply orders when stock levels are critical, and provides real-time monitoring capabilities.

### Key Objectives

- **Architecture Comparison**: Implement the same business logic using both SOA (SOAP) and Serverless (Azure Event Hubs + Functions) architectures
- **Automated Decision Making**: Intelligent ordering system that automatically creates orders when hospital stock levels fall below thresholds
- **Real-time Monitoring**: Streamlit dashboard for performance comparison and supply chain visualization
- **Enterprise Integration**: Standard WSDL/SOAP contracts and JSON schemas for seamless integration with hospital systems

---

## 🏗 Architecture

The platform implements a **dual-architecture approach** for academic comparison:

### High-Level Architecture

```
                                    ┌─────────────────────────────────────┐
                                    │      Central Warehouse Platform     │
                                    │             (Team 1)                │
                                    └─────────────────────────────────────┘
                                                    │
                    ┌───────────────────────────────┼───────────────────────────────┐
                    │                               │                               │
            ┌───────▼───────┐               ┌───────▼───────┐               ┌───────▼───────┐
            │  SOA / SOAP   │               │  Serverless   │               │   Dashboard   │
            │   Service     │               │ Azure Events  │               │   Streamlit   │
            └───────────────┘               └───────────────┘               └───────────────┘
                    │                               │                               │
                    │         ┌─────────────────────┤                               │
                    │         │                     │                               │
            ┌───────▼─────────▼─────────────────────▼───────────────────────────────▼───────┐
            │                           Azure PostgreSQL Database                            │
            │    StockEvents │ Orders │ DecisionLogs │ ESBLogs │ PerformanceMetrics         │
            └───────────────────────────────────────────────────────────────────────────────┘
```

### SOA Architecture (SOAP)

```
┌──────────────┐     SOAP/XML      ┌──────────────────────┐     SQL      ┌──────────────┐
│   Hospital   │ ────────────────> │   Flask + Spyne      │ ──────────> │  PostgreSQL  │
│   Systems    │                   │   SOAP Web Service   │              │   Database   │
└──────────────┘                   └──────────────────────┘              └──────────────┘
                                            │
                                   StockUpdateService
                                   OrderCreationService
```

### Serverless Architecture (Azure Event Hubs)

```
┌──────────────┐     JSON/AMQP     ┌──────────────────┐     Trigger     ┌──────────────────┐
│   Hospital   │ ────────────────> │  Azure Event Hub │ ─────────────> │  Azure Function  │
│   Systems    │                   │ inventory-events │                 │ StockProcessor   │
└──────────────┘                   └──────────────────┘                 └──────────────────┘
                                                                                │
                                            ┌───────────────────────────────────┘
                                            │
                                            ▼
                                   ┌──────────────────┐     SQL      ┌──────────────┐
                                   │  Azure Event Hub │ ──────────> │  PostgreSQL  │
                                   │  order-commands  │              │   Database   │
                                   └──────────────────┘              └──────────────┘
```

---

## ✨ Features

### Core Functionality

| Feature | Description |
|---------|-------------|
| **Stock Update Processing** | Process real-time inventory updates from hospitals |
| **Automated Order Creation** | Intelligent decision engine triggers orders when stock is critical |
| **Manual Order Support** | Support for emergency/manual order creation |
| **Performance Logging** | Track latency, throughput, and error rates |
| **Architecture Comparison** | Side-by-side SOA vs Serverless metrics |

### Decision Engine Logic

The system uses the following thresholds for automated ordering:

| Days of Supply | Action | Priority |
|----------------|--------|----------|
| < 1.0 days | **Trigger Order** | 🔴 URGENT |
| 1.0 - 2.0 days | **Trigger Order** | 🟠 HIGH |
| ≥ 2.0 days | No Action | ✅ Adequate |

**Order Quantity Calculation:**
```
orderQuantity = (dailyConsumptionUnits × 7) - currentStockUnits
```
*Target: Restock to 7 days of supply*

---

## 🛠 Technology Stack

### Backend

| Technology | Purpose |
|------------|---------|
| **Python 3.9+** | Primary programming language |
| **Flask** | Web framework for SOAP service |
| **Spyne** | SOAP/WSDL implementation |
| **Azure Functions** | Serverless compute |
| **Azure Event Hubs** | Event streaming platform |
| **PostgreSQL** | Relational database |
| **psycopg2 / pg8000** | Database drivers |

### Frontend

| Technology | Purpose |
|------------|---------|
| **Streamlit** | Interactive monitoring dashboard |
| **Plotly** | Data visualization |
| **Pandas** | Data manipulation |

### Infrastructure

| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Multi-container orchestration |
| **Azure App Service** | Cloud hosting |
| **Azure Database for PostgreSQL** | Managed database |

---

## 📁 Project Structure

```
COMP464-Team1-Central-Platform/
│
├── 📄 real_soap_service.py      # Main SOAP service (Flask + Spyne)
├── 📄 dashboard.py              # Streamlit monitoring dashboard
├── 📄 setup_db.py               # Database initialization script
├── 📄 test_azure_deployment.py  # Azure Event Hub test client
│
├── 📁 contracts/                # Service contracts
│   ├── 📁 schemas/              # JSON schemas for serverless
│   │   ├── InventoryLowEvent.schema.json
│   │   └── OrderCreationCommand.schema.json
│   └── 📁 wsdl/                 # WSDL definitions for SOAP
│       ├── CentralServices.wsdl
│       └── StockUpdateService.wsdl
│
├── 📁 database/                 # Database scripts
│   └── init.sql                 # Full schema with tables, indexes, views
│
├── 📁 mock-server/              # Mock SOAP server for testing
│   ├── app.py
│   ├── requirements.txt
│   └── test_request.xml
│
├── 📁 my-azure-function/        # Deployed Azure Function
│   ├── host.json
│   ├── requirements.txt
│   └── 📁 StockEventProcessor/  # Function implementation
│       ├── __init__.py          # Main function logic
│       ├── function.json        # Bindings configuration
│       └── stock_function_logic.py
│
├── 📁 serverless/               # Serverless development files
│   ├── README_SERVERLESS.md     # Serverless documentation
│   ├── event_producer_sim.py    # Event producer simulator
│   ├── stock_function_logic.py  # Decision engine logic
│   └── requirements_serverless.txt
│
├── 📄 Dockerfile                # Container definition
├── 📄 docker-compose.yml        # Docker orchestration
├── 📄 requirements_soa.txt      # SOAP service dependencies
├── 📄 requirements_dashboard.txt # Dashboard dependencies
├── 📄 INTEGRATION_GUIDE.md      # Client integration guide
└── 📄 .gitignore               # Git ignore rules
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Docker & Docker Compose
- Azure subscription (for cloud deployment)
- PostgreSQL (local or Azure)

### Option 1: Docker Deployment

```bash
# Clone the repository
git clone https://github.com/H-Saglam/COMP464-Team1-Central-Platform.git
cd COMP464-Team1-Central-Platform

# Build and run with Docker Compose
docker-compose up --build
```

The SOAP service will be available at `http://localhost:8000/CentralServices`

### Option 2: Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements_soa.txt

# Set environment variables
export DB_HOST=localhost
export POSTGRES_DB=hospital_db
export POSTGRES_USER=app_user
export POSTGRES_PASSWORD=secure_password
export DB_PORT=5432

# Initialize database
python setup_db.py

# Run the SOAP service
python real_soap_service.py
```

### Option 3: Running the Dashboard

```bash
# Install dashboard dependencies
pip install -r requirements_dashboard.txt

# Run Streamlit dashboard
streamlit run dashboard.py
```

---

## 📖 API Documentation

### SOAP Services

#### Service Endpoint
- **URL**: `http://localhost:8000/CentralServices`
- **WSDL**: `http://localhost:8000/CentralServices?wsdl`
- **Protocol**: SOAP 1.1

#### StockUpdate Operation

**Request:**
```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="http://hospital-supply-chain.example.com/soap/stock">
    <soap:Body>
        <tns:StockUpdateRequest>
            <tns:hospitalId>HOSPITAL-A</tns:hospitalId>
            <tns:productCode>MORPHINE-10MG</tns:productCode>
            <tns:currentStockUnits>10</tns:currentStockUnits>
            <tns:dailyConsumptionUnits>5</tns:dailyConsumptionUnits>
            <tns:daysOfSupply>2.0</tns:daysOfSupply>
            <tns:timestamp>2026-01-08T09:00:00</tns:timestamp>
        </tns:StockUpdateRequest>
    </soap:Body>
</soap:Envelope>
```

**Response:**
```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <StockUpdateResult>
            <success>true</success>
            <message>Order created: ORD-20260108-ABC12345</message>
            <orderTriggered>true</orderTriggered>
            <orderId>ORD-20260108-ABC12345</orderId>
        </StockUpdateResult>
    </soap:Body>
</soap:Envelope>
```

#### CreateOrder Operation

**Request:**
```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="http://hospital-supply-chain.example.com/soap/order">
    <soap:Body>
        <tns:OrderCreationRequest>
            <tns:hospitalId>HOSPITAL-A</tns:hospitalId>
            <tns:productCode>EMERGENCY-KIT</tns:productCode>
            <tns:orderQuantity>100</tns:orderQuantity>
            <tns:priority>URGENT</tns:priority>
            <tns:timestamp>2026-01-08T10:00:00</tns:timestamp>
        </tns:OrderCreationRequest>
    </soap:Body>
</soap:Envelope>
```

### Serverless Events (Azure Event Hubs)

#### InventoryLowEvent (Input)

```json
{
  "eventId": "evt-550e8400-e29b-41d4-a716-446655440000",
  "eventType": "InventoryLow",
  "hospitalId": "HOSPITAL-A",
  "productCode": "PHYSIO-SALINE",
  "currentStockUnits": 40,
  "dailyConsumptionUnits": 30,
  "daysOfSupply": 1.33,
  "threshold": 2.0,
  "timestamp": "2026-01-03T12:00:00.000Z"
}
```

#### OrderCreationCommand (Output)

```json
{
  "commandId": "cmd-550e8400-e29b-41d4-a716-446655440001",
  "commandType": "CreateOrder",
  "orderId": "ORD-20260103-ABCD1234",
  "hospitalId": "HOSPITAL-A",
  "productCode": "PHYSIO-SALINE",
  "orderQuantity": 170,
  "priority": "HIGH",
  "estimatedDeliveryDate": "2026-01-05T12:00:00.000Z",
  "warehouseId": "CENTRAL-WAREHOUSE",
  "timestamp": "2026-01-03T12:00:00.000Z"
}
```

---

## 📊 Dashboard

The Streamlit dashboard provides real-time monitoring and architecture comparison:

### Dashboard Features

- **KPI Cards**: Total orders, stock events, pending orders, critical alerts
- **Architecture Comparison**: SOA vs Serverless latency and throughput
- **Hospital Analytics**: Order distribution by hospital and priority
- **Time Series**: Event throughput trends over 24 hours

### Running the Dashboard

```bash
streamlit run dashboard.py
```

Access at: `http://localhost:8501`

---

## 🔗 Integration Guide

For detailed integration instructions, see [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md).

### Quick Start for Client Teams

#### Python SOAP Client (using Zeep)

```python
from zeep import Client

wsdl = 'http://localhost:8000/CentralServices?wsdl'
client = Client(wsdl=wsdl)

# Stock Update Example
response = client.service.StockUpdate({
    'hospitalId': 'HOSPITAL-X',
    'productCode': 'MORPHINE-10MG',
    'currentStockUnits': 10,
    'dailyConsumptionUnits': 5,
    'daysOfSupply': 2.0,
    'timestamp': '2026-01-08T09:00:00'
})
print("Response:", response)
```

#### Azure Event Hub Client

```python
import asyncio
import json
from azure.eventhub import EventData, TransportType
from azure.eventhub.aio import EventHubProducerClient

CONNECTION_STR = "Endpoint=sb://..."  # Get from Team 1
EVENT_HUB_NAME = "inventory-low-events"

async def send_event():
    producer = EventHubProducerClient.from_connection_string(
        conn_str=CONNECTION_STR,
        eventhub_name=EVENT_HUB_NAME,
        transport_type=TransportType.AmqpOverWebsocket
    )
    
    async with producer:
        event_batch = await producer.create_batch()
        event_data = {
            "hospitalId": "HOSPITAL-X",
            "productCode": "CRITICAL-MEDICINE",
            "currentStockUnits": 5,
            "dailyConsumptionUnits": 10,
            "daysOfSupply": 0.5,
            "threshold": 2.0,
            "timestamp": "2026-01-08T10:30:00"
        }
        event_batch.add(EventData(json.dumps(event_data)))
        await producer.send_batch(event_batch)

asyncio.run(send_event())
```

---

## 📈 Performance Comparison

### SOA vs Serverless

| Metric | SOA (SOAP) | Serverless (Event Hubs) |
|--------|------------|-------------------------|
| **Protocol** | SOAP/XML | JSON over AMQP |
| **Latency** | 100-1500ms | ~50-200ms |
| **Scaling** | Manual/VM-based | Automatic |
| **Cost Model** | Always-on | Pay-per-execution |
| **Coupling** | Synchronous | Asynchronous |
| **Contract** | WSDL/XSD | JSON Schema |

### Database Schema

The shared database enables fair comparison:

- **StockEvents**: All incoming inventory events
- **Orders**: Created orders (both architectures)
- **DecisionLogs**: Audit trail of decisions
- **ESBLogs**: Latency and performance metrics
- **PerformanceMetrics**: Aggregated metrics

---

## 🏆 Team Information

**Team 1 - Central Warehouse**  
COMP464 - Service Oriented Architecture Course Project

### Deployment URLs

| Service | URL |
|---------|-----|
| **SOAP Service** | `http://team1-central-platform-eqajhdbjbggkfxhf.westeurope-01.azurewebsites.net/CentralServices` |
| **WSDL** | `http://team1-central-platform-eqajhdbjbggkfxhf.westeurope-01.azurewebsites.net/CentralServices?wsdl` |
| **Event Hub** | `inventory-low-events` (connection string available on request) |

---

## 📄 License

This project is developed for educational purposes as part of COMP464 course.

---

## 🤝 Contributing

This is a course project. For questions or integration support, please contact Team 1 through the course communication channels.

---

<div align="center">
  <strong>🏥 Hospital Supply Chain - Central Platform</strong><br>
  Built with ❤️ by Team 1 | COMP464
</div>
