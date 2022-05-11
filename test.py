import requests
from requests.structures import CaseInsensitiveDict
import json

url = "http://batterystatus.sunhive.com/api/devices/update"

headers = CaseInsensitiveDict()
#headers["Content-Type"] = "application/json"

headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

data = {
    "deviceID": "SH001",
    "address": "12c Talabi Lagos",
    "size": "12kwh",
    "max_min": "50",
    "numberOfCycle": 11,
    "status": 1
}

p = json.dumps(data, indent=6)
#print(p)


resp = requests.post(url, data=p, headers=headers)

print(resp.status_code)
print(resp.text)

