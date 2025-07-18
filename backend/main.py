from fastapi import FastAPI, Depends, HTTPException, Path, Request, status
from prisma import Prisma
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from jose import jwt, JWTError
import httpx
from uuid import uuid4
from datetime import datetime


load_dotenv()

app = FastAPI()
db = Prisma()

origins=["http://localhost:3000"]
CLERK_JWT_PUBLIC_KEY = os.getenv("CLERK_JWT_PUBLIC_KEY")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#auth middleware

async def verify_clerk_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing Authorization header")

    session_token = auth_header.split("Bearer ")[1]
    headers = {"Authorization": f"Bearer {CLERK_JWT_PUBLIC_KEY}"}

    async with httpx.AsyncClient() as client:
        # Validate session
        session_resp = await client.get(f"https://api.clerk.dev/v1/sessions/{session_token}", headers=headers)
        if session_resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session token")

        session_data = session_resp.json()
        user_id = session_data["user_id"]

        # Get full user info
        user_resp = await client.get(f"https://api.clerk.dev/v1/users/{user_id}", headers=headers)
        if user_resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Failed to fetch user info")

        return user_resp.json()
    


@app.on_event("startup")
async def connect_db():
    await db.connect()

@app.on_event("shutdown")
async def disconnect_db():
    await db.disconnect()



#Auth routes
@app.post("/user/signup")
async def create_user(user_data: dict = Depends(verify_clerk_user)):
    user_id = user_data["id"]
    email = user_data["email_addresses"][0]["email_address"]
    name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()

    existing = await db.user.find_unique(where={"clerkUserId": user_id})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists. Please login.")

    await db.user.create(
        data={
            "clerkUserId": user_id,
            "name": name,
            "email": email,
            "role": "customer"
        }
    )
    return {"message": "User signed up successfully."}


@app.post("/admin/signup")
async def create_admin(admin_data: dict = Depends(verify_clerk_user)):
    admin_id = admin_data["id"]
    email = admin_data["email_addresses"][0]["email_address"]
    name = f"{admin_data.get('first_name', '')} {admin_data.get('last_name', '')}".strip()

    existing = await db.user.find_unique(where={"clerkUserId": admin_id})
    if existing:
        raise HTTPException(status_code=400, detail="Admin already exists. Please login.")

    await db.user.create(
        data={
            "clerkUserId": admin_id,
            "name": name,
            "email": email,
            "role": "admin"
        }
    )
    return {"message": "Admin signed up successfully."}


@app.post("/user/login")
async def user_login(user_data: dict = Depends(verify_clerk_user)):
    user_id = user_data["id"]
    user = await db.user.find_unique(where={"clerkUserId": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please sign up.")
    return {"message": "User logged in successfully."}


@app.post("/admin/login")
async def admin_login(admin_data: dict = Depends(verify_clerk_user)):
    admin_id = admin_data["id"]
    admin = await db.user.find_unique(where={"clerkUserId": admin_id})
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found. Please sign in.")
    return {"message": "Admin logged in successfully."}



@app.get("/admin/users/{user_id}")
async def get_user(user_id: int = Path(...)):
    user=await db.user.find_unique(where={"id":user_id})
    if not user :
        raise HTTPException(status_code=404,detail="User not found . Please sing in.")
    return {"User":user}



@app.post("/admin/{user_id}/businesses")
async def create_business(request: Request, user_id: int = Path(...)):
    data = await request.json()
    business_name = data.get("name")
    owner_id = user_id
    created_id = str(uuid4())

    await db.business.create(
        data={
            "id": created_id,
            "name": business_name,
            "ownerId": owner_id,
        }
    )
    return {"message": "Created business successfully"}


@app.get("/admin/business/{business_id}")
async def get_business(business_id: str = Path(...)):
    business=await db.business.find_unique(where={"id":business_id})
    if not business:
        raise HTTPException(status_code=404,detail="Business not found . Go to create Business")
    return {"business":business}



@app.post("/admin/{business_id}/queues")
async def create_queues(request : Request , business_id: str=Path(...)):
    queue_id=str(uuid4())
    title=request.get("Title")
    now = datetime.now(datetime.timezone.utc)
    await db.queue.create(
        data={
            "id":queue_id,
            "title":title,
            "businessId":business_id,
            "createdAt":now,
        }
    )
    return {"message":"Created queue succesfully for the business {business_id}"}



@app.post("/user/queues/{queue_id}/join/{user_id}")
async def join_queue(queue_id: str = Path(...), user_id: int = Path(...)):
    existing=await db.queueentry.find_first(where={"queueId":queue_id,"userId":user_id})
    if existing:
        raise HTTPException(status_code=404,detail="User already joined this queue.")
    count=db.queueentry.count(where={"queueId":queue_id})
    position=count+1
    await db.queueentry.create(
        data={
            "queueId":queue_id,
            "userId":user_id,
            "position":position,
            "status":"waiting",
        }
    )
    return {"message": f"User {user_id} joined queue {queue_id}"}






@app.get("/user/queues/{queue_id}/position/{user_id}")
async def get_position(queue_id: str = Path(...), user_id: int = Path(...)):
    existing = await db.queueentry.find_first(where={"queueId":queue_id,"userId":user_id})
    if not existing:
        raise HTTPException(status_code=404,detail="User has not joined this queue. Please join .")
    return {"message": f"User {user_id}'s position in queue {queue_id} is {existing.position}"}




@app.get("/admin/business/{business_id}/queues")
def get_all_business_queues(business_id: int = Path(...)):
    queues=db.queue.find_many(where={"businessId":business_id },order={ "createdAt":"asc"})
    return {"message": f"The business {business_id} has created {queues} queues"}



@app.get("/admin/users/{user_id}/queues")
def get_all_users_queues(user_id: int = Path(...)):
    queues=db.queue.find_many(where={"userId":user_id},order={"createdAt":"asc"})
    return {"message": f"The user {user_id} has joined {queues} queues"}





@app.patch("/admin/queues/{queue_id}/status/{user_id}")
def change_status_user(queue_id: int = Path(...), user_id: int = Path(...)):
    return {"message": f"Changed status of user {user_id} in queue {queue_id}"}

@app.get("/admin/queues/{queue_id}/status/{user_id}")
def check_status_user(queue_id: int = Path(...), user_id: int = Path(...)):
    return {"message": f"Status of user {user_id} in queue {queue_id}"}





@app.get("/admin/analytics/{business_id}")
def get_all_queues_analytics_under_a_business(business_id: int = Path(...)):
    return {"message": f"These are the analytics of all queues created by business {business_id}"}






@app.get("/admin/queues/{queue_id}")
def get_queue(queue_id: int = Path(...)):
    return {"message": f"Queue details of {queue_id}"}






@app.post("/user/queues/{queue_id}/notify/{user_id}")
def notify_user(queue_id: int = Path(...), user_id: int = Path(...)):
    return {"message": f"Notified user {user_id} in queue {queue_id}"}


