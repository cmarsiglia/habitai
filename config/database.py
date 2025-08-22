from supabase import create_client, Client
import pandas as pd

url = "https://TU-PROJECT.supabase.co"   # reemplaza con tu Supabase URL
key = "TU-API-KEY"                       # reemplaza con tu service_role o anon key
supabase: Client = create_client(url, key)
