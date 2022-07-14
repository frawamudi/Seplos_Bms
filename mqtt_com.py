#https://www.digi.com/resources/documentation/Digidocs/90001541/reference/r_example_publish_mqtt.htm
#https://www.emqx.com/en/blog/how-to-use-mqtt-in-python
#https://github.com/eclipse/paho.mqtt.python
#https://www.digi.com/resources/documentation/Digidocs/90001541/reference/r_example_publish_mqtt.htm
#http://www.steves-internet-guide.com/into-mqtt-python-client/
#https://www.delftstack.com/howto/git/move-commit-to-another-branch-in-git/
from paho.mqtt import client as mqtt_client
import time
#import json

broker = 'localhost'
port = 1883
topic = "Workshop/BMS"
client_id = ""
#f'python-mqtt-{random.randint(0, 1000)}'
username = "Sunhive"
password = 'Sunhive'

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID
    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    client.loop_start()  # Start networking daemon
    return client


def publish(client, msg):
    msg_count = 0
    #while True:
    time.sleep(1)
    msg1 = f"messages: {msg_count}"
    result = client.publish(topic, msg)
    # result: [0, 1]
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic}`")
        client.loop_stop()
    else:
        print(f"Failed to send message to topic {topic}")
        msg_count += 1

def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

    client.subscribe(topic)
    client.on_message = on_message

"""
def run():
    client = connect_mqtt()
    #subscribe(client)
    client.loop_start()

    data = {
        "Bank": 0,
        "Rack Voltage": 51.20,
        "Module Voltage": 51.00,
        "Min cell Voltage": 3.50,
        "Max cell Voltage": 3.60,
        "Cell Voltages": [3.55, 3.52, 3.51, 3.60, 3.54, 3.57, 3.55, 3.55, 3.52, 3.51, 3.60, 3.54, 3.57, 3.55],
        "Current": 25.40,
        "SOC":47,
        "BMS Cycles": 4
    }

    msg = json.dumps(data)
    publish(client, msg)
    #client.loop_forever()


if __name__ == '__main__':
    run() 
"""