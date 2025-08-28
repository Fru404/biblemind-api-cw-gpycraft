import json
from datetime import datetime
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from gpycraft.googleSheet.gsheetsdb import gsheetsdb as gb
from gpycraft.fireStore.firestoreupload import firestoreupload
from gpycraft.app_config import Admin
import os

app = FastAPI()

origins = [
    "*"
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


@app.get("/sheet-data")
async def get_sheet_data(date: Optional[str] = Query(None, description="Date in DD-MM-YYYY format")):
    try:
        raw_data = gsheets_instance.in_json()

        if isinstance(raw_data, str):
            all_data = json.loads(raw_data)
        else:
            all_data = raw_data

        if date:
            try:
                # Parse input date as dd-mm-yyyy
                datetime.strptime(date, "%d-%m-%Y")
                # Convert to yyyy-mm-dd for internal matching
                day, month, year = date.split("-")
                query_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except ValueError:
                return JSONResponse(content={"error": "Invalid date format. Use DD-MM-YYYY."}, status_code=400)
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
