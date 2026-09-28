import json
import urllib.request
import urllib.error
from uuid import uuid4

API_URL = "http://localhost:8000"

def run_live_tests():
    print("=== LIVE API TEST ON http://localhost:8000 ===")
    
    # 1. Register a test user
    email = f"test_live_{uuid4().hex[:8]}@example.com"
    password = "StrongPassword123!"
    reg_payload = json.dumps({
        "email": email,
        "password": password,
        "display_name": "Test Live User",
    }).encode("utf-8")
    
    req = urllib.request.Request(
        f"{API_URL}/api/v1/auth/register",
        data=reg_payload,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            access_token = data.get("access_token")
            user_id = data.get("user", {}).get("id")
            print(f"Registered test user: {email} (id: {user_id})")
    except urllib.error.HTTPError as e:
        print(f"Registration failed: {e.code} - {e.read().decode('utf-8')}")
        return

    # Add a transaction so user has real financial facts
    # First get or create account
    acc_payload = json.dumps({
        "name": "Tài khoản chính",
        "type": "BANK",
        "currency": "VND",
        "opening_balance": 15000000.0,
    }).encode("utf-8")
    req_acc = urllib.request.Request(
        f"{API_URL}/api/v1/accounts",
        data=acc_payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    )
    try:
        with urllib.request.urlopen(req_acc) as resp:
            acc_data = json.loads(resp.read().decode("utf-8"))
            account_id = acc_data.get("id")
            print(f"Created account: {account_id}")
    except urllib.error.HTTPError as e:
        print(f"Account creation: {e.code} - {e.read().decode('utf-8')}")

    # The 4 Required Live Test Queries
    queries = [
        "trước tháng 8 ý",
        "quy tắc 50/30/20 là gì?",
        "Tháng này tôi đã chi bao nhiêu?",
        "Phân tích chi tiêu 6 tháng qua của tôi.",
    ]

    results = {}
    for idx, q in enumerate(queries, start=1):
        print(f"\n==================================================")
        print(f"LIVE QUERY {idx}: '{q}'")
        print(f"==================================================")
        payload = json.dumps({"question": q, "currency": "VND"}).encode("utf-8")
        req_query = urllib.request.Request(
            f"{API_URL}/api/v1/ai/query",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
        )
        try:
            with urllib.request.urlopen(req_query) as resp:
                status_code = resp.status
                body = json.loads(resp.read().decode("utf-8"))
                results[q] = body
                print(f"HTTP Status: {status_code}")
                print(f"RAW JSON RESPONSE:")
                print(json.dumps(body, indent=2, ensure_ascii=False))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            print(f"HTTP Error {e.code}: {err_body}")
            results[q] = {"error": e.code, "body": err_body}

    return results

if __name__ == "__main__":
    run_live_tests()
