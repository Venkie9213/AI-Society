import hashlib
import hmac
import time
import requests
import json

SECRET = "your_secret_here"
URL = "http://localhost:8000/webhooks/slack/events"

def generate_signature(timestamp, body):
    sig_basestring = f"v0:{timestamp}:{body}"
    my_signature = 'v0=' + hmac.new(
        SECRET.encode('utf-8'),
        sig_basestring.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return my_signature

def test_proxy():
    payload = {
        "type": "url_verification",
        "challenge": "verification_challenge_123",
        "token": "valid_token"
    }
    body = json.dumps(payload)
    timestamp = str(int(time.time()))
    signature = generate_signature(timestamp, body)
    
    headers = {
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": signature,
        "Content-Type": "application/json"
    }
    
    print(f"Sending request to {URL} with signature {signature}...")
    try:
        response = requests.post(URL, data=body, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200 and response.json().get("challenge") == "verification_challenge_123":
             print("SUCCESS: Proxy verification passed!")
        else:
             print("FAILURE: Proxy verification failed.")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_proxy()
