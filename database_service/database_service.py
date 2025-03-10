from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from typing import Dict, Any
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.responses import PlainTextResponse
 
# MongoDB connection details
MONGODB_URI = "mongodb://mongo:27017"
DATABASE_NAME = "health_data"
COLLECTION_NAME = "checkin_lab_reports"
 
# Initialize the FastAPI app
app = FastAPI()
 
# Initialize the Prometheus instrumentator
instrumentator = Instrumentator()
 
# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]
 
# Data model for the request (you can extend this based on your needs)
class CheckinLabReport(BaseModel):
    userId: str
    checkin: Dict[str, Any]
    labReport: Dict[str, Any]
 
# Instrumenting the app before defining routes
instrumentator.instrument(app).expose(app, "/metrics", response_class=PlainTextResponse)
 
@app.post("/api/v1/data")
async def store_data(data: CheckinLabReport):
    # Convert the incoming data into a dictionary
    data_dict = data.dict()
 
    try:
        # Store the data in MongoDB
        result = collection.insert_one(data_dict)
        if result.inserted_id:
            return {"status": "success", "message": "Data stored successfully", "id": str(result.inserted_id)}
        else:
            raise HTTPException(status_code=500, detail="Failed to insert data into database")
 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
 
# Optionally, to see how the database service works with a GET request
@app.get("/api/v1/data/{user_id}")
async def get_data(user_id: str):
    try:
        data = collection.find_one({"userId": user_id})
        if data:
            # Return the data as a dictionary
            return data
        else:
            raise HTTPException(status_code=404, detail="Data not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")