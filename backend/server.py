from fastapi import FastAPI, HTTPException, Body, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import os
import logging
import json
import uuid
import httpx
import re
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600
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
    # Drop existing collections to start fresh
    await db.base_elements.drop()
    await db.elements.drop()
    await db.combinations.drop()
    await db.user_progress.drop()
    
    logger.info("Database collections reset")
    
    # Create base elements with fixed IDs for consistency
    water_id = str(uuid.uuid4())
    fire_id = str(uuid.uuid4())
    wind_id = str(uuid.uuid4())
    earth_id = str(uuid.uuid4())
    
    base_elements = [
        {"id": water_id, "name": "Water", "emoji": "💧"},
        {"id": fire_id, "name": "Fire", "emoji": "🔥"},
        {"id": wind_id, "name": "Wind", "emoji": "💨"},
        {"id": earth_id, "name": "Earth", "emoji": "🌍"}
    ]
    
    # Store base elements in both collections
    await db.base_elements.insert_many(base_elements)
    await db.elements.insert_many(base_elements)
    logger.info(f"Created {len(base_elements)} base elements")
    
    # Create a mapping of element keys for easy lookup
    element_map = {}
    
    # Add base elements to the map first
    element_map["💧 Water"] = water_id
    element_map["🔥 Fire"] = fire_id 
    element_map["💨 Wind"] = wind_id
    element_map["🌍 Earth"] = earth_id
    
    # Load combinations from JSON
    try:
        combinations_path = Path("/app/data/combinations.json")
        if combinations_path.exists():
            with open(combinations_path, 'r') as f:
                combinations_data = json.load(f)
            
            # Process combinations for database
            processed_combinations = []
            
            for combo in combinations_data:
                # Get element keys
                element1_key = combo["element1"]
                element2_key = combo["element2"]
                result_key = combo["result"]
                
                # Parse the emoji and name
                element1_parts = element1_key.split(" ", 1)
                element2_parts = element2_key.split(" ", 1)
                result_parts = result_key.split(" ", 1)
                
                # Get or create element IDs
                if element1_key in element_map:
                    element1_id = element_map[element1_key]
                else:
                    element1_id = str(uuid.uuid4())
                    element_map[element1_key] = element1_id
                    # Create the element in the database
                    await db.elements.insert_one({
                        "id": element1_id,
                        "name": element1_parts[1],
                        "emoji": element1_parts[0]
                    })
                
                if element2_key in element_map:
                    element2_id = element_map[element2_key]
                else:
                    element2_id = str(uuid.uuid4())
                    element_map[element2_key] = element2_id
                    # Create the element in the database
                    await db.elements.insert_one({
                        "id": element2_id,
                        "name": element2_parts[1],
                        "emoji": element2_parts[0]
                    })
                
                if result_key in element_map:
                    result_id = element_map[result_key]
                else:
                    result_id = str(uuid.uuid4())
                    element_map[result_key] = result_id
                    # Create the element in the database
                    await db.elements.insert_one({
                        "id": result_id,
                        "name": result_parts[1],
                        "emoji": result_parts[0]
                    })
                
                # Create combination record
                processed_combinations.append({
                    "element1_id": element1_id,
                    "element2_id": element2_id,
                    "result_id": result_id
                })
            
            # Insert all processed combinations
            if processed_combinations:
                await db.combinations.insert_many(processed_combinations)
                logger.info(f"Loaded {len(processed_combinations)} combinations")
            
            # Log total elements created
            elements_count = await db.elements.count_documents({})
            logger.info(f"Total elements in database: {elements_count}")
            
    except Exception as e:
        logger.error(f"Error loading combinations: {str(e)}")

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

