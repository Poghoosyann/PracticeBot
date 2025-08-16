import os
import asyncio

from google import genai
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI, HTTPException, Request

load_dotenv()

MONGO_DB = os.getenv("MONGO_DB")

mongo_client = AsyncIOMotorClient(MONGO_DB)
db = mongo_client.get_database("PracticeBot")

app = FastAPI()

class UserData(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None

class UserLanguageUpdate(BaseModel):
    language_code: str

class UserUpdateData(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None


async def getUser(user_id: int):
    users_collection = db.users
    user = await users_collection.find_one({"_id": user_id})
    return user


async def updateUser(telegram_id: int, update_data: Dict[str, Any]):
    users_collection = db.users
    result = await users_collection.update_one(
        {"_id": telegram_id},
        update_data
    )


@app.post("/users")
async def create_user(user: UserData):
    users_collection = db.users

    user_data_dict = user.model_dump(exclude_unset=True)
    user_data_dict["_id"] = user.telegram_id 
    
    result = await users_collection.update_one(
        {"_id": user.telegram_id}, 
        {"$set": user_data_dict},
        upsert=True
    )
    
    return {"message": "Пользователь создан или обновлен", "telegram_id": user.telegram_id}


@app.get("/users/{telegram_id}", response_model=UserData)
async def get_user_data(telegram_id: int):
    user = await getUser(telegram_id)

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    user['telegram_id'] = user['_id']
    return UserData(**user)

    
@app.patch("/users/{telegram_id}/language")
async def update_user_language(telegram_id: int, lang_update: UserLanguageUpdate):
    await updateUser(
        telegram_id,
        {"$set": {"language_code": lang_update.language_code}}
    )
    return {"message": "Попытка обновления языка пользователя завершена"}