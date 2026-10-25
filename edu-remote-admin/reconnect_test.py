"""Test: reconnect behavior and cleanup"""
import json
import time
import subprocess
import paho.mqtt.client as mqtt

MQTT_HOST = "broker.emqx.io"
MQTT_PORT = 1883
CHANNEL = "edu-ra-a7f3k9q2"
TOPIC_CMDS = f"{CHANNEL}/cmds"
TOPIC_RESPONSES = f"{CHANNEL}/responses"

last_response = {}

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

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="edu-ra-recon-test", protocol=mqtt.MQTTv5)
c.on_connect = on_connect
c.on_message = on_message
c.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
c.loop_start()
time.sleep(2)

def send_cmd(cmd, timeout=15):
    global last_response
    last_response = {}
    c.publish(TOPIC_CMDS, json.dumps({"cmd": cmd}))
    deadline = time.time() + timeout
    while not last_response and time.time() < deadline:
        time.sleep(0.3)
    return last_response.get("result", "(no response)")

# TEST 1: Kill the client process. It should NOT restart (no watchdog).
# But the INSTALLED copy can be manually started again.
print("[*] Test 1: Kill client and check if it's still responding...")
subprocess.run(["taskkill", "/f", "/im", "EduRemoteAdmin.exe"], capture_output=True)
time.sleep(2)
result = send_cmd("whoami")
if "no response" in result or not result:
    print("[PASS] Client died and did not respond (expected)")
else:
    print(f"[?] Client responded after kill: {result}")

# TEST 2: Start the installed copy manually (simulating a reboot auto-start)
print("[*] Test 2: Start installed copy and check if it responds...")
import os
os.system('start "" "C:/Users/subha/edu-remote-admin/EduRemoteAdmin.exe"')
time.sleep(5)
result = send_cmd("whoami")
if "subha" in result:
    print("[PASS] Installed copy started and responded correctly")
else:
    print(f"[FAIL] Installed copy did not respond: {result}")

print("\n[*] All reconnect tests complete")
c.disconnect()
