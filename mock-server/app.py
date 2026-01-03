"""
Mock SOAP Server for Hospital Supply Chain
Flask-based mock server for StockUpdateService

This server is for testing purposes for other teams.
Run with: python app.py
"""

from flask import Flask, request, Response
import xml.etree.ElementTree as ET
from datetime import datetime
import uuid
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# XML Namespaces
SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
TNS = "http://hospital-supply-chain.example.com/soap/stock"


def create_soap_response(success: bool, message: str, order_triggered: bool = False, order_id: str = None) -> str:
    """Create a SOAP response envelope."""
    order_id_element = f"<tns:orderId>{order_id}</tns:orderId>" if order_id else "<tns:orderId/>"

    response = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{SOAP_NS}" xmlns:tns="{TNS}">
    <soap:Body>
        <tns:StockUpdateResponse>
            <tns:success>{str(success).lower()}</tns:success>
            <tns:message>{message}</tns:message>
            <tns:orderTriggered>{str(order_triggered).lower()}</tns:orderTriggered>
            {order_id_element}
        </tns:StockUpdateResponse>
    </soap:Body>
</soap:Envelope>"""
    return response


def create_soap_fault(error_code: str, error_message: str, hospital_id: str = None, product_code: str = None) -> str:
    """Create a SOAP fault response."""
    timestamp = datetime.utcnow().isoformat() + "Z"

    fault = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{SOAP_NS}" xmlns:tns="{TNS}">
    <soap:Body>
        <soap:Fault>
            <faultcode>soap:Server</faultcode>
            <faultstring>{error_message}</faultstring>
            <detail>
                <tns:StockUpdateFault>
                    <tns:errorCode>{error_code}</tns:errorCode>
                    <tns:errorMessage>{error_message}</tns:errorMessage>
                    <tns:hospitalId>{hospital_id or 'N/A'}</tns:hospitalId>
                    <tns:productCode>{product_code or 'N/A'}</tns:productCode>
                    <tns:timestamp>{timestamp}</tns:timestamp>
                </tns:StockUpdateFault>
            </detail>
        </soap:Fault>
    </soap:Body>
</soap:Envelope>"""
    return fault


def parse_stock_update_request(xml_data: str) -> dict:
    """Parse the incoming SOAP request and extract StockUpdateRequest fields."""
    try:
        root = ET.fromstring(xml_data)

        # Define namespaces for parsing
        namespaces = {
            'soap': SOAP_NS,
            'tns': TNS
        }

        # Find the StockUpdateRequest element
        body = root.find('.//soap:Body', namespaces)
        if body is None:
            # Try without namespace prefix
            body = root.find('.//{%s}Body' % SOAP_NS)

        if body is None:
            return None

        # Try to find StockUpdateRequest with various namespace patterns
        request_elem = None
        for child in body:
            if 'StockUpdateRequest' in child.tag:
                request_elem = child
                break

        if request_elem is None:
            return None

        # Extract fields (handle both namespaced and non-namespaced)
        def get_text(parent, tag_name):
            for child in parent:
                if tag_name in child.tag:
                    return child.text
            return None

        return {
            'hospitalId': get_text(request_elem, 'hospitalId'),
            'productCode': get_text(request_elem, 'productCode'),
            'currentStockUnits': get_text(request_elem, 'currentStockUnits'),
            'dailyConsumptionUnits': get_text(request_elem, 'dailyConsumptionUnits'),
            'daysOfSupply': get_text(request_elem, 'daysOfSupply'),
            'timestamp': get_text(request_elem, 'timestamp')
        }

    except ET.ParseError as e:
        logger.error(f"XML Parse Error: {e}")
        return None


@app.route('/StockUpdateService', methods=['POST'])
def stock_update_service():
    """
    Mock SOAP endpoint for StockUpdateService.
    Accepts XML POST requests and returns hardcoded success response.
    """
    content_type = request.headers.get('Content-Type', '')

    # Validate content type
    if 'xml' not in content_type.lower() and 'text' not in content_type.lower():
        logger.warning(f"Invalid content type received: {content_type}")
        # Still try to process it

    xml_data = request.data.decode('utf-8')
    logger.info(f"Received request:\n{xml_data[:500]}...")  # Log first 500 chars

    # Parse the request
    parsed_request = parse_stock_update_request(xml_data)

    if parsed_request is None:
        logger.error("Failed to parse SOAP request")
        fault_response = create_soap_fault(
            error_code="PARSE_ERROR",
            error_message="Could not parse SOAP request"
        )
        return Response(fault_response, status=400, mimetype='text/xml')

    logger.info(f"Parsed request: {parsed_request}")

    # Check if we should trigger an order (mock logic: if daysOfSupply < 7)
    order_triggered = False
    order_id = None

    try:
        days_of_supply = float(parsed_request.get('daysOfSupply', 999))
        if days_of_supply < 7:
            order_triggered = True
            order_id = f"ORD-MOCK-{uuid.uuid4().hex[:8].upper()}"
            logger.info(f"Mock order triggered: {order_id}")
    except (ValueError, TypeError):
        pass

    # Create success response
    response_xml = create_soap_response(
        success=True,
        message="Mock received - Stock update processed successfully",
        order_triggered=order_triggered,
        order_id=order_id
    )

    logger.info(f"Sending response:\n{response_xml}")

    return Response(response_xml, status=200, mimetype='text/xml')


@app.route('/StockUpdateService', methods=['GET'])
def stock_update_service_wsdl():
    """Return WSDL for the service (simplified)."""
    wsdl_location = "See contracts/wsdl/StockUpdateService.wsdl for full WSDL"
    return Response(
        f"<!-- {wsdl_location} -->\n<message>Use POST method with SOAP XML body</message>",
        status=200,
        mimetype='text/xml'
    )


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "StockUpdateService-Mock",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with service info."""
    return {
        "service": "Hospital Supply Chain - Mock SOAP Server",
        "version": "1.0.0",
        "endpoints": {
            "StockUpdateService": "/StockUpdateService (POST - SOAP XML)",
            "health": "/health (GET)",
            "wsdl": "/StockUpdateService (GET)"
        },
        "documentation": "This is a mock server for testing purposes."
    }


if __name__ == '__main__':
    print("=" * 60)
    print("Hospital Supply Chain - Mock SOAP Server")
    print("=" * 60)
    print("Endpoints:")
    print("  POST /StockUpdateService - SOAP endpoint")
    print("  GET  /StockUpdateService - WSDL info")
    print("  GET  /health             - Health check")
    print("  GET  /                   - Service info")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
