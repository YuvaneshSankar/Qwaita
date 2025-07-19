import asyncio
import httpx
from httpx import ASGITransport
from main import app, db

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
ENDC = "\033[0m"
all_results = []

def print_result(route, method, request, response, passed, error=""):
    color = GREEN if passed else RED
    status_line = f"{color}{'PASS' if passed else 'FAIL'}{ENDC}"
    print(f"{YELLOW}{method} {route}{ENDC}")
    print(f"    Input:   {request}")
    print(f"    Output:  {response.status_code} {response.text}")
    if error:
        print(f"    Error:   {RED}{error}{ENDC}")
    print(f"    ---- {status_line} ----\n")
    all_results.append((route, method, status_line, response.status_code, error, request, response.text))

async def main():
    await db.connect()

    # --- Create Dummy Users/Admin if not exist
    # These clerkUserIds are guaranteed "unique" and easy for lookup
    DUMMY_CUSTOMER_CLERK = "dummy_customer"
    DUMMY_ADMIN_CLERK = "dummy_admin"
    customer = await db.user.find_unique(where={"clerkUserId": DUMMY_CUSTOMER_CLERK})
    if not customer:
        customer = await db.user.create(data={
            "clerkUserId": DUMMY_CUSTOMER_CLERK,
            "name": "Customer Test",
            "email": "customer@test.com",
            "role": "customer"
        })
    user_id = customer.id

    admin = await db.user.find_unique(where={"clerkUserId": DUMMY_ADMIN_CLERK})
    if not admin:
        admin = await db.user.create(data={
            "clerkUserId": DUMMY_ADMIN_CLERK,
            "name": "Admin Test",
            "email": "admin@test.com",
            "role": "admin"
        })
    admin_id = admin.id

    business_id = None
    queue_id = None
    pass_count = 0
    fail_count = 0

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:

        # --- CREATE BUSINESS (as admin for user_id)
        create_biz_route = f"/admin/{user_id}/businesses"
        biz_payload = {"name": "NewTestBiz"}
        resp = await ac.post(create_biz_route, json=biz_payload)
        passed = resp.status_code == 200
        print_result(create_biz_route, "POST", biz_payload, resp, passed)
        pass_count += passed
        fail_count += not passed
        if passed:
            all_biz = await db.business.find_many(where={"ownerId": user_id})
            if all_biz:
                business_id = all_biz[-1].id

        # --- CREATE QUEUE in Business
        queue_payload = {"title": "QueueTest"}
        if business_id:
            create_queue_route = f"/admin/{business_id}/queues"
            resp = await ac.post(create_queue_route, json=queue_payload)
            passed = resp.status_code == 200
            print_result(create_queue_route, "POST", queue_payload, resp, passed)
            pass_count += passed
            fail_count += not passed

            all_queues = await db.queue.find_many(where={"businessId": business_id})
            if all_queues:
                queue_id = all_queues[-1].id

        # --- USER JOIN QUEUE
        if queue_id:
            join_route = f"/user/queues/{queue_id}/join/{user_id}"
            resp = await ac.post(join_route)
            passed = resp.status_code in (200, 400)
            print_result(join_route, "POST", {}, resp, passed)
            pass_count += passed
            fail_count += not passed

            # POSITION IN QUEUE
            pos_route = f"/user/queues/{queue_id}/position/{user_id}"
            resp = await ac.get(pos_route)
            passed = resp.status_code in (200, 404)
            print_result(pos_route, "GET", {}, resp, passed)
            pass_count += passed
            fail_count += not passed

        # --- ADMIN CHANGE STATUS
        if queue_id:
            status_route = f"/admin/queues/{queue_id}/status/{user_id}"
            resp = await ac.patch(status_route, json={"status": "served"})
            passed = resp.status_code in (200, 404)
            print_result(status_route, "PATCH", {"status": "served"}, resp, passed)
            pass_count += passed
            fail_count += not passed

            # CHECK STATUS
            check_status_route = f"/admin/queues/{queue_id}/status/{user_id}"
            resp = await ac.get(check_status_route)
            passed = resp.status_code in (200, 404)
            print_result(check_status_route, "GET", {}, resp, passed)
            pass_count += passed
            fail_count += not passed

            # LEAVE QUEUE
            leave_route = f"/admin/queues/{queue_id}/leave/{user_id}"
            resp = await ac.post(leave_route)
            passed = resp.status_code in (200, 404)
            print_result(leave_route, "POST", {}, resp, passed)
            pass_count += passed
            fail_count += not passed

        # --- ANALYTICS & LISTINGS ---
        if business_id:
            analytics_route = f"/admin/analytics/{business_id}"
            resp = await ac.get(analytics_route)
            passed = resp.status_code == 200
            print_result(analytics_route, "GET", {}, resp, passed)
            pass_count += passed
            fail_count += not passed

            get_queues_route = f"/admin/business/{business_id}/queues"
            resp = await ac.get(get_queues_route)
            passed = resp.status_code == 200
            print_result(get_queues_route, "GET", {}, resp, passed)
            pass_count += passed
            fail_count += not passed

        get_user_queues_route = f"/admin/users/{user_id}/queues"
        resp = await ac.get(get_user_queues_route)
        passed = resp.status_code == 200
        print_result(get_user_queues_route, "GET", {}, resp, passed)
        pass_count += passed
        fail_count += not passed

    print(f"\n{YELLOW}----- TEST SUMMARY -----{ENDC}")
    for (route, method, status, code, error, req, resp_txt) in all_results:
        if status == f"{GREEN}PASS{ENDC}":
            print(f"{GREEN}PASS{ENDC}  {method} {route} ({code})")
        else:
            print(f"{RED}FAIL{ENDC}  {method} {route} ({code}): {error}")
    print(f"\n{YELLOW}TOTAL: {len(all_results)} | PASSED: {pass_count} | FAILED: {fail_count}{ENDC}")

    print("\nInputs and outputs for each route:")
    for (route, method, status, code, error, req, resp_txt) in all_results:
        print(f"\nRoute: {route}")
        print(f"Method: {method}")
        print(f"Input: {req}")
        print(f"Status: {status}")
        print(f"Output: {resp_txt}")

    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
