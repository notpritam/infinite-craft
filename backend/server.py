from fastapi import FastAPI, HTTPException, Body, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import os
import logging
import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from bson import ObjectId

# /backend 
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Custom JSON encoder for MongoDB ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'infinite_craft')]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models
class Element(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    emoji: str

class CombinationRequest(BaseModel):
    element1_id: str
    element2_id: str

class CombinationResult(BaseModel):
    success: bool
    result: Optional[Element] = None
    message: str = ""

class UserProgress(BaseModel):
    user_id: str
    discovered_elements: List[str]  # List of element IDs

# Initialize database with base elements and combinations
async def init_db():
    # Check if base elements collection exists
    base_elements_count = await db.base_elements.count_documents({})
    
    if base_elements_count == 0:
        # Create base elements
        base_elements = [
            {"id": str(uuid.uuid4()), "name": "Water", "emoji": "💧"},
            {"id": str(uuid.uuid4()), "name": "Fire", "emoji": "🔥"},
            {"id": str(uuid.uuid4()), "name": "Wind", "emoji": "💨"},
            {"id": str(uuid.uuid4()), "name": "Earth", "emoji": "🌍"}
        ]
        await db.base_elements.insert_many(base_elements)
        logger.info("Base elements created")
    
    # Check if combinations collection exists
    combinations_count = await db.combinations.count_documents({})
    
    if combinations_count == 0:
        # Load combinations from JSON
        try:
            combinations_path = Path("/app/data/combinations.json")
            if combinations_path.exists():
                with open(combinations_path, 'r') as f:
                    combinations_data = json.load(f)
                
                # Process combinations for database
                processed_combinations = []
                for combo in combinations_data:
                    # Parse the emoji and name from the string
                    element1_parts = combo["element1"].split(" ", 1)
                    element2_parts = combo["element2"].split(" ", 1)
                    result_parts = combo["result"].split(" ", 1)
                    
                    # Get or create elements
                    element1 = await get_element_by_name_emoji(element1_parts[1], element1_parts[0])
                    element2 = await get_element_by_name_emoji(element2_parts[1], element2_parts[0])
                    result = await get_element_by_name_emoji(result_parts[1], result_parts[0])
                    
                    # Create combination
                    processed_combinations.append({
                        "element1_id": element1["id"],
                        "element2_id": element2["id"],
                        "result_id": result["id"]
                    })
                
                if processed_combinations:
                    await db.combinations.insert_many(processed_combinations)
                    logger.info(f"Loaded {len(processed_combinations)} combinations")
        except Exception as e:
            logger.error(f"Error loading combinations: {e}")

async def get_element_by_name_emoji(name, emoji):
    # Try to find existing element
    element = await db.elements.find_one({"name": name, "emoji": emoji})
    
    if not element:
        # Create new element
        element = {
            "id": str(uuid.uuid4()),
            "name": name,
            "emoji": emoji
        }
        await db.elements.insert_one(element)
    
    return element

@app.on_event("startup")
async def startup_db_client():
    await init_db()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

@app.get("/api")
async def root():
    return {"message": "Infinite Craft API"}

@app.get("/api/elements/base")
async def get_base_elements():
    """Return all base elements"""
    base_elements = await db.base_elements.find().to_list(length=100)
    # Convert ObjectId to string if needed
    return json.loads(json.dumps(base_elements, cls=JSONEncoder))

@app.get("/api/elements/all")
async def get_all_elements():
    """Return all elements (for admin/testing)"""
    elements = await db.elements.find().to_list(length=1000)
    # Convert ObjectId to string if needed
    return json.loads(json.dumps(elements, cls=JSONEncoder))

@app.get("/api/elements/discovered")
async def get_discovered_elements(user_id: str = "default"):
    """Return all discovered elements for a user"""
    user_progress = await db.user_progress.find_one({"user_id": user_id})
    
    if not user_progress:
        # User has no progress, create with base elements
        base_elements = await db.base_elements.find().to_list(length=100)
        base_element_ids = [elem["id"] for elem in base_elements]
        
        user_progress = {
            "user_id": user_id,
            "discovered_elements": base_element_ids
        }
        await db.user_progress.insert_one(user_progress)
        
        # Return base elements as discovered
        return base_elements
    
    # Get all discovered elements
    element_ids = user_progress["discovered_elements"]
    discovered_elements = []
    
    for element_id in element_ids:
        element = await db.elements.find_one({"id": element_id})
        if element:
            discovered_elements.append(element)
    
    return discovered_elements

@app.post("/api/elements/combine")
async def combine_elements(combination: CombinationRequest, user_id: str = "default"):
    """Combine two elements and return the result"""
    # Get the elements
    element1 = await db.elements.find_one({"id": combination.element1_id})
    element2 = await db.elements.find_one({"id": combination.element2_id})
    
    if not element1 or not element2:
        raise HTTPException(status_code=404, detail="One or both elements not found")
    
    # Check if combination exists
    combination_result = await db.combinations.find_one({
        "$or": [
            {"element1_id": element1["id"], "element2_id": element2["id"]},
            {"element1_id": element2["id"], "element2_id": element1["id"]}
        ]
    })
    
    if not combination_result:
        return CombinationResult(
            success=False,
            message="These elements cannot be combined"
        )
    
    # Get the result element
    result_element = await db.elements.find_one({"id": combination_result["result_id"]})
    
    if not result_element:
        raise HTTPException(status_code=500, detail="Result element not found")
    
    # Add to user's discovered elements if not already discovered
    user_progress = await db.user_progress.find_one({"user_id": user_id})
    
    if not user_progress:
        # Create user progress with base elements + new discovery
        base_elements = await db.base_elements.find().to_list(length=100)
        base_element_ids = [elem["id"] for elem in base_elements]
        
        user_progress = {
            "user_id": user_id,
            "discovered_elements": base_element_ids
        }
        await db.user_progress.insert_one(user_progress)
    
    # Check if element is already discovered
    is_new_discovery = result_element["id"] not in user_progress["discovered_elements"]
    
    # Add to discovered elements if new
    if is_new_discovery:
        await db.user_progress.update_one(
            {"user_id": user_id},
            {"$addToSet": {"discovered_elements": result_element["id"]}}
        )
    
    return CombinationResult(
        success=True,
        result=Element(**result_element),
        message="New element discovered!" if is_new_discovery else "Element already discovered"
    )

@app.post("/api/user/reset")
async def reset_user_progress(user_id: str = "default"):
    """Reset a user's discoveries back to base elements only"""
    # Get base elements
    base_elements = await db.base_elements.find().to_list(length=100)
    base_element_ids = [elem["id"] for elem in base_elements]
    
    # Update or create user progress
    await db.user_progress.update_one(
        {"user_id": user_id},
        {"$set": {"discovered_elements": base_element_ids}},
        upsert=True
    )
    
    return {"message": "User progress reset to base elements"}

@app.get("/api/user/progress")
async def get_user_progress(user_id: str = "default"):
    """Get a specific user's progress"""
    user_progress = await db.user_progress.find_one({"user_id": user_id})
    
    if not user_progress:
        # User has no progress, create with base elements
        base_elements = await db.base_elements.find().to_list(length=100)
        base_element_ids = [elem["id"] for elem in base_elements]
        
        user_progress = {
            "user_id": user_id,
            "discovered_elements": base_element_ids
        }
        await db.user_progress.insert_one(user_progress)
    
    # Count discoveries
    discovery_count = len(user_progress["discovered_elements"])
    
    return {
        "user_id": user_progress["user_id"],
        "discovery_count": discovery_count,
        "discovered_elements": user_progress["discovered_elements"]
    }

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8001)
