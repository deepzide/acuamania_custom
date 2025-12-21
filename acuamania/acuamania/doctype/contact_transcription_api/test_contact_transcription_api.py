import os
import random
import string

import requests

# ================================================================
# CONSTANTS
# ================================================================

BASE_URL = "http://localhost:8000"

ENDPOINT = (
	"/api/method/"
	"acuamania.acuamania.doctype.contact_transcription_api."
	"contact_transcription_api.append_transcription"
)

CONTACT_PHONE = "099111222"
EMAIL_RANDOM_LENGTH = 5
EMAIL_DOMAIN = "test.com"

# Load credentials from site_config.json (exported by you via env)
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")


# ================================================================
# HELPERS
# ================================================================


def random_email():
	name = "".join(random.choices(string.ascii_lowercase, k=EMAIL_RANDOM_LENGTH))
	return f"{name}@{EMAIL_DOMAIN}"


def api_headers():
	return {"Authorization": f"token {API_KEY}:{API_SECRET}"}


# ================================================================
# TESTS (HTTP REAL)
# ================================================================


def test_append_creates_buffer():
	# Create a new Contact via API or database fixture
	requests.post(
		f"{BASE_URL}/api/resource/Contact",
		headers=api_headers(),
		json={
			"first_name": "Test User",
			"email_id": random_email(),
			"phone_nos": [{"phone": CONTACT_PHONE}],
			"custom_transcription_text": "",
		},
	)

	# Call the endpoint via REQUESTS (real HTTP)
	r = requests.post(
		f"{BASE_URL}{ENDPOINT}", data={"phone": CONTACT_PHONE, "message": "Hola"}, headers=api_headers()
	)
	assert r.status_code == 200

	# Now retrieve the contact via API
	contact = requests.get(
		f'{BASE_URL}/api/resource/Contact?filters={{"phone":"{CONTACT_PHONE}"}}', headers=api_headers()
	).json()

	docname = contact["data"][0]["name"]

	# Fetch full doc
	doc = requests.get(f"{BASE_URL}/api/resource/Contact/{docname}", headers=api_headers()).json()

	assert doc["data"]["custom_transcription_text"] == "Hola"


def test_ignore_if_no_contact():
	r = requests.post(
		f"{BASE_URL}{ENDPOINT}", data={"phone": "00000000", "message": "Hola"}, headers=api_headers()
	)

	assert r.status_code == 200
	j = r.json()
	assert j["status"] == "ignored"
	assert j["reason"] == "Contact not found for this phone"
