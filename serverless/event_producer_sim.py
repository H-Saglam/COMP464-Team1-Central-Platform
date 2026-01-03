"""
Event Producer Simulator for Hospital Supply Chain
Simulates a Hospital sending 'InventoryLowEvent' to Azure Event Hubs

This script demonstrates how hospitals would publish low inventory events
to the Azure Event Hubs for serverless processing.

Usage:
    1. Set your Azure Event Hubs connection string in environment variable
    2. Run: python3 event_producer_sim.py

Environment Variables:
    EVENT_HUB_CONNECTION_STRING: Azure Event Hubs connection string
    EVENT_HUB_NAME: Event Hub name (default: inventory-events)
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

# Azure Event Hubs SDK
try:
    from azure.eventhub import EventHubProducerClient, EventData
    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False
    print("WARNING: azure-eventhub not installed. Running in simulation mode.")


# ============================================
# Configuration
# ============================================

# Placeholder connection string - User must replace with real one
DEFAULT_CONNECTION_STRING = (
    "Endpoint=sb://mock-hub.servicebus.windows.net/;"
    "SharedAccessKeyName=RootManageSharedAccessKey;"
    "SharedAccessKey=PLACEHOLDER_KEY_REPLACE_ME"
)

DEFAULT_EVENT_HUB_NAME = "inventory-events"


# ============================================
# InventoryLowEvent Generator
# ============================================

class InventoryLowEventGenerator:
    """
    Generates InventoryLowEvent payloads matching the JSON schema.
    Schema: contracts/schemas/InventoryLowEvent.schema.json
    """

    @staticmethod
    def create_event(
        hospital_id: str,
        product_code: str,
        current_stock_units: int,
        daily_consumption_units: int,
        threshold: float = 2.0,
        event_id: Optional[str] = None
    ) -> dict:
        """
        Create an InventoryLowEvent payload.

        Args:
            hospital_id: Unique hospital identifier
            product_code: Product/SKU code
            current_stock_units: Current inventory level
            daily_consumption_units: Daily consumption rate
            threshold: Days of supply threshold that triggered this event
            event_id: Optional custom event ID (auto-generated if not provided)

        Returns:
            dict: Event payload matching InventoryLowEvent.schema.json
        """
        # Calculate days of supply
        if daily_consumption_units > 0:
            days_of_supply = round(current_stock_units / daily_consumption_units, 2)
        else:
            days_of_supply = float('inf') if current_stock_units > 0 else 0.0

        # Generate event
        event = {
            "eventId": event_id or f"evt-{uuid.uuid4()}",
            "eventType": "InventoryLow",
            "hospitalId": hospital_id,
            "productCode": product_code,
            "currentStockUnits": current_stock_units,
            "dailyConsumptionUnits": daily_consumption_units,
            "daysOfSupply": days_of_supply,
            "threshold": threshold,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        return event


# ============================================
# Event Hub Producer
# ============================================

class EventHubEventProducer:
    """
    Sends events to Azure Event Hubs.
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        event_hub_name: Optional[str] = None
    ):
        """
        Initialize the Event Hub producer.

        Args:
            connection_string: Azure Event Hubs connection string
            event_hub_name: Name of the Event Hub
        """
        self.connection_string = connection_string or os.environ.get(
            "EVENT_HUB_CONNECTION_STRING",
            DEFAULT_CONNECTION_STRING
        )
        self.event_hub_name = event_hub_name or os.environ.get(
            "EVENT_HUB_NAME",
            DEFAULT_EVENT_HUB_NAME
        )
        self.producer = None

    def _is_placeholder_connection(self) -> bool:
        """Check if using placeholder connection string."""
        return "PLACEHOLDER" in self.connection_string or "mock-hub" in self.connection_string

    def connect(self):
        """Establish connection to Event Hub."""
        if not AZURE_SDK_AVAILABLE:
            print("[SIMULATION] Azure SDK not available - running in simulation mode")
            return

        if self._is_placeholder_connection():
            print("[SIMULATION] Using placeholder connection string - running in simulation mode")
            print("[SIMULATION] Set EVENT_HUB_CONNECTION_STRING environment variable for real connection")
            return

        try:
            self.producer = EventHubProducerClient.from_connection_string(
                conn_str=self.connection_string,
                eventhub_name=self.event_hub_name
            )
            print(f"[CONNECTED] Connected to Event Hub: {self.event_hub_name}")
        except Exception as e:
            print(f"[ERROR] Failed to connect to Event Hub: {e}")
            self.producer = None

    def send_event(self, event: dict) -> bool:
        """
        Send a single event to Event Hub.

        Args:
            event: Event payload dictionary

        Returns:
            bool: True if sent successfully (or simulated)
        """
        event_json = json.dumps(event, indent=2)

        print("\n" + "=" * 60)
        print("SENDING INVENTORY LOW EVENT")
        print("=" * 60)
        print(f"Event ID: {event.get('eventId')}")
        print(f"Hospital: {event.get('hospitalId')}")
        print(f"Product: {event.get('productCode')}")
        print(f"Current Stock: {event.get('currentStockUnits')} units")
        print(f"Daily Consumption: {event.get('dailyConsumptionUnits')} units")
        print(f"Days of Supply: {event.get('daysOfSupply')}")
        print(f"Threshold: {event.get('threshold')} days")
        print("-" * 60)

        if self.producer is None:
            print("[SIMULATION MODE] Event would be sent to Azure Event Hubs:")
            print(event_json)
            print("[SIMULATION] Event simulated successfully!")
            return True

        try:
            # Create batch and add event
            event_data_batch = self.producer.create_batch()
            event_data_batch.add(EventData(json.dumps(event)))

            # Send the batch
            self.producer.send_batch(event_data_batch)
            print(f"[SUCCESS] Event sent to Event Hub: {self.event_hub_name}")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to send event: {e}")
            return False

    def send_batch(self, events: list) -> bool:
        """
        Send multiple events as a batch.

        Args:
            events: List of event payload dictionaries

        Returns:
            bool: True if all sent successfully
        """
        print(f"\n[BATCH] Sending {len(events)} events...")

        if self.producer is None:
            for event in events:
                self.send_event(event)
            return True

        try:
            event_data_batch = self.producer.create_batch()

            for event in events:
                event_data_batch.add(EventData(json.dumps(event)))

            self.producer.send_batch(event_data_batch)
            print(f"[SUCCESS] Batch of {len(events)} events sent successfully!")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to send batch: {e}")
            return False

    def close(self):
        """Close the producer connection."""
        if self.producer:
            self.producer.close()
            print("[DISCONNECTED] Event Hub connection closed")


