# 🏥 Central Medical Supply Chain Platform

![Python](https://img.shields.io/badge/Python-87.1%25-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12.1%25-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-0.8%25-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Azure](https://img.shields.io/badge/Azure-Cloud-0089D6?style=for-the-badge&logo=microsoft-azure&logoColor=white)
![SOAP](https://img.shields.io/badge/SOAP-1.1-orange?style=for-the-badge)

> **Central Warehouse (Team 1)** - A Service-Oriented Architecture (SOA) implementation for hospital supply chain management, featuring SOAP web services and Azure Event Hubs integration for real-time event processing.

## 📋 Project Overview

This project is the **Central Medical Supply Chain System (Warehouse)** developed as part of COMP464 course. It serves as the central hub for managing medical inventory across multiple hospitals, implementing:

- **SOAP Web Services** for stock updates and order management
- **Azure Event Hubs** for asynchronous critical event processing
- **Real-time Monitoring Dashboard** for supply chain analytics
- **Automated Decision Engine** for intelligent order triggering

### 🎯 Key Features

| Feature | Description |
|---------|-------------|
| **Stock Update Service** | Hospitals report daily inventory levels via SOAP |
| **Order Creation Service** | Manual and automated order processing |
| **Critical Event Handling** | Azure Event Hub for urgent stock alerts |
| **Decision Engine** | Automatic reorder triggering based on configurable thresholds |
| **Real-time Dashboard** | Streamlit-based monitoring with SOA vs Serverless comparison |
| **Full Audit Trail** | ESB logging and decision tracking |

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────��──────┐
│                        Hospital Systems (Clients)                    │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
    ┌─────────────────┐ ┌──────────────┐ ┌──────────────────┐
    │   SOAP Service  │ │ Event Hub    │ │   Dashboard      │
    │   (Port 8000)   │ │ (Serverless) │ │   (Streamlit)    │
    └────────┬────────┘ └──────┬───────┘ └────────┬─────────┘
             │                 │                   │
             ▼                 ▼                   ▼
    ┌─────────────────────────────────────────────────────────┐
    │              Azure PostgreSQL Database                   │
    │  ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌──────────┐ │
    │  │  Orders  │ │  Stock   │ │ Decision   │ │   ESB    │ │
    │  │          │ │  Events  │ │   Logs     │ │   Logs   │ │
    │  └──────────┘ └──────────┘ └────────────┘ └──────────┘ │
    └─────────────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **Python 3.9** - Core programming language
- **Flask** - Web framework for SOAP service hosting
- **Spyne** - SOAP/WSDL implementation framework
- **psycopg2** - PostgreSQL database adapter

### Cloud & Infrastructure
- **Azure Web Apps** - SOAP service deployment
- **Azure Event Hubs** - Serverless event streaming
- **Azure PostgreSQL** - Managed database service
- **Docker** - Containerization

### Frontend & Monitoring
- **Streamlit** - Interactive dashboard
- **Plotly** - Data visualization
- **Pandas** - Data analysis

## 📁 Project Structure

```
COMP464-Team1-Central-Platform/
├── 📄 real_soap_service.py      # Main SOAP service (StockUpdate + OrderCreation)
├── 📄 dashboard.py              # Streamlit monitoring dashboard
├── 📄 setup_db.py               # Database initialization script
├── 📄 test_azure_deployment.py  # Deployment testing utilities
│
├── 📂 contracts/                # WSDL contracts for SOA integration
├── 📂 database/                 # PostgreSQL schema definitions
├── 📂 serverless/               # Azure Functions for event processing
├── 📂 my-azure-function/        # Azure Function app configuration
├── 📂 mock-server/              # Mock services for testing
│
├── 📄 Dockerfile                # Container image definition
├── 📄 docker-compose.yml        # Multi-container orchestration
├── 📄 requirements_soa.txt      # Python dependencies (SOAP service)
├── 📄 requirements_dashboard.txt # Python dependencies (Dashboard)
│
├── 📄 INTEGRATION_GUIDE.md      # Client integration documentation
└── 📄 test_*.xml                # SOAP request test files
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Docker & Docker Compose
- Azure account (for cloud deployment)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/YunusogluKerem/COMP464-Team1-Central-Platform.git
   cd COMP464-Team1-Central-Platform
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements_soa.txt
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the services**
   - SOAP Service: `http://localhost:8000/CentralServices`
   - WSDL: `http://localhost:8000/CentralServices?wsdl`
   - Health Check: `http://localhost:8000/health`

### Running the Dashboard

```bash
pip install -r requirements_dashboard.txt
streamlit run dashboard.py
```

## 📡 API Reference

### SOAP Endpoints

**Base URL:** `http://localhost:8000/CentralServices`

#### StockUpdate
Reports hospital inventory levels. Triggers automatic orders when stock is critical.

```xml
<StockUpdateRequest>
  <hospitalId>HOSPITAL-A</hospitalId>
  <productCode>MORPHINE-10MG</productCode>
  <currentStockUnits>10</currentStockUnits>
  <dailyConsumptionUnits>5</dailyConsumptionUnits>
  <daysOfSupply>2.0</daysOfSupply>
  <timestamp>2026-01-08T09:00:00</timestamp>
</StockUpdateRequest>
```

**Response:**
- `success` - Operation status
- `orderTriggered` - Whether an automatic order was created
- `orderId` - Generated order ID (if triggered)

#### CreateOrder
Manual order creation for emergency situations.

```xml
<OrderCreationRequest>
  <hospitalId>HOSPITAL-A</hospitalId>
  <productCode>CRITICAL-MED</productCode>
  <orderQuantity>100</orderQuantity>
  <priority>URGENT</priority>
  <timestamp>2026-01-08T10:00:00</timestamp>
</OrderCreationRequest>
```

### Decision Engine Thresholds

| Condition | Priority | Action |
|-----------|----------|--------|
| Days of Supply < 1.0 | **URGENT** | Immediate order triggered |
| Days of Supply < 2.0 | **HIGH** | Priority order created |
| Days of Supply ≥ 2.0 | - | Stock adequate, no action |

## 📊 Dashboard Features

The Streamlit dashboard provides:

- **KPI Cards**: Total orders, processed events, pending orders, critical alerts
- **Architecture Comparison**: SOA vs Serverless latency metrics
- **Hospital Analytics**: Order distribution by hospital and priority
- **Throughput Trends**: 24-hour event processing visualization

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | PostgreSQL host | `localhost` |
| `POSTGRES_DB` | Database name | `hospital_db` |
| `POSTGRES_USER` | Database user | `app_user` |
| `POSTGRES_PASSWORD` | Database password | - |
| `DB_PORT` | Database port | `5432` |
| `PORT` | SOAP service port | `8000` |

## 🧪 Testing

Test files are provided for SOAP service validation:

```bash
# Test stock update
curl -X POST http://localhost:8000/CentralServices \
  -H "Content-Type: text/xml" \
  -d @test_request.xml

# Test order creation
curl -X POST http://localhost:8000/CentralServices \
  -H "Content-Type: text/xml" \
  -d @test_order.xml
```

## 🌐 Azure Deployment

The system is deployed on Azure with:

- **SOAP Service**: Azure Web App (Linux container)
- **Database**: Azure Database for PostgreSQL
- **Event Processing**: Azure Event Hubs + Azure Functions

**Live Endpoints:**
- WSDL: `http://team1-central-platform-*.azurewebsites.net/CentralServices?wsdl`
- Service: `http://team1-central-platform-*.azurewebsites.net/CentralServices`

## 📚 Integration Guide

For client teams integrating with this central platform, see the detailed [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) which includes:

- SOAP client examples (Python/Zeep)
- Azure Event Hub connection setup
- Sample code snippets
- Connection string configuration

## 👥 Team

**Team 1** - COMP464 Service-Oriented Architecture Course Project

## 📄 License

This project is part of an academic course (COMP464) and is intended for educational purposes.

---

<p align="center">
  <b>Central Medical Supply Chain Platform</b><br>
  SOA Implementation | Azure Cloud | Real-time Monitoring
</p>
