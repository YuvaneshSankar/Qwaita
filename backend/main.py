from fastapi import FastAPI, Depends, HTTPException, Path, Request, status
from prisma import Prisma
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from jose import jwt, JWTError
import httpx
from uuid import uuid4
from datetime import datetime, timezone
import smtplib
from email.mime.text import MIMEText

load_dotenv()

app = FastAPI()
db = Prisma()

origins = ["http://localhost:3000"]
CLERK_JWT_PUBLIC_KEY = os.getenv("CLERK_JWT_PUBLIC_KEY")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")  # IMPORTANT: Added missing env var

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#--------------- AUTH MIDDLEWARE ---------------#

async def verify_clerk_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    session_token = auth_header.split("Bearer ")[1]
    headers = {"Authorization": f"Bearer {CLERK_SECRET_KEY}"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        session_resp = await client.get(
            f"https://api.clerk.dev/v1/sessions/{session_token}",
            headers=headers
        )
        if session_resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")

        session_data = session_resp.json()
        user_id = session_data.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="No user_id found")

        user_resp = await client.get(
            f"https://api.clerk.dev/v1/users/{user_id}",
            headers=headers
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=401, detail="User fetch failed")
        return user_resp.json()

#--------------- EMAIL UTILS ---------------#

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "yuvanesh.ykv@gmail.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

async def send_email(to_email: str, subject: str, body: str):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print("Email failed:", e)

#--------------- DATABASE LIFESPAN ---------------#

@app.on_event("startup")
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()

#--------------- AUTH ROUTES ---------------#

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
        raise HTTPException(status_code=404, detail="Admin not found. Please sign up.")
    return {"message": "Admin logged in successfully."}

#--------------- USER AND BUSINESS ROUTES ---------------#

