# minimal_test_insert.py
from supabase import create_client
import os

url = "https://ctrbrlsgdteajwncawzu.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN0cmJybHNnZHRlYWp3bmNhd3p1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Njc4NDAyOSwiZXhwIjoyMDYyMzYwMDI5fQ.3yIi76DPD0uEjobuwFS8C90YxhfcnK8lcbRMDHdsFls"
supabase = create_client(url, key)

res = supabase.table("legal_queries").insert({
    "query":    "Standalone test Q",
    "response": "Standalone test A"
}).execute()

print("=== INSERT RESULT OBJECT ===")
print(res)
print("=== TYPE ===")
print(type(res))
print("=== DIR() ===")
print(dir(res))
# Try common fields if they exist
for attr in ("data", "count", "status_code", "error", "status_text"):
    print(f"{attr}:", getattr(res, attr, "<not present>"))

