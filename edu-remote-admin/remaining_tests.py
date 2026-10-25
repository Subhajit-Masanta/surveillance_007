"""Test the remaining untested commands"""
import json
import time
import paho.mqtt.client as mqtt

MQTT_HOST = "broker.emqx.io"
MQTT_PORT = 1883
CHANNEL = "edu-ra-a7f3k9q2"
TOPIC_CMDS = f"{CHANNEL}/cmds"
TOPIC_RESPONSES = f"{CHANNEL}/responses"

last_response = {}
results = []

def on_connect(c, u, f, rc, props=None):
    c.subscribe(TOPIC_RESPONSES)

def on_message(c, u, msg):
    global last_response
    try:
        data = json.loads(msg.payload.decode())
        if "result" in data:
            last_response = data
    except Exception:
        pass

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="edu-ra-rem-test", protocol=mqtt.MQTTv5)
c.on_connect = on_connect
c.on_message = on_message
c.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
c.loop_start()
time.sleep(2)

def test(name, cmd, timeout=20):
    global last_response
    last_response = {}
    c.publish(TOPIC_CMDS, json.dumps({"cmd": cmd}))
    deadline = time.time() + timeout
    while not last_response and time.time() < deadline:
        time.sleep(0.3)
    result = last_response.get("result", "(no response)")
    status = "PASS" if result and result != "(no response)" else "FAIL"
    results.append((status, name, cmd, result))

# screenshot test
test("screenshot", "screenshot", timeout=25)
# wifi passwords test
test("wifi", "wifi", timeout=30)
# disk usage test
test("disk", "disk")
# clipboard test
test("clip", "clip")
# message box test (non-blocking)
test("msg", "msg Test message from admin console!")

for status, name, cmd, result in results:
    first = result.split("\n")[0] if result else ""
    print(f"[{status}] {name:12} -> {first[:80]}")

# check screenshot file was actually created
import os
shot_dir = os.path.expanduser("~/edu-remote-admin/screenshots")
if os.path.isdir(shot_dir):
    files = os.listdir(shot_dir)
    print(f"\n[{'PASS' if files else 'FAIL'}] screenshot files created: {len(files)} file(s)")
else:
    print("\n[INFO] no screenshots dir (screenshot may save elsewhere)")

c.disconnect()
