
import sys
import os
sys.path.append(os.getcwd())

print("Attempting to import app.workers.ingestion...")
try:
    import app.workers.ingestion
    print("Import SUCCESS")
except Exception as e:
    print(f"Import FAILED: {e}")
    import traceback
    traceback.print_exc()
