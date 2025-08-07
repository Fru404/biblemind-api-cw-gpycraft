from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from gpycraft.googleSheet.gsheetsdb import gsheetsdb as gb
from gpycraft.fireStore.firestoreupload import firestoreupload
from gpycraft.app_config import Admin
import os

app = FastAPI()

# Enable CORS
origins = [
    "https://biblemind.onrender.com",  # React dev server origin
    # add other allowed origins here or use ["*"] for all (only for dev)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # or ["*"] to allow all origins (dev only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup config
admin_instance = Admin()
os.environ['SHEET_NUMBER'] = '2'
sheet_number = os.environ.get('SHEET_NUMBER')

credentials_path = admin_instance.credentials_path
sheet_url = admin_instance.sheet_url(sheet_number=sheet_number)
storage_bucket = admin_instance.storage_bucket

# Setup instances
gsheets_instance = gb(credentials_path, sheet_url, sheet_number=sheet_number)
fire_instance = firestoreupload(storage_bucket=storage_bucket, credentials_path=credentials_path)


@app.get("/sheet-data")
async def get_sheet_data(num_rows: int = 5):
    try:
        json_data = gsheets_instance.in_json(num_rows=num_rows)
        return JSONResponse(content=json_data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
