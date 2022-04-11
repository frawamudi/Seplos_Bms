import json

bmsJsonData = {
    "bankvoltage": 53.20,
    "busvoltage": 53.86,
    "cellvoltages": {
        "bank0":[4.078, 4.093, 4.096, 4.143, 4.076, 4.099, 4.099, 4.094, 4.052, 4.045, 4.087, 4.079, 4.068, 4.073],
        "bank1":[],
        "bank2":[],
        "bank3":[],
        "bank4":[],
        "bank5":[],
        "bank6":[],
        "bank7":[],
        "bank8":[],
        "bank9":[],
        "bank10":[],
        "bank11":[],
        "bank12":[],
        "bank13":[]
    },
    "charging": False,
    "discharging": True,
    "standby": False,
    "current": 8.60,
    "power": 457.52,
    "S.O.C": 91,
    "S.O.H": 100,
    "batterycycles": 3,
    "bankN": 0,
    "status":[]
}

#bmsJsonData
# the json file where the output must be stored
out_file = open("myfile.json", "w")
  
json.dump(bmsJsonData, out_file, indent = 6)
  
out_file.close()

b = json.dumps(bmsJsonData, indent = 6)
print(b)