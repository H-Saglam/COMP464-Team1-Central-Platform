"""
Stock Function Logic for Azure Functions
Processes InventoryLowEvents and generates OrderCreationCommands

This module contains the core business logic that will be deployed
as an Azure Function triggered by Event Hubs.

Usage (standalone testing):
    python3 stock_function_logic.py

In Azure Functions:
    Import process_events() in your __init__.py
"""

import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional


# ============================================
# Decision Engine (Same as SOAP Service)
# ============================================

class ServerlessDecisionEngine:
    """
    Decision Engine for Serverless Architecture.
    Mirrors the logic from the SOAP service for consistency.
    """

    # Configuration thresholds
    THRESHOLD_CRITICAL = 2.0  # Days - trigger order if daysOfSupply < threshold
    THRESHOLD_URGENT = 1.0    # Days - mark as URGENT priority
    RESTOCK_DAYS = 7          # Target days of supply after restock

    @staticmethod
    def evaluate(event: dict) -> dict:
        """
        Evaluate an InventoryLowEvent and decide on order creation.

        Args:
            event: InventoryLowEvent payload

        Returns:
            dict with keys: should_order, priority, order_quantity, reason
        """
        days_of_supply = float(event.get('daysOfSupply', 999))
        threshold = float(event.get('threshold', ServerlessDecisionEngine.THRESHOLD_CRITICAL))
        daily_consumption = int(event.get('dailyConsumptionUnits', 0))
        current_stock = int(event.get('currentStockUnits', 0))

        result = {
            'should_order': False,
            'priority': None,
            'order_quantity': 0,
            'reason': '',
            'days_of_supply': days_of_supply,
            'threshold_used': threshold
        }

        # Decision: Should we trigger an order?
        if days_of_supply < threshold:
            result['should_order'] = True

            # Calculate order quantity: (daily * 7) - current
            target_stock = daily_consumption * ServerlessDecisionEngine.RESTOCK_DAYS
            result['order_quantity'] = max(target_stock - current_stock, daily_consumption)

            # Determine priority based on urgency
            if days_of_supply < ServerlessDecisionEngine.THRESHOLD_URGENT:
                result['priority'] = 'URGENT'
                result['reason'] = (
                    f'CRITICAL: Only {days_of_supply:.1f} days of supply remaining '
                    f'(< {ServerlessDecisionEngine.THRESHOLD_URGENT} day)'
                )
            else:
                result['priority'] = 'HIGH'
                result['reason'] = (
                    f'LOW STOCK: {days_of_supply:.1f} days of supply remaining '
                    f'(< {threshold} days)'
                )
        else:
            result['reason'] = f'Stock levels adequate: {days_of_supply:.1f} days of supply'

        return result


# ============================================
# Order Command Generator
# ============================================

class OrderCommandGenerator:
    """
    Generates OrderCreationCommand payloads matching the JSON schema.
    Schema: contracts/schemas/OrderCreationCommand.schema.json
    """

    DEFAULT_WAREHOUSE = "CENTRAL-WAREHOUSE"

    @staticmethod
    def create_command(
        event: dict,
        decision: dict,
        command_id: Optional[str] = None,
        order_id: Optional[str] = None
    ) -> dict:
        """
        Create an OrderCreationCommand from an event and decision.

        Args:
            event: Original InventoryLowEvent
            decision: Decision engine result
            command_id: Optional custom command ID
            order_id: Optional custom order ID

        Returns:
            dict: Command payload matching OrderCreationCommand.schema.json
        """
        now = datetime.now(timezone.utc)

        # Calculate estimated delivery based on priority
        if decision['priority'] == 'URGENT':
            delivery_days = 1  # Next day delivery for urgent
        elif decision['priority'] == 'HIGH':
            delivery_days = 2  # 2-day delivery for high priority
        else:
            delivery_days = 5  # Standard delivery

        estimated_delivery = now + timedelta(days=delivery_days)

        command = {
            "commandId": command_id or f"cmd-{uuid.uuid4()}",
            "commandType": "CreateOrder",
            "orderId": order_id or f"ORD-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}",
            "hospitalId": event.get('hospitalId'),
            "productCode": event.get('productCode'),
            "orderQuantity": decision['order_quantity'],
            "priority": decision['priority'],
            "estimatedDeliveryDate": estimated_delivery.isoformat(),
            "warehouseId": OrderCommandGenerator.DEFAULT_WAREHOUSE,
            "timestamp": now.isoformat()
        }

        return command


# ============================================
# Event Processor (Azure Function Logic)
# ============================================

