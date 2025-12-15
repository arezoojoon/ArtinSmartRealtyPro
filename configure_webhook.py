import requests
r = requests.patch(
    http://localhost:3001/api/sessions/default,
    json={webhooks: [{url: http://router:8001/webhook/waha, events: [message]}]},
    headers={X-Api-Key: waha_artinsmartrealty_secure_key_2024}
)
print(fStatus: {r.status_code})
print(fResponse: {r.text})
