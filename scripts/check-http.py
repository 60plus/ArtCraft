"""Check the desktop HTTP handler and authentication from inside the container."""
import base64
import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen

url = "http://127.0.0.1:3000/"
try:
    with urlopen(url, timeout=10) as response:
        raise RuntimeError(f"Unauthenticated access returned {response.status}")
except HTTPError as error:
    assert error.code == 401, error.code
credentials = (os.environ["CUSTOM_USER"] + ":" + os.environ["PASSWORD"]).encode()
request = Request(url, headers={"Authorization": "Basic " + base64.b64encode(credentials).decode()})
with urlopen(request, timeout=10) as response:
    assert response.status == 200, response.status
    assert b"<html" in response.read().lower()
print("Desktop HTTP: unauthenticated=401, authenticated=200; HTML received")
