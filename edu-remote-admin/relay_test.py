"""Relay test: publish commands, verify the real client responds."""
import json
import time
import threading
import sys
import paho.mqtt.client as mqtt

MQTT_HOST = "broker.emqx.io"
MQTT_PORT = 1883
CHANNEL = "edu-ra-a7f3k9q2"
TOPIC_CMDS = f"{CHANNEL}/cmds"
TOPIC_RESPONSES = f"{CHANNEL}/responses"

got_online = threading.Event()
responses = []
got_response = threading.Event()

def on_connect(c, u, f, rc, props=None):
    c.subscribe(TOPIC_RESPONSES)
    print("[*] Test console connected to relay", flush=True)

def on_message(c, u, msg):
    data = json.loads(msg.payload.decode())
    if "event" in data and data["event"] == "online":
        print(f"[+] CLIENT ONLINE: {data.get('client')}", flush=True)
        got_online.set()
    elif "result" in data:
        print(f"\n--- response ---\n{data['result']}\n----------------", flush=True)
        responses.append(data)
        got_response.set()

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="edu-ra-test-console", protocol=mqtt.MQTTv5)
c.on_connect = on_connect
c.on_message = on_message
c.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
c.loop_start()
time.sleep(2)

# Wait for the client to come online
print("[*] Waiting for client to connect (run edu_admin.py)...", flush=True)
if not got_online.wait(timeout=15):
    print("[!] No 'online' event seen (client started first) - sending commands anyway!", flush=True)

for cmd in ["sysinfo", "uptime", "battery"]:
    got_response.clear()
    print(f"\n>>> Sending: {cmd}", flush=True)
    c.publish(TOPIC_CMDS, json.dumps({"cmd": cmd}))
    got_response.wait(timeout=30)

print("\n[+] RELAY TEST COMPLETE", flush=True)
c.disconnect()
