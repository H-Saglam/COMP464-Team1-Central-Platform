"""
Real SOAP Service for Hospital Supply Chain - Central Warehouse (Team 1)
Implements StockUpdateService with Decision Engine and ESB Simulation

Run with: python3 real_soap_service.py
WSDL available at: http://localhost:8000/StockUpdateService?wsdl
"""

import logging
import random
import time
import uuid
from datetime import datetime

from flask import Flask, request as flask_request, Response
from spyne import Application, Service, rpc
from spyne.decorator import srpc
from spyne.model.complex import ComplexModel
from spyne.model.primitive import Unicode, Integer, Decimal, Boolean, DateTime
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from werkzeug.serving import run_simple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
)
logger = logging.getLogger('StockUpdateService')

# ============================================
# Complex Models (Request/Response)
# ============================================

class StockUpdateRequest(ComplexModel):
    """Input model for stock update requests from hospitals."""
    __namespace__ = 'http://hospital-supply-chain.example.com/soap/stock'

    hospitalId = Unicode(min_occurs=1, max_occurs=1, doc="Unique hospital identifier")
    productCode = Unicode(min_occurs=1, max_occurs=1, doc="Product/SKU code")
    currentStockUnits = Integer(min_occurs=1, max_occurs=1, doc="Current stock in units")
    dailyConsumptionUnits = Integer(min_occurs=1, max_occurs=1, doc="Daily consumption rate")
    daysOfSupply = Decimal(min_occurs=1, max_occurs=1, doc="Days of supply remaining")
    timestamp = Unicode(min_occurs=1, max_occurs=1, doc="ISO8601 timestamp")


class StockUpdateResult(ComplexModel):
    """Output model for stock update responses."""
    __namespace__ = 'http://hospital-supply-chain.example.com/soap/stock'

    success = Boolean(min_occurs=1, max_occurs=1, doc="Whether processing was successful")
    message = Unicode(min_occurs=1, max_occurs=1, doc="Response message")
    orderTriggered = Boolean(min_occurs=1, max_occurs=1, doc="Whether an order was auto-triggered")
    orderId = Unicode(min_occurs=0, max_occurs=1, doc="Generated order ID if triggered")


# ============================================
# Decision Engine
# ============================================

class DecisionEngine:
    """
    Central Warehouse Decision Engine
    Determines if an order should be triggered based on stock levels.
    """

    THRESHOLD_CRITICAL = 2.0  # Days - trigger order if below this
    THRESHOLD_URGENT = 1.0    # Days - mark as URGENT priority
    RESTOCK_DAYS = 7          # Target days of supply after restock

    @staticmethod
    def evaluate(days_of_supply: float, daily_consumption: int, current_stock: int) -> dict:
        """
        Evaluate stock levels and decide on order creation.

        Returns:
            dict with keys: should_order, priority, order_quantity, reason
        """
        result = {
            'should_order': False,
            'priority': None,
            'order_quantity': 0,
            'reason': ''
        }

        if days_of_supply < DecisionEngine.THRESHOLD_CRITICAL:
            result['should_order'] = True

            # Calculate order quantity: (daily * 7) - current
            target_stock = daily_consumption * DecisionEngine.RESTOCK_DAYS
            result['order_quantity'] = max(target_stock - current_stock, daily_consumption)

            # Determine priority based on urgency
            if days_of_supply < DecisionEngine.THRESHOLD_URGENT:
                result['priority'] = 'URGENT'
                result['reason'] = f'CRITICAL: Only {days_of_supply:.1f} days of supply remaining (< {DecisionEngine.THRESHOLD_URGENT} days)'
            else:
                result['priority'] = 'HIGH'
                result['reason'] = f'LOW STOCK: {days_of_supply:.1f} days of supply remaining (< {DecisionEngine.THRESHOLD_CRITICAL} days)'

            logger.warning(f"🚨 Order triggered: {result['reason']}")
        else:
            result['reason'] = f'Stock levels adequate: {days_of_supply:.1f} days of supply'
            logger.info(f"✅ {result['reason']}")

        return result


# ============================================
# ESB Simulator
# ============================================

class ESBSimulator:
    """
    Enterprise Service Bus Simulator
    Simulates network latency typical in SOA architectures.
    """

    MIN_LATENCY_SEC = 0.1
    MAX_LATENCY_SEC = 1.5

    @staticmethod
    def simulate_latency() -> float:
        """
        Simulate ESB network latency.

        Returns:
            float: The simulated latency in seconds
        """
        latency = random.uniform(ESBSimulator.MIN_LATENCY_SEC, ESBSimulator.MAX_LATENCY_SEC)
        logger.info(f"⏱️  ESB Latency Simulation: {latency*1000:.0f}ms")
        time.sleep(latency)
        return latency


# ============================================
# SOAP Service Implementation
# ============================================

