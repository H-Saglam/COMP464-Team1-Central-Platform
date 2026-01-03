# Serverless Architecture - Azure Event Hubs Component

## Team 1 - Central Warehouse

This directory contains the serverless components for the Hospital Supply Chain system using Azure Event Hubs and Azure Functions.

---

## Architecture Overview

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  Hospital   │────>│  Event Hub       │────>│ Azure Function  │────>│  Event Hub       │
│  Systems    │     │  (inventory-     │     │ (Stock Logic)   │     │  (order-         │
│             │     │   events)        │     │                 │     │   commands)      │
└─────────────┘     └──────────────────┘     └─────────────────┘     └──────────────────┘
                           │                         │
                           │                         │
                    InventoryLowEvent         OrderCreationCommand
                    (JSON Schema)             (JSON Schema)
```

---

## Prerequisites

1. **Python 3.9+**
2. **Azure Subscription** with:
   - Azure Event Hubs namespace
   - At least 2 Event Hubs:
     - `inventory-events` (input)
     - `order-commands` (output)
3. **Azure Functions Core Tools** (for local development)

---

## Setup Instructions

### 1. Install Dependencies

```bash
cd serverless
pip install -r requirements_serverless.txt
```

### 2. Configure Azure Connection String

**IMPORTANT:** You must set your real Azure Event Hubs connection string before running these scripts.

#### Option A: Environment Variable (Recommended)

```bash
# Linux/macOS
export EVENT_HUB_CONNECTION_STRING="Endpoint=sb://YOUR-NAMESPACE.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=YOUR-KEY"
export EVENT_HUB_NAME="inventory-events"

# Windows (PowerShell)
$env:EVENT_HUB_CONNECTION_STRING="Endpoint=sb://YOUR-NAMESPACE.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=YOUR-KEY"
$env:EVENT_HUB_NAME="inventory-events"
```

#### Option B: Azure Portal

1. Go to Azure Portal > Event Hubs Namespace
2. Click "Shared access policies"
3. Click "RootManageSharedAccessKey" (or create a new policy)
4. Copy the "Connection string–primary key"

#### Option C: local.settings.json (for Azure Functions)

Create `local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "EVENT_HUB_CONNECTION_STRING": "Endpoint=sb://YOUR-NAMESPACE...",
    "EVENT_HUB_NAME": "inventory-events"
  }
}
```

---

## Files Description

| File | Description |
|------|-------------|
| `requirements_serverless.txt` | Python dependencies for Azure Event Hubs |
| `event_producer_sim.py` | Simulates hospitals sending InventoryLowEvents |
| `stock_function_logic.py` | Azure Function logic with Decision Engine |
| `README_SERVERLESS.md` | This documentation file |

---

## Running the Scripts

### Test Event Producer (Simulation Mode)

Without Azure connection, runs in simulation mode:

```bash
python3 event_producer_sim.py
```

Output:
```
======================================================================
  HOSPITAL SUPPLY CHAIN - EVENT PRODUCER SIMULATOR
======================================================================

