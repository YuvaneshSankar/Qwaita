from fastapi import FastAPI, Path
from prisma import Prisma

app = FastAPI()
db = Prisma()


@app.on_event("startup")
async def connect_db():
    await db.connect()

@app.on_event("shutdown")
async def disconnect_db():
    await db.disconnect()

@app.get("/")
def header():
    return {"message": "Hi there"}


@app.post("/users")
def create_user():
    return {"message": "Created user"}

@app.get("/admin/users/{user_id}")
def get_user(user_id: int = Path(...)):
    return {"message": f"User details of {user_id}"}

@app.get("/admin/users/{user_id}/queues")
def get_all_users_queues(user_id: int = Path(...)):
    return {"message": f"The user {user_id} has joined these many queues"}


@app.post("/admin/businesses")
def create_business():
    return {"message": "Created business"}

@app.get("/admin/business/{business_id}")
def get_business(business_id: int = Path(...)):
    return {"message": f"Business details of {business_id}"}

@app.get("/admin/business/{business_id}/queues")
def get_all_business_queues(business_id: int = Path(...)):
    return {"message": f"The business {business_id} has created these queues"}

@app.get("/admin/analytics/{business_id}")
def get_all_queues_analytics_under_a_business(business_id: int = Path(...)):
    return {"message": f"These are the analytics of all queues created by business {business_id}"}


@app.post("/admin/queues")
def create_queues():
    return {"message": "Created queue"}

@app.get("/admin/queues/{queue_id}")
def get_queue(queue_id: int = Path(...)):
    return {"message": f"Queue details of {queue_id}"}

@app.patch("/admin/queues/{queue_id}/status/{user_id}")
def change_status_user(queue_id: int = Path(...), user_id: int = Path(...)):
    return {"message": f"Changed status of user {user_id} in queue {queue_id}"}

@app.get("/admin/queues/{queue_id}/status/{user_id}")
def check_status_user(queue_id: int = Path(...), user_id: int = Path(...)):
    return {"message": f"Status of user {user_id} in queue {queue_id}"}


@app.post("/user/queues/{queue_id}/join/{user_id}")
def join_queue(queue_id: int = Path(...), user_id: int = Path(...)):
    return {"message": f"User {user_id} joined queue {queue_id}"}

@app.post("/user/queues/{queue_id}/notify/{user_id}")
def notify_user(queue_id: int = Path(...), user_id: int = Path(...)):
    return {"message": f"Notified user {user_id} in queue {queue_id}"}

@app.get("/user/queues/{queue_id}/position/{user_id}")
def get_position(queue_id: int = Path(...), user_id: int = Path(...)):
    return {"message": f"User {user_id}'s position in queue {queue_id}"}