def process_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a batch of InventoryLowEvents.

    This is the main function that will be called by Azure Functions.
    It evaluates each event and generates OrderCreationCommands as needed.

    Args:
        events: List of InventoryLowEvent payloads

    Returns:
        List of OrderCreationCommand payloads for triggered orders
    """
    print("\n" + "=" * 70)
    print("  SERVERLESS EVENT PROCESSOR")
    print("  Processing InventoryLowEvents...")
    print("=" * 70)

    decision_engine = ServerlessDecisionEngine()
    command_generator = OrderCommandGenerator()
    order_commands = []

    for i, event in enumerate(events, 1):
        print(f"\n--- Event {i}/{len(events)} ---")
        print(f"Event ID: {event.get('eventId')}")
        print(f"Hospital: {event.get('hospitalId')}")
        print(f"Product: {event.get('productCode')}")
        print(f"Current Stock: {event.get('currentStockUnits')} units")
        print(f"Daily Consumption: {event.get('dailyConsumptionUnits')} units")
        print(f"Days of Supply: {event.get('daysOfSupply')}")
        print(f"Threshold: {event.get('threshold')} days")

        # Run decision engine
        decision = decision_engine.evaluate(event)

        if decision['should_order']:
            print(f"\n  >>> TRIGGER ORDER COMMAND <<<")
            print(f"  Reason: {decision['reason']}")
            print(f"  Priority: {decision['priority']}")
            print(f"  Order Quantity: {decision['order_quantity']} units")

            # Generate order command
            command = command_generator.create_command(event, decision)
            order_commands.append(command)

            print(f"\n  Generated OrderCreationCommand:")
            print(f"  {json.dumps(command, indent=4)}")
        else:
            print(f"\n  [OK] No order needed: {decision['reason']}")

    # Summary
    print("\n" + "=" * 70)
    print("  PROCESSING COMPLETE")
    print("=" * 70)
    print(f"  Total events processed: {len(events)}")
    print(f"  Orders triggered: {len(order_commands)}")

    if order_commands:
        print("\n  Orders to be sent to Order Creation Hub:")
        for cmd in order_commands:
            print(f"    - {cmd['orderId']}: {cmd['productCode']} "
                  f"({cmd['orderQuantity']} units, {cmd['priority']})")

    print("=" * 70)

    return order_commands


# ============================================
# Azure Function Entry Point (Template)
# ============================================

def azure_function_main(events):
    """
    Template for Azure Function entry point.

    In your Azure Function's __init__.py, use:

    ```python
    import azure.functions as func
    from stock_function_logic import process_events
    import json

    def main(events: func.EventHubEvent):
        # Parse events
        event_list = []
        for event in events:
            event_data = json.loads(event.get_body().decode('utf-8'))
            event_list.append(event_data)

        # Process events
        order_commands = process_events(event_list)

        # TODO: Send order_commands to output Event Hub
        # output.set(json.dumps(order_commands))
    ```
    """
    pass


# ============================================
# Standalone Test
# ============================================

def run_standalone_test():
    """Run standalone test with sample events."""
    print("=" * 70)
    print("  HOSPITAL SUPPLY CHAIN - STOCK FUNCTION LOGIC TEST")
    print("  Serverless Architecture (Team 1)")
    print("=" * 70)

    # Sample events (simulating what would come from Event Hubs)
    test_events = [
        {
            "eventId": "evt-test-001",
            "eventType": "InventoryLow",
            "hospitalId": "Hospital-A",
            "productCode": "PHYSIO-SALINE",
            "currentStockUnits": 40,
            "dailyConsumptionUnits": 30,
            "daysOfSupply": 1.33,
            "threshold": 2.0,
            "timestamp": "2026-01-03T12:00:00.000Z"
        },
        {
            "eventId": "evt-test-002",
            "eventType": "InventoryLow",
            "hospitalId": "Hospital-B",
            "productCode": "SURGICAL-GLOVES-M",
            "currentStockUnits": 100,
            "dailyConsumptionUnits": 80,
            "daysOfSupply": 1.25,
            "threshold": 2.0,
            "timestamp": "2026-01-03T12:00:00.000Z"
        },
        {
            "eventId": "evt-test-003",
            "eventType": "InventoryLow",
            "hospitalId": "Hospital-A",
            "productCode": "N95-MASKS",
            "currentStockUnits": 25,
            "dailyConsumptionUnits": 50,
            "daysOfSupply": 0.5,  # URGENT case!
            "threshold": 2.0,
            "timestamp": "2026-01-03T12:00:00.000Z"
        },
        {
            "eventId": "evt-test-004",
            "eventType": "InventoryLow",
            "hospitalId": "Hospital-C",
            "productCode": "BANDAGES-LARGE",
            "currentStockUnits": 500,
            "dailyConsumptionUnits": 100,
            "daysOfSupply": 5.0,  # Above threshold - no order
            "threshold": 2.0,
            "timestamp": "2026-01-03T12:00:00.000Z"
        }
    ]

    # Process events
    order_commands = process_events(test_events)

    # Output final result
    print("\n" + "=" * 70)
    print("  FINAL OUTPUT - ORDER CREATION COMMANDS")
    print("=" * 70)

    if order_commands:
        print("\nThese commands would be sent to the Order Creation Event Hub:\n")
        print(json.dumps(order_commands, indent=2))
    else:
        print("\nNo orders to create.")

    print("\n" + "=" * 70)
    print("  TEST COMPLETE")
    print("=" * 70)

    return order_commands


if __name__ == "__main__":
    run_standalone_test()
