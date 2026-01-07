import logging
import json
import azure.functions as func
from .stock_function_logic import process_events

def main(events: func.EventHubEvent, outputEvents: func.Out[str]):
    event_list = []
    
    # 1. Gelen verileri oku
    for event in events:
        try:
            event_body = event.get_body().decode('utf-8')
            logging.info(f"İşleniyor: {event_body}")
            event_data = json.loads(event_body)
            event_list.append(event_data)
        except Exception as e:
            logging.error(f"Veri okuma hatası: {e}")

    # 2. Sizin mantığınızı çalıştır
    if event_list:
        order_commands = process_events(event_list)

        # 3. Sipariş varsa Event Hub'a gönder
        if order_commands:
            logging.info(f"{len(order_commands)} adet sipariş oluşturuldu.")
            # JSON listesini string'e çevirip gönderiyoruz
            outputEvents.set(json.dumps(order_commands))