[SIMULATION] Using placeholder connection string - running in simulation mode
[SIMULATION] Event would be sent to Azure Event Hubs:
{
  "eventId": "evt-...",
  "eventType": "InventoryLow",
  "hospitalId": "Hospital-A",
  "productCode": "PHYSIO-SALINE",
  ...
}
```

### Test Function Logic (Standalone)

```bash
python3 stock_function_logic.py
```

This processes sample events and shows:
- Which events trigger orders
- Generated OrderCreationCommand payloads
- Priority decisions (URGENT/HIGH/NORMAL)

---

## Decision Engine Logic

The serverless Decision Engine mirrors the SOA/SOAP service logic:

| Days of Supply | Action | Priority |
|----------------|--------|----------|
| < 1.0 days | Trigger Order | **URGENT** |
| 1.0 - 2.0 days | Trigger Order | **HIGH** |
| >= 2.0 days | No Action | - |

### Order Quantity Calculation

```
orderQuantity = (dailyConsumptionUnits × 7) - currentStockUnits
```

Target: Restock to 7 days of supply.

---

## JSON Schemas

Events and commands follow strict JSON schemas:

### InventoryLowEvent (Input)

```json
{
  "eventId": "evt-uuid",
  "eventType": "InventoryLow",
  "hospitalId": "Hospital-A",
  "productCode": "PHYSIO-SALINE",
  "currentStockUnits": 40,
  "dailyConsumptionUnits": 30,
  "daysOfSupply": 1.33,
  "threshold": 2.0,
  "timestamp": "2026-01-03T12:00:00.000Z"
}
```

### OrderCreationCommand (Output)

```json
{
  "commandId": "cmd-uuid",
  "commandType": "CreateOrder",
  "orderId": "ORD-20260103-ABCD1234",
  "hospitalId": "Hospital-A",
  "productCode": "PHYSIO-SALINE",
  "orderQuantity": 170,
  "priority": "HIGH",
  "estimatedDeliveryDate": "2026-01-05T12:00:00.000Z",
  "warehouseId": "CENTRAL-WAREHOUSE",
  "timestamp": "2026-01-03T12:00:00.000Z"
}
```

---

## Deploying to Azure Functions

### 1. Create Function App

```bash
# Create resource group
az group create --name rg-hospital-supply --location westeurope

# Create storage account
az storage account create --name sthospitalsupply --resource-group rg-hospital-supply

# Create function app
az functionapp create \
  --name func-hospital-stock \
  --resource-group rg-hospital-supply \
  --storage-account sthospitalsupply \
  --consumption-plan-location westeurope \
  --runtime python \
  --runtime-version 3.9 \
  --functions-version 4
```

### 2. Create Azure Function Structure

```
func-hospital-stock/
├── host.json
├── requirements.txt
├── StockEventProcessor/
│   ├── __init__.py
│   └── function.json
└── stock_function_logic.py
```

### 3. function.json

```json
{
  "bindings": [
    {
      "type": "eventHubTrigger",
      "name": "events",
      "direction": "in",
      "eventHubName": "inventory-events",
      "connection": "EVENT_HUB_CONNECTION_STRING",
      "cardinality": "many",
      "consumerGroup": "$Default"
    },
    {
      "type": "eventHub",
      "name": "outputEvents",
      "direction": "out",
      "eventHubName": "order-commands",
      "connection": "EVENT_HUB_CONNECTION_STRING"
    }
  ]
}
```

### 4. __init__.py

```python
import azure.functions as func
import json
from stock_function_logic import process_events

def main(events: func.EventHubEvent, outputEvents: func.Out[str]):
    event_list = []
    for event in events:
        event_data = json.loads(event.get_body().decode('utf-8'))
        event_list.append(event_data)

    order_commands = process_events(event_list)

    if order_commands:
        outputEvents.set(json.dumps(order_commands))
```

---

## Comparison: SOA vs Serverless

| Aspect | SOA (SOAP) | Serverless (Event Hubs) |
|--------|------------|-------------------------|
| Protocol | SOAP/XML | JSON over AMQP |
| Latency | 100-1500ms (ESB simulated) | ~50-200ms |
| Scaling | Manual/VM-based | Automatic |
| Cost Model | Always-on | Pay-per-execution |
| Coupling | Synchronous | Asynchronous |

---

## Troubleshooting

### "Connection refused" Error

- Verify EVENT_HUB_CONNECTION_STRING is set correctly
- Check firewall rules in Azure Portal
- Ensure Event Hub exists with correct name

### "Unauthorized" Error

- Verify SharedAccessKey is correct
- Check policy has "Send" and "Listen" claims

### Events Not Processing

- Check consumer group exists ("$Default" or custom)
- Verify function is running and not throttled
- Check Application Insights for errors

---

## Contact

Team 1 - Central Warehouse
Hospital Supply Chain Project
