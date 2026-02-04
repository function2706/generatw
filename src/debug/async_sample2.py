import time

import requests

urls = ["https://httpbin.org/delay/1" for _ in range(10)]

start = time.time()

for url in urls:
    requests.get(url)

print("elapsed:", time.time() - start)
