import asyncio
import json
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData, TransportType

# DİKKAT: Takım 1'den aldığınız anahtarı buraya yapıştırın
CONNECTION_STR = "Endpoint=sb://medical-supply-chain-ns.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=HFDW05QKieWgy3uDKmNHc2OisPdrfNvoy+AEhKCJZlw=;TransportType=AmqpWebSockets"
EVENT_HUB_NAME = "inventory-low-events"

async def run():
    # DÜZELTME: Sizin sürümünüze uygun olan ismi kullandık (AmqpOverWebsocket)
    producer = EventHubProducerClient.from_connection_string(
        conn_str=CONNECTION_STR, 
        eventhub_name=EVENT_HUB_NAME,
        transport_type=TransportType.AmqpOverWebsocket
    )
    
    async with producer:
        event_batch = await producer.create_batch()
        
        # Test Verisi
        test_data = {
    "hospitalId": "TEST-SERVERLESS-DB", # Farklı bir isim verelim ki tabloda hemen tanı
    "productCode": "TEST-URUN-999",
    "currentStockUnits": 5,             # Stok çok az
    "dailyConsumptionUnits": 10,        # Tüketim çok fazla
    "daysOfSupply": 0.5,                # Kritik seviye (1.0'ın altında)
    "threshold": 2.0,
    "timestamp": "2026-01-07T22:45:00"
}
        
        print(f"Gönderiliyor: {test_data}")
        event_batch.add(EventData(json.dumps(test_data)))
        
        await producer.send_batch(event_batch)
        print("✅ Veri Azure Event Hub'a başarıyla gönderildi!")

if __name__ == '__main__':
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass