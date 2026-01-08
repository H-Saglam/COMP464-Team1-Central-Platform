import logging
import json
import os
import datetime
import azure.functions as func
import pg8000.native
import ssl
import uuid
from typing import List

def main(events: List[func.EventHubEvent], outputEvent: func.Out[func.EventHubEvent]):
    logging.info('>>> SERVERLESS PROCESSOR (FULL MODE) BAŞLADI <<<')
    
    # DB Bağlantısı Hazırlığı
    db_host = os.environ.get("DB_HOST")
    db_password = os.environ.get("DB_PASSWORD")
    conn = None
    
    try:
        ssl_context = ssl.create_default_context()
        conn = pg8000.native.Connection(
            user=os.environ.get("DB_USER"),
            password=db_password,
            host=db_host,
            database=os.environ.get("DB_NAME"),
            ssl_context=ssl_context
        )
    except Exception as e:
        logging.error(f"DB Bağlantı Hatası: {str(e)}")

    # Olayları İşle
    for event in events:
        try:
            body = event.get_body().decode('utf-8')
            data = json.loads(body)
            days = float(data.get('daysOfSupply', 99))
            
            if days < 2.0:
                # 1. Sipariş ID Oluştur
                unique_suffix = str(uuid.uuid4())[:8]
                order_id = f"ORD-SRV-{unique_suffix}"
                
                logging.info(f"🚨 KRİTİK STOK! Sipariş ID: {order_id}")

                # 2. Veritabanına Yaz
                if conn:
                    conn.run(
                        """INSERT INTO orders (
                            order_id, hospital_id, product_code, order_quantity, 
                            priority, order_status, order_source, created_at
                        ) VALUES (:oid, :hid, :prod, :qty, :prio, 'PENDING', 'Serverless', :time)""",
                        oid=order_id,
                        hid=data.get("hospitalId"),
                        prod=data.get("productCode"),
                        qty=50,
                        prio="URGENT",
                        time=datetime.datetime.now()
                    )
                    logging.info("💾 DB Kaydı Başarılı.")

                # 3. Event Hub'a (Sonraki Aşamaya) Mesaj Gönder
                # Sipariş komutunu hazırla
                command_message = {
                    "commandId": str(uuid.uuid4()),
                    "commandType": "ProcessOrder",
                    "orderId": order_id,
                    "details": data
                }
                # Çıktı kanalına yaz
                outputEvent.set(
                    func.EventHubEvent(json.dumps(command_message).encode('utf-8'))
                )
                logging.info("📤 Event Hub'a (order-commands) iletildi.")

        except Exception as e:
            logging.error(f"Hata: {str(e)}")

    if conn:
        conn.close()