async def generate_combination_with_ai(element1, element2):
    """Generate a combination using OpenAI when no predefined combination exists"""
    try:
        # Format the input for OpenAI
        input_text = f"{element1['emoji']} {element1['name']} + {element2['emoji']} {element2['name']}"
        
        # OpenAI API call
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY', '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')}"
        }
        
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": """Word Combination Assistant Prompt
You are a specialized AI assistant that creates new word combinations and matching emojis when two existing elements are combined. Your task is to generate creative, logical, and engaging results when users combine different words.
Core Functionality
When presented with two input elements, you will:
Analyze both input elements (words and their emojis)
Determine a logical or creative combination result
Select an appropriate emoji that matches the result
Return only the result and emoji in the specified format
Input Format
You will receive input in the form: "{word1} {emoji1} + {word2} {emoji2}"
Output Format
You must respond with ONLY the resulting word and emoji in the format: "{result} {emoji}"
Do not include any explanations, greetings, or additional text
Do not reference the input elements in your response
Do not include quotation marks in your output
Combination Rules
When creating combinations:
Aim for results that follow intuitive logic when possible
Be creative but maintain plausibility in your combinations
Consider both scientific and cultural associations
Select the most appropriate and visually clear emoji for each result
Maintain consistent results for the same input combinations
Create combinations that can lead to further interesting combinations"""
                },
                {
                    "role": "user",
                    "content": input_text
                }
            ]
        }
        
        # Make the API call
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response_data = response.json()
        
        # Parse the response to extract the result
        result_text = response_data['choices'][0]['message']['content'].strip()
        
        # Simple parsing - split by the last space
        # The emoji is typically the last element in the string
        parts = result_text.split()
        if len(parts) > 1:
            result_emoji = parts[-1]
            result_name = " ".join(parts[:-1])
        else:
            # Fallback if we can't parse properly
            result_emoji = "🔮"
            result_name = result_text
        
        # Create new element
        result_element = await get_element_by_name_emoji(result_name, result_emoji)
        
        # Create and save the combination
        new_combination = {
            "element1_id": element1["id"],
            "element2_id": element2["id"],
            "result_id": result_element["id"]
        }
        
        await db.combinations.insert_one(new_combination)
        logger.info(f"Created new AI-generated combination: {element1['name']} + {element2['name']} = {result_name}")
        
        return result_element
    
    except Exception as e:
        logger.error(f"Error generating combination with AI: {str(e)}")
        logger.error(f"Response data: {response_data if 'response_data' in locals() else 'No response data'}")
        # Default to returning the first element if AI generation fails
        return element1

@app.on_event("startup")
async def startup_db_client():
    logger.info("Initializing database...")
    await init_db()
    
    # Log base elements for debugging
    base_elements = await db.base_elements.find().to_list(length=100)
    logger.info(f"Loaded {len(base_elements)} base elements")
    for elem in base_elements:
        logger.info(f"Base element: {elem['emoji']} {elem['name']} (ID: {elem['id']})")
    
    # Log combinations for debugging
    combinations = await db.combinations.find().to_list(length=200)
    logger.info(f"Loaded {len(combinations)} combinations")
    if len(combinations) > 0:
        logger.info(f"Sample combination: {combinations[0]}")
    else:
        logger.info("No combinations found in database")

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
        return json.loads(json.dumps(base_elements, cls=JSONEncoder))
    
    # Get all discovered elements
    element_ids = user_progress["discovered_elements"]
    discovered_elements = []
    
    for element_id in element_ids:
        element = await db.elements.find_one({"id": element_id})
        if element:
            discovered_elements.append(element)
    
    return json.loads(json.dumps(discovered_elements, cls=JSONEncoder))

@app.post("/api/elements/combine")
async def combine_elements(combination: CombinationRequest, user_id: str = "default"):
    """Combine two elements and return the result"""
    try:
        # Debug log
        logger.info(f"Combine request: {combination.element1_id} + {combination.element2_id}")
        
        # Get the elements (check in both base_elements and elements collections)
        element1 = await db.base_elements.find_one({"id": combination.element1_id})
        if not element1:
            element1 = await db.elements.find_one({"id": combination.element1_id})
            
        element2 = await db.base_elements.find_one({"id": combination.element2_id})
        if not element2:
            element2 = await db.elements.find_one({"id": combination.element2_id})
        
        # Debug log
        logger.info(f"Found elements: {element1 is not None}, {element2 is not None}")
        
        if not element1 or not element2:
            logger.error(f"Elements not found: {combination.element1_id}, {combination.element2_id}")
            return CombinationResult(
                success=False,
                message="One or both elements not found"
            )
        
        # Check if combination exists
        combination_result = await db.combinations.find_one({
            "$or": [
                {"element1_id": element1["id"], "element2_id": element2["id"]},
                {"element1_id": element2["id"], "element2_id": element1["id"]}
            ]
        })
        
        logger.info(f"Combination found: {combination_result is not None}")
        
        if not combination_result:
            # If no predefined combination exists, generate one with AI
            logger.info(f"No predefined combination found, generating with AI...")
            result_element = await generate_combination_with_ai(element1, element2)
            
            if not result_element:
                return CombinationResult(
                    success=False,
                    message="These elements cannot be combined"
                )
        else:
            # Get the result element if we found a predefined combination
            result_element = await db.elements.find_one({"id": combination_result["result_id"]})
        
        if not result_element:
            logger.error(f"Result element not found: {combination_result['result_id']}")
            return CombinationResult(
                success=False,
                message="Result element not found"
            )
        
        logger.info(f"Result element: {result_element['name']}")
        
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
        
        # Return the result with proper MongoDB object conversion
        result_dict = {
            "success": True,
            "result": result_element,
            "message": "New element discovered!" if is_new_discovery else "Element already discovered"
        }
        return json.loads(json.dumps(result_dict, cls=JSONEncoder))
        
    except Exception as e:
        logger.error(f"Error in combine_elements: {str(e)}")
        return CombinationResult(
            success=False,
            message=f"Error: {str(e)}"
        )

@app.post("/api/user/reset")
async def reset_user_progress(user_id: str = "default"):
    """Reset a user's discoveries back to base elements only"""
    try:
        # Get base elements
        base_elements = await db.base_elements.find().to_list(length=100)
        base_element_ids = [elem["id"] for elem in base_elements]
        
        # Update or create user progress
        await db.user_progress.update_one(
            {"user_id": user_id},
            {"$set": {"discovered_elements": base_element_ids}},
            upsert=True
        )
        
        logger.info(f"Reset user progress for {user_id} to {len(base_element_ids)} base elements")
        return {"message": "User progress reset to base elements"}
    except Exception as e:
        logger.error(f"Error resetting user progress: {str(e)}")
        return {"error": str(e)}

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
