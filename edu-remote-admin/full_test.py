"""FULL TEST SUITE - all commands + edge cases"""
import json
import time
import sys
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

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="edu-ra-fulltest", protocol=mqtt.MQTTv5)
c.on_connect = on_connect
c.on_message = on_message
c.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
c.loop_start()
time.sleep(2)

def test(name, cmd, expect_contains=None, max_len=200):
    global last_response
    last_response = {}
    c.publish(TOPIC_CMDS, json.dumps({"cmd": cmd}))
    deadline = time.time() + 15
    while not last_response and time.time() < deadline:
        time.sleep(0.3)
    if last_response:
        result = last_response.get("result", "")
        status = "PASS"
        if expect_contains and expect_contains not in result:
            status = "FAIL (missing expected text)"
        results.append((name, cmd, status, result[:max_len]))
    else:
        results.append((name, cmd, "FAIL (no response)", ""))

# ============ NORMAL COMMANDS ============
test("sysinfo", "sysinfo", "OS:")
test("help", "help", "COMMANDS")
test("pwd", "pwd")
test("ls", "ls")
test("battery", "battery")
test("uptime", "uptime")
test("ipconfig", "ipconfig")
test("whoami", "whoami", "subha")

# ============ FILES ============
test("cat known file", "cat C:/Users/subha/Desktop/New\\ folder/Testing/edu-remote-admin/README.md", "Edu Remote Admin")
test("ls specific dir", "ls C:/Users", "subha")

# ============ EDGE CASES ============
test("ls nonexistent", "ls Z:/does/not/exist")
test("cat nonexistent", "cat Z:/does/not/exist.txt")
test("download nonexistent", "download Z:/fake/file.txt")
test("empty-ish dir ls", "ls C:/Users/subha/Desktop")
test("dir with spaces", "ls C:/Program Files")
test("special chars in cmd", "echo hello&world", "hello")
test("numbers only", "echo 12345", "12345")
test("very long output cmd", "dir C:\\Users", "")

# ============ SYSTEM COMMANDS ============
test("tasklist", "tasklist", ".exe")
test("hostname", "hostname")
test("date", "date /t")

print("\n" + "="*60)
print("TEST RESULTS")
print("="*60)
for name, cmd, status, result in results:
    print(f"\n[{status}] {name}")
    print(f"  cmd: {cmd}")
    print(f"  result: {result[:100]}")
print(f"\n{'='*60}")
print(f"TOTAL: {len(results)} tests")
passes = sum(1 for r in results if r[2].startswith("PASS"))
print(f"PASSED: {passes}")