# ============================================
# Main Simulation
# ============================================

def run_simulation():
    """Run the event producer simulation."""
    print("=" * 70)
    print("  HOSPITAL SUPPLY CHAIN - EVENT PRODUCER SIMULATOR")
    print("  Serverless Architecture (Team 1)")
    print("=" * 70)
    print()

    # Create event generator
    generator = InventoryLowEventGenerator()

    # Create sample events
    print("[INFO] Generating sample InventoryLowEvent...")

    # Primary test case: Hospital-A with low stock
    event1 = generator.create_event(
        hospital_id="Hospital-A",
        product_code="PHYSIO-SALINE",
        current_stock_units=40,
        daily_consumption_units=30,
        threshold=2.0
    )

    # Additional test cases
    event2 = generator.create_event(
        hospital_id="Hospital-B",
        product_code="SURGICAL-GLOVES-M",
        current_stock_units=100,
        daily_consumption_units=80,
        threshold=2.0
    )

    event3 = generator.create_event(
        hospital_id="Hospital-A",
        product_code="N95-MASKS",
        current_stock_units=25,
        daily_consumption_units=50,  # Very critical - 0.5 days!
        threshold=2.0
    )

    # Create producer and connect
    producer = EventHubEventProducer()
    producer.connect()

    try:
        # Send events
        producer.send_event(event1)
        producer.send_event(event2)
        producer.send_event(event3)

        print("\n" + "=" * 60)
        print("SIMULATION COMPLETE")
        print("=" * 60)
        print(f"Total events sent: 3")
        print()
        print("Next Steps:")
        print("  1. Set EVENT_HUB_CONNECTION_STRING with your real Azure connection")
        print("  2. Run stock_function_logic.py to see how events are processed")
        print("  3. Deploy to Azure Functions for production use")
        print("=" * 60)

    finally:
        producer.close()


if __name__ == "__main__":
    run_simulation()
