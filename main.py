from src.gui import start_gui
from src.db import connect_to_oracle, execute_select
from dotenv import load_dotenv
import os

load_dotenv()

def main():
    print("Hello from cps510-lab9!")
    username = os.getenv("TMU_CS_USERNAME")
    password = os.getenv("TMU_CS_PASSWORD")
    dsn = os.getenv("ORACLE_DSN")
    oracle_client_lib_dir = os.getenv("ORACLE_CLIENT_LIB_DIR")
    print("Connecting to Oracle database...")
    conn = None
    try:
        conn = connect_to_oracle(username, password, dsn, oracle_client_lib_dir)
        print("Connected to Oracle database")
    except Exception as e:
        print(f"Error connecting to Oracle database: {e}")
        if conn:
            conn.close()
        exit(1)
    
    start_gui(conn)
    conn.close()

if __name__ == "__main__":
    main()