class StockUpdateServiceImpl(Service):
    """
    StockUpdateService SOAP Implementation
    Handles stock update requests from hospital systems.
    """

    @rpc(StockUpdateRequest, _returns=StockUpdateResult)
    def StockUpdate(ctx, request):
        """
        Process a stock update request from a hospital.

        Business Logic:
        1. Simulate ESB latency
        2. Validate request
        3. Run Decision Engine
        4. Generate order if needed
        5. Return response
        """
        start_time = time.time()

        logger.info("=" * 60)
        logger.info("📦 STOCK UPDATE REQUEST RECEIVED")
        logger.info("=" * 60)
        logger.info(f"   Hospital ID: {request.hospitalId}")
        logger.info(f"   Product Code: {request.productCode}")
        logger.info(f"   Current Stock: {request.currentStockUnits} units")
        logger.info(f"   Daily Consumption: {request.dailyConsumptionUnits} units")
        logger.info(f"   Days of Supply: {request.daysOfSupply}")
        logger.info(f"   Timestamp: {request.timestamp}")

        # Step 1: ESB Latency Simulation
        esb_latency = ESBSimulator.simulate_latency()

        # Step 2: Run Decision Engine
        decision = DecisionEngine.evaluate(
            days_of_supply=float(request.daysOfSupply),
            daily_consumption=int(request.dailyConsumptionUnits),
            current_stock=int(request.currentStockUnits)
        )

        # Step 3: Create response
        response = StockUpdateResult()
        response.success = True

        if decision['should_order']:
            # Generate order ID
            order_id = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

            response.orderTriggered = True
            response.orderId = order_id
            response.message = (
                f"Order {order_id} created. "
                f"Priority: {decision['priority']}. "
                f"Quantity: {decision['order_quantity']} units. "
                f"Reason: {decision['reason']}"
            )

            logger.info("-" * 60)
            logger.info("📋 ORDER CREATED")
            logger.info(f"   Order ID: {order_id}")
            logger.info(f"   Priority: {decision['priority']}")
            logger.info(f"   Quantity: {decision['order_quantity']} units")
            logger.info(f"   Hospital: {request.hospitalId}")
            logger.info(f"   Product: {request.productCode}")
            logger.info("-" * 60)
        else:
            response.orderTriggered = False
            response.orderId = None
            response.message = f"Stock update processed. {decision['reason']}. No order needed."

        # Log processing time
        total_time = (time.time() - start_time) * 1000
        logger.info(f"⏱️  Total processing time: {total_time:.0f}ms (ESB: {esb_latency*1000:.0f}ms)")
        logger.info("=" * 60)

        return response


# ============================================
# Application Setup
# ============================================

# Create Spyne application
soap_app = Application(
    [StockUpdateServiceImpl],
    tns='http://hospital-supply-chain.example.com/soap/stock',
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11(),
    name='StockUpdateService'
)

# Wrap with WSGI
wsgi_app = WsgiApplication(soap_app)

# Create Flask app for additional endpoints
flask_app = Flask(__name__)


@flask_app.route('/')
def index():
    """Root endpoint with service info."""
    return {
        "service": "Hospital Supply Chain - Real SOAP Service",
        "version": "1.0.0",
        "team": "Central Warehouse (Team 1)",
        "endpoints": {
            "SOAP": "POST /StockUpdateService",
            "WSDL": "GET /StockUpdateService?wsdl"
        },
        "decision_engine": {
            "threshold_critical_days": DecisionEngine.THRESHOLD_CRITICAL,
            "threshold_urgent_days": DecisionEngine.THRESHOLD_URGENT,
            "restock_target_days": DecisionEngine.RESTOCK_DAYS
        },
        "esb_simulation": {
            "min_latency_ms": ESBSimulator.MIN_LATENCY_SEC * 1000,
            "max_latency_ms": ESBSimulator.MAX_LATENCY_SEC * 1000
        }
    }


@flask_app.route('/health')
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "StockUpdateService",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@flask_app.route('/StockUpdateService', methods=['GET', 'POST'])
def soap_endpoint():
    """Forward requests to SOAP WSGI app."""
    # Create WSGI environ from Flask request
    environ = flask_request.environ

    # Capture response
    response_body = []
    response_status = []
    response_headers = []

    def start_response(status, headers):
        response_status.append(status)
        response_headers.extend(headers)

    # Call WSGI app
    result = wsgi_app(environ, start_response)
    for data in result:
        response_body.append(data)

    # Build Flask response
    body = b''.join(response_body)
    status_code = int(response_status[0].split(' ')[0]) if response_status else 200

    resp = Response(body, status=status_code)
    for header, value in response_headers:
        resp.headers[header] = value

    return resp


# ============================================
# Main Entry Point
# ============================================

if __name__ == '__main__':
    print("=" * 70)
    print("  HOSPITAL SUPPLY CHAIN - REAL SOAP SERVICE")
    print("  Central Warehouse (Team 1)")
    print("=" * 70)
    print()
    print("  🌐 Service URL:  http://localhost:8000/StockUpdateService")
    print("  📄 WSDL URL:     http://localhost:8000/StockUpdateService?wsdl")
    print("  ❤️  Health:      http://localhost:8000/health")
    print("  ℹ️  Info:        http://localhost:8000/")
    print()
    print("  Decision Engine Configuration:")
    print(f"    - Critical threshold: < {DecisionEngine.THRESHOLD_CRITICAL} days → Order triggered")
    print(f"    - Urgent threshold:   < {DecisionEngine.THRESHOLD_URGENT} day  → URGENT priority")
    print(f"    - Restock target:     {DecisionEngine.RESTOCK_DAYS} days of supply")
    print()
    print("  ESB Simulation:")
    print(f"    - Latency range: {ESBSimulator.MIN_LATENCY_SEC*1000:.0f}ms - {ESBSimulator.MAX_LATENCY_SEC*1000:.0f}ms")
    print()
    print("=" * 70)
    print("  Press Ctrl+C to stop the server")
    print("=" * 70)
    print()

    # Run Flask app
    flask_app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
