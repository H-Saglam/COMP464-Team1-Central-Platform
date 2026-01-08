import psycopg2
import os

# --- AZURE BİLGİLERİNİ BURAYA GİR ---
DB_HOST = "team1-postgres-db.postgres.database.azure.com" # Resimden aldım
DB_NAME = "postgres"      # Varsayılan veritabanı adı
DB_USER = "admin1"        # Resimden aldım (Administrator login)
DB_PASS = "Root1234!" # <--- BURAYI DEGISTIR!
PORT = 5432

def init_db():
    try:
        print("Azure Veritabanına bağlanılıyor...")
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=PORT,
            sslmode="require" # Azure için zorunlu
        )
        cur = conn.cursor()
        
        print("init.sql dosyası okunuyor...")
        with open("database/init.sql", "r") as f:
            sql_script = f.read()
            
        print("Tablolar oluşturuluyor...")
        cur.execute(sql_script)
        conn.commit()
        
        print("✅ BAŞARILI! Tüm tablolar Azure'a yüklendi.")
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ HATA: {e}")

if __name__ == "__main__":
    init_db()