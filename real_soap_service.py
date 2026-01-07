"""
Real SOAP Service for Hospital Supply Chain - Central Warehouse (Team 1)
Implements StockUpdateService AND OrderCreationService with Database Persistence

Run with: python3 real_soap_service.py
"""

import logging
import random
import time
import uuid
import os
import psycopg2
from datetime import datetime

from flask import Flask, request as flask_request, Response
from spyne import Application, Service, rpc
from spyne.model.complex import ComplexModel
from spyne.model.primitive import Unicode, Integer, Decimal, Boolean
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
)
logger = logging.getLogger('CentralWarehouseSOAP')

# ============================================
# Database Configuration
# ============================================

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("POSTGRES_DB", "hospital_db")
DB_USER = os.environ.get("POSTGRES_USER", "app_user")
DB_PASS = os.environ.get("POSTGRES_PASSWORD", "secure_password")
DB_PORT = os.environ.get("DB_PORT", "5432")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

# ============================================
# Models: StockUpdate
# ============================================

class StockUpdateRequest(ComplexModel):
    __namespace__ = 'http://hospital-supply-chain.example.com/soap/stock'
    hospitalId = Unicode(min_occurs=1, max_occurs=1)
    productCode = Unicode(min_occurs=1, max_occurs=1)
    currentStockUnits = Integer(min_occurs=1, max_occurs=1)
    dailyConsumptionUnits = Integer(min_occurs=1, max_occurs=1)
    daysOfSupply = Decimal(min_occurs=1, max_occurs=1)
    timestamp = Unicode(min_occurs=1, max_occurs=1)

class StockUpdateResult(ComplexModel):
    __namespace__ = 'http://hospital-supply-chain.example.com/soap/stock'
    success = Boolean(min_occurs=1, max_occurs=1)
    message = Unicode(min_occurs=1, max_occurs=1)
    orderTriggered = Boolean(min_occurs=1, max_occurs=1)
    orderId = Unicode(min_occurs=0, max_occurs=1)

# ============================================
# Models: OrderCreation (YENİ EKLENDİ)
# ============================================

class OrderCreationRequest(ComplexModel):
    __namespace__ = 'http://hospital-supply-chain.example.com/soap/order'
    orderId = Unicode(min_occurs=0, max_occurs=1) # Optional, if not provided generated
    hospitalId = Unicode(min_occurs=1, max_occurs=1)
    productCode = Unicode(min_occurs=1, max_occurs=1)
    orderQuantity = Integer(min_occurs=1, max_occurs=1)
    priority = Unicode(min_occurs=1, max_occurs=1) # URGENT, HIGH, NORMAL
    estimatedDeliveryDate = Unicode(min_occurs=0, max_occurs=1)
    timestamp = Unicode(min_occurs=1, max_occurs=1)

class OrderCreationResult(ComplexModel):
    __namespace__ = 'http://hospital-supply-chain.example.com/soap/order'
    success = Boolean(min_occurs=1, max_occurs=1)
    message = Unicode(min_occurs=1, max_occurs=1)
    orderId = Unicode(min_occurs=1, max_occurs=1)

# ============================================
# Helpers
# ============================================

class DecisionEngine:
    THRESHOLD_CRITICAL = 2.0
    THRESHOLD_URGENT = 1.0
    RESTOCK_DAYS = 7

    @staticmethod
    def evaluate(days_of_supply: float, daily_consumption: int, current_stock: int) -> dict:
        result = {'should_order': False, 'priority': None, 'order_quantity': 0, 'reason': ''}
        
        if days_of_supply < DecisionEngine.THRESHOLD_CRITICAL:
            result['should_order'] = True
            target_stock = daily_consumption * DecisionEngine.RESTOCK_DAYS
            calc_quantity = target_stock - current_stock
            result['order_quantity'] = max(int(calc_quantity), daily_consumption)

            if days_of_supply < DecisionEngine.THRESHOLD_URGENT:
                result['priority'] = 'URGENT'
                result['reason'] = f'CRITICAL: {days_of_supply:.1f} days (< {DecisionEngine.THRESHOLD_URGENT})'
            else:
                result['priority'] = 'HIGH'
                result['reason'] = f'LOW STOCK: {days_of_supply:.1f} days (< {DecisionEngine.THRESHOLD_CRITICAL})'
        else:
            result['reason'] = f'Adequate stock: {days_of_supply:.1f} days'

        return result

# ============================================
# Service 1: StockUpdateService
# ============================================

class StockUpdateServiceImpl(Service):
    @rpc(StockUpdateRequest, _returns=StockUpdateResult)
    def StockUpdate(ctx, request):
        # ... (Önceki kodun aynısı) ...
        start_time = time.time()
        logger.info(f"[StockUpdate] Received update from {request.hospitalId}")
        
        # Simüle edilmiş gecikme
        time.sleep(random.uniform(0.1, 0.5))

        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            event_id = f"evt-{uuid.uuid4()}"

            # Event Kaydet
            cur.execute("""
                INSERT INTO StockEvents (event_id, hospital_id, product_code, current_stock_units, daily_consumption_units, days_of_supply, event_source, received_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, 'SOA', NOW())
            """, (event_id, request.hospitalId, request.productCode, request.currentStockUnits, request.dailyConsumptionUnits, request.daysOfSupply))

            # Karar Ver
            decision = DecisionEngine.evaluate(float(request.daysOfSupply), int(request.dailyConsumptionUnits), int(request.currentStockUnits))
            response = StockUpdateResult()
            response.success = True
            
            if decision['should_order']:
                order_id = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
                cur.execute("""
                    INSERT INTO Orders (order_id, hospital_id, product_code, order_quantity, priority, order_source, order_status)
                    VALUES (%s, %s, %s, %s, %s, 'SOA', 'PENDING')
                """, (order_id, request.hospitalId, request.productCode, decision['order_quantity'], decision['priority']))
                
                cur.execute("INSERT INTO DecisionLogs (decision_id, event_id, order_id, decision_type, decision_reason, days_of_supply_at_decision, threshold_used) VALUES (%s, %s, %s, 'ORDER_CREATED', %s, %s, %s)",
                           (f"dec-{uuid.uuid4()}", event_id, order_id, decision['reason'], request.daysOfSupply, DecisionEngine.THRESHOLD_CRITICAL))
                
                response.orderTriggered = True
                response.orderId = order_id
                response.message = f"Order created: {order_id}"
            else:
                cur.execute("INSERT INTO DecisionLogs (decision_id, event_id, decision_type, decision_reason, days_of_supply_at_decision, threshold_used) VALUES (%s, %s, 'ORDER_SKIPPED', %s, %s, %s)",
                           (f"dec-{uuid.uuid4()}", event_id, decision['reason'], request.daysOfSupply, DecisionEngine.THRESHOLD_CRITICAL))
                response.orderTriggered = False
                response.message = "Stock adequate"

            # ESB Log
            cur.execute("INSERT INTO ESBLogs (log_id, message_id, source_hospital_id, target_service, latency_ms, status) VALUES (%s, %s, %s, 'StockUpdateService', %s, 'SUCCESS')",
                       (f"log-{uuid.uuid4()}", event_id, request.hospitalId, int((time.time() - start_time) * 1000)))

            conn.commit()
            return response

        except Exception as e:
            if conn: conn.rollback()
            logger.error(f"[StockUpdate] Error: {e}")
            return StockUpdateResult(success=False, message="Internal Server Error")
        finally:
            if conn: conn.close()

# ============================================
# Service 2: OrderCreationService (YENİ)
# ============================================

class OrderCreationServiceImpl(Service):
    @rpc(OrderCreationRequest, _returns=OrderCreationResult)
    def CreateOrder(ctx, request):
        start_time = time.time()
        logger.info(f"[OrderCreation] Received order command for {request.hospitalId}")
        
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # ID yoksa oluştur
            order_id = request.orderId if request.orderId else f"ORD-MANUAL-{uuid.uuid4().hex[:8].upper()}"
            
            # Veritabanına kaydet
            cur.execute("""
                INSERT INTO Orders 
                (order_id, hospital_id, product_code, order_quantity, priority, order_source, order_status, notes)
                VALUES (%s, %s, %s, %s, %s, 'SOA', 'PENDING', 'Created via OrderCreationService')
            """, (
                order_id,
                request.hospitalId,
                request.productCode,
                request.orderQuantity,
                request.priority
            ))
            
            # TODO: Gerçek senaryoda burada Hastane'nin servisine (ReceiveOrder) istek atılır.
            # Şimdilik sadece veritabanına kaydediyoruz (Requirements A.2.4)
            
            # ESB Log
            cur.execute("INSERT INTO ESBLogs (log_id, message_id, source_hospital_id, target_service, latency_ms, status) VALUES (%s, %s, %s, 'OrderCreationService', %s, 'SUCCESS')",
                       (f"log-{uuid.uuid4()}", order_id, request.hospitalId, int((time.time() - start_time) * 1000)))

            conn.commit()
            
            logger.info(f"[OrderCreation] Order {order_id} created successfully")
            return OrderCreationResult(success=True, message="Order processed", orderId=order_id)

        except Exception as e:
            if conn: conn.rollback()
            logger.error(f"[OrderCreation] Error: {e}")
            return OrderCreationResult(success=False, message=f"Error: {str(e)}", orderId="")
        finally:
            if conn: conn.close()

# ============================================
# Application Setup
# ============================================

# İki servisi tek bir Spyne uygulamasında birleştiriyoruz
soap_app = Application(
    [StockUpdateServiceImpl, OrderCreationServiceImpl],
    tns='http://hospital-supply-chain.example.com/soap',
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11(),
    name='CentralServices'
)

wsgi_app = WsgiApplication(soap_app)
flask_app = Flask(__name__)

@flask_app.route('/health')
def health():
    return {"status": "healthy", "services": ["StockUpdateService", "OrderCreationService"]}

@flask_app.route('/CentralServices', methods=['GET', 'POST'])
def soap_endpoint():
    environ = flask_request.environ
    response_body = []
    response_status = []
    response_headers = []
    def start_response(status, headers):
        response_status.append(status)
        response_headers.extend(headers)
    result = wsgi_app(environ, start_response)
    for data in result: response_body.append(data)
    status_code = int(response_status[0].split(' ')[0]) if response_status else 200
    resp = Response(b''.join(response_body), status=status_code)
    for header, value in response_headers: resp.headers[header] = value
    return resp

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    flask_app.run(host='0.0.0.0', port=port)