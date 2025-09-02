import json
import os
from datetime import datetime
from fastapi import FastAPI, Query, Header, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from gpycraft.googleSheet.gsheetsdb import gsheetsdb as gb
from gpycraft.fireStore.firestoreupload import firestoreupload
from gpycraft.app_config import Admin

app = FastAPI()

origins = [
    "https://biblemind.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

admin_instance = Admin()
os.environ['SHEET_NUMBER'] = '1'
sheet_number = os.environ.get('SHEET_NUMBER')

credentials_path = admin_instance.credentials_path
sheet_url = admin_instance.sheet_url(sheet_number=sheet_number)
storage_bucket = admin_instance.storage_bucket

gsheets_instance = gb(credentials_path, sheet_url, sheet_number=sheet_number)
fire_instance = firestoreupload(storage_bucket=storage_bucket, credentials_path=credentials_path)

# === API Key dependency ===
API_KEY = os.getenv("BIBLEMIND_API_KEY")  # set in environment
API_KEY_NAME = "X-API-Key"  # header name

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")
    return x_api_key

@app.get("/sheet-data")
async def get_sheet_data(
    date: Optional[str] = Query(None, description="Date in DD-MM-YYYY format"),
    api_key: str = Depends(verify_api_key)  # enforce API key
):
    try:
        raw_data = gsheets_instance.in_json()

        if isinstance(raw_data, str):
            all_data = json.loads(raw_data)
        else:
            all_data = raw_data

        if date:
            try:
                datetime.strptime(date, "%d-%m-%Y")
                day, month, year = date.split("-")
                query_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except ValueError:
                return JSONResponse(
                    content={"error": "Invalid date format. Use DD-MM-YYYY."},
                    status_code=400
                )
        else:
            query_date = datetime.now().strftime("%Y-%m-%d")

        matched_entry = None
        for entry in all_data:
            entry_date_raw = entry.get("date")
            if not entry_date_raw:
                continue
            try:
                day, month, year = entry_date_raw.split("/")
                entry_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except Exception:
                continue

            if entry_date == query_date:
                matched_entry = entry
                break

        if matched_entry:
            return JSONResponse(content=matched_entry)
        else:
            return JSONResponse(content={
                "ot": f"No Old Testament reading available for {date if date else datetime.now().strftime('%d-%m-%Y')}.",
                "gospel": f"No Gospel reading available for {date if date else datetime.now().strftime('%d-%m-%Y')}.",
                "pope": f"No Pope reflection available for {date if date else datetime.now().strftime('%d-%m-%Y')}.",
                "date": date if date else datetime.now().strftime("%d-%m-%Y")
            })
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