@app.get("/admin/users/{user_id}")
async def get_user(user_id: int = Path(...)):
    user = await db.user.find_unique(where={"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please sign in.")
    return {"User": user}

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
    business = await db.business.find_unique(where={"id": business_id})
    if not business:
        raise HTTPException(status_code=404, detail="Business not found. Go to create Business")
    return {"business": business}

@app.post("/admin/{business_id}/queues")
async def create_queues(request: Request, business_id: str = Path(...)):
    data = await request.json()
    queue_id = str(uuid4())
    title = data.get("title") or data.get("Title")
    now = datetime.now(timezone.utc)
    await db.queue.create(
        data={
            "id": queue_id,
            "title": title,
            "businessId": business_id,
            "createdAt": now,
        }
    )
    return {"message": f"Created queue successfully for the business {business_id}"}

@app.post("/user/queues/{queue_id}/join/{user_id}")
async def join_queue(queue_id: str = Path(...), user_id: int = Path(...)):
    existing = await db.queueentry.find_first(where={"queueId": queue_id, "userId": user_id})
    if existing:
        raise HTTPException(status_code=400, detail="User already joined this queue.")
    count = await db.queueentry.count(where={"queueId": queue_id})
    position = count + 1
    await db.queueentry.create(
        data={
            "queueId": queue_id,
            "userId": user_id,
            "position": position,
            "status": "waiting",
        }
    )
    return {"message": f"User {user_id} joined queue {queue_id}"}

@app.get("/user/queues/{queue_id}/position/{user_id}")
async def get_position(queue_id: str = Path(...), user_id: int = Path(...)):
    existing = await db.queueentry.find_first(where={"queueId": queue_id, "userId": user_id})
    if not existing:
        raise HTTPException(status_code=404, detail="User has not joined this queue. Please join.")
    return {"message": f"User {user_id}'s position in queue {queue_id} is {existing.position}"}

@app.get("/admin/business/{business_id}/queues")
async def get_all_business_queues(business_id: str = Path(...)):
    queues = await db.queue.find_many(where={"businessId": business_id}, order={"createdAt": "asc"})
    return {"message": f"The business {business_id} has created {len(queues)} queues", "queues": queues}

@app.get("/admin/users/{user_id}/queues")
async def get_all_users_queues(user_id: int = Path(...)):
    # Should get all QueueEntry for user_id, then join with Queue to get queue info
    queue_entries = await db.queueentry.find_many(where={"userId": user_id})
    queue_ids = [qe.queueId for qe in queue_entries]
    queues = await db.queue.find_many(where={"id": {"in": queue_ids}}, order={"createdAt": "asc"}) if queue_ids else []
    return {"message": f"The user {user_id} has joined {len(queues)} queues", "queues": queues}
@app.patch("/admin/queues/{queue_id}/status/{user_id}")
async def change_status_user(
    queue_id: str = Path(...), 
    user_id: int = Path(...), 
    request: Request = None
):
    data = await request.json()
    status_val = data.get("status")
    valid_status = ["waiting", "served", "skipped"]
    if status_val not in valid_status:
        raise HTTPException(status_code=400, detail="Invalid status")
    entry = await db.queueentry.find_first(where={"queueId": queue_id, "userId": user_id})
    if not entry:
        raise HTTPException(status_code=404, detail="User not in the queue")

    # Perform status update
    await db.queueentry.update(
        where={"id": entry.id},
        data={"status": status_val}
    )

    if status_val in ["skipped", "served"]:
        await db.queueentry.update_many(
            where={
                "queueId": queue_id,
                "position": {"gt": entry.position},
            },
            data={
                "position": {"decrement": 1}
            }
        )

    return {"message": f"Changed status of user {user_id} in queue {queue_id} to {status_val}"}


@app.get("/admin/queues/{queue_id}/status/{user_id}")
async def check_status_user(queue_id: str = Path(...), user_id: int = Path(...)):
    user_status = await db.queueentry.find_first(where={"queueId": queue_id, "userId": user_id})
    if not user_status:
        raise HTTPException(status_code=404, detail="User not in the queue")
    return {"message": f"Status of user {user_id} in queue {queue_id} is {user_status.status}"}

@app.post("/admin/queues/{queue_id}/leave/{user_id}")
async def leave_queue(queue_id: str = Path(...), user_id: int = Path(...)):
    user = await db.queueentry.find_first(where={"queueId": queue_id, "userId": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not in the queue")
    position_left = user.position
    # Mark this entry skipped
    await db.queueentry.update(
        where={"id": user.id},
        data={"status": "skipped"}
    )
    # Decrement positions of those after
    await db.queueentry.update_many(
        where={"queueId": queue_id, "position": {"gt": position_left}},
        data={"position": {"decrement": 1}}
    )
    return {"message": f"User {user_id} left the queue {queue_id}. Positions updated."}

@app.get("/admin/queues/{queue_id}")
async def get_queue(queue_id: str = Path(...)):
    queue = await db.queue.find_unique(where={"id": queue_id})
    return {"message": f"Queue details of {queue_id} is {queue}"}

@app.get("/admin/analytics/{business_id}")
async def get_all_queues_analytics_under_a_business(business_id: str = Path(...)):
    queues = await db.queue.find_many(
        where={"businessId": business_id},
        include={"queueEntries": True},
        order={"createdAt": "asc"}
    )

    business_total_users = 0
    total_served = 0
    total_skipped = 0
    total_waiting = 0
    all_queue_data = []

    for queue in queues:
        entries = queue.queueEntries
        total_users = len(entries)
        served = sum(1 for e in entries if e.status == "served")
        skipped = sum(1 for e in entries if e.status == "skipped")
        waiting = total_users - served - skipped

        business_total_users += total_users
        total_served += served
        total_skipped += skipped
        total_waiting += waiting

        all_queue_data.append({
            "queueId": queue.id,
            "title": queue.title,
            "createdAt": queue.createdAt,
            "totalUsers": total_users,
            "servedUsers": served,
            "skippedUsers": skipped,
            "waitingUsers": waiting,
        })

    average_users_per_queue = business_total_users / len(queues) if queues else 0

    return {
        "businessId": business_id,
        "totalQueues": len(queues),
        "totalUsersAcrossQueues": business_total_users,
        "averageUsersPerQueue": average_users_per_queue,
        "totalServedUsers": total_served,
        "totalSkippedUsers": total_skipped,
        "totalWaitingUsers": total_waiting,
        "queues": all_queue_data
    }

@app.post("/user/queues/{queue_id}/notify/{user_id}")
async def notify_user(queue_id: str = Path(...), user_id: int = Path(...)):
    queue_entry = await db.queueentry.find_first(
        where={"queueId": queue_id, "userId": user_id}
    )
    if not queue_entry:
        raise HTTPException(status_code=404, detail="User not found in the queue")
    if queue_entry.position == 5:
        user = await db.user.find_unique(where={"id": user_id})
        if not user or not user.email:
            raise HTTPException(status_code=404, detail="User email not found")
        subject = "Your Turn is Coming Soon!"
        body = f"Hi {user.name},\n\nYou are now position 5 in queue {queue_id}. Please be ready."
        await send_email(to_email=user.email, subject=subject, body=body)
        return {"message": f"Email notification sent to user {user_id}"}
    else:
        return {"message": f"User {user_id} is at position {queue_entry.position}, no notification sent."}
