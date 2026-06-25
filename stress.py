import requests
import concurrent.futures
import time

API = "http://localhost:8080/api/shorten"

TOTAL_REQUESTS = 100000
WORKERS = 5000


def create_url(i):
    try:
        r = requests.post(
            API,
            json={
                "url": f"https://example.com/page/{i}"
            },
            timeout=5
        )

        if r.status_code != 200:
         print("FAILED:", r.status_code, r.text)

        return r.status_code

    except Exception as e:
        return "ERROR"


start = time.time()

success = 0
failed = 0

with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:

    results = executor.map(
        create_url,
        range(TOTAL_REQUESTS)
    )

    for status in results:
        if status == 200:
            success += 1
        else:
            failed += 1


end = time.time()

print("====================")
print("Requests:", TOTAL_REQUESTS)
print("Success:", success)
print("Failed:", failed)
print("Time:", round(end-start, 2), "seconds")
print(
    "RPS:",
    round(TOTAL_REQUESTS/(end-start),2)
)