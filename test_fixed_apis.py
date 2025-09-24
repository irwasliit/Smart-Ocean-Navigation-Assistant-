"""Extended diagnostic script for Marine Weather & AI services.

Features:
 - Loads .env (if python-dotenv installed)
 - Tests OpenAI key presence and performs model & chat test
 - Categorizes OpenAI errors (quota, auth, billing, rate limit, network)
 - Tests Open-Meteo weather API (success + forced error scenario)
 - Tests local backend (health, register/login negative & positive, save location) with detailed 4xx/5xx bodies
 - Pretty prints error JSON and offers explanations

Run:  python test_fixed_apis.py
"""

from __future__ import annotations
import os, json, time, textwrap, traceback
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass  # silently ignore if not installed

import requests

LINE = "=" * 58

def banner(title: str):
    print(f"\n{LINE}\n{title}\n{LINE}")

def truncate(text: str, limit: int = 400) -> str:
    return text if len(text) <= limit else text[:limit] + "... (truncated)"

def pretty_json(data: Any) -> str:
    try:
        return json.dumps(data, indent=2, ensure_ascii=False)[:1200]
    except Exception:
        return str(data)

def explain_openai_error(msg: str) -> str:
    lower = msg.lower()
    if 'insufficient_quota' in lower or 'quota' in lower:
        return 'Your account has exhausted its quota. Check billing/subscription at https://platform.openai.com/account/usage.'
    if 'billing' in lower or 'payment' in lower:
        return 'Billing or payment issue detected. Verify payment method and active plan.'
    if 'rate limit' in lower or 'too many requests' in lower:
        return 'Rate limit exceeded. Slow down requests or apply retry with backoff.'
    if 'invalid api key' in lower:
        return 'API key invalid. Double‑check OPENAI_API_KEY value in .env.'
    if 'organization' in lower:
        return 'Your key may not have access to the specified organization.'
    if 'timeout' in lower or 'timed out' in lower:
        return 'Network timeout. Check connectivity or retry.'
    return 'General OpenAI API error. Inspect raw message and docs for specifics.'

def safe_request(method: str, url: str, **kwargs) -> requests.Response:
    try:
        r = requests.request(method, url, timeout=30, **kwargs)
        return r
    except requests.RequestException as e:
        class Dummy:
            status_code = 0
            reason = 'NETWORK_ERROR'
            text = str(e)
            headers = {}
            def json(self):
                return {'network_error': str(e)}
        return Dummy()  # type: ignore

def test_openai():
    print("1. Testing AI (OpenAI)")
    key = os.getenv('OPENAI_API_KEY')
    if not key or key == 'your-openai-api-key':
        print("❌ AI Service: API Key missing or placeholder (OPENAI_API_KEY)")
        return
    print("✅ API Key detected (length: {} chars)".format(len(key)))

    # Support both old and new client styles
    try:
        import openai  # type: ignore
    except ImportError:
        print("❌ openai package not installed. Run: pip install openai")
        return

    # New style client (>=1.x)
    client = None
    new_style_ok = False
    if hasattr(openai, 'OpenAI'):
        try:
            client = openai.OpenAI(api_key=key)  # type: ignore[attr-defined]
            new_style_ok = True
        except Exception:
            new_style_ok = False

    # Test 1: list models (or fallback)
    try:
        if new_style_ok:
            models = client.models.list()  # type: ignore
            print(f"✅ OpenAI models retrieved (count≈{len(models.data)})")
        else:
            # Legacy
            openai.api_key = key  # type: ignore
            _ = openai.Model.list()  # type: ignore
            print("✅ OpenAI models retrieved (legacy API)")
    except Exception as e:
        msg = truncate(str(e), 500)
        print(f"⚠️  Model list error: {msg}")
        print("   ➤ Explanation:", explain_openai_error(msg))

    # Test 2: simple chat/completion
    try:
        if new_style_ok:
            resp = client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[{"role": "user", "content": "Return one-word: Weather"}],
                max_tokens=5,
            )
            content = resp.choices[0].message.content if resp.choices else ''
            print("✅ Chat test succeeded:", content)
        else:
            resp = openai.ChatCompletion.create(  # type: ignore
                model=os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[{"role": "user", "content": "Return one-word: Weather"}],
                max_tokens=5,
            )
            content = resp.choices[0].message['content'] if resp.choices else ''
            print("✅ Chat test succeeded:", content)
    except Exception as e:
        msg = truncate(str(e), 500)
        print(f"⚠️  Chat error: {msg}")
        print("   ➤ Explanation:", explain_openai_error(msg))

def test_weather_service():
    print("2. Testing External Weather (Open-Meteo)")
    lat, lon = 40.7128, -74.0060
    base_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        'latitude': lat,
        'longitude': lon,
        'current': 'temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,pressure_msl,visibility',
        # Do NOT include wave parameters here; fetch from marine API after success
        'hourly': 'visibility',
        'timezone': 'auto'
    }
    r = safe_request('GET', base_url, params=params)
    if r.status_code == 200:
        data = r.json()
        current = data.get('current', {})
        print("✅ Weather API: success")
        print(f"   Temperature: {current.get('temperature_2m', 'N/A')}°C")
        print(f"   Wind Speed: {current.get('wind_speed_10m', 'N/A')} km/h")
        # Fetch wave data separately from marine endpoint
        marine_url = "https://marine-api.open-meteo.com/v1/marine"
        marine_params = {
            'latitude': lat,
            'longitude': lon,
            'hourly': 'wave_height,wave_period',
            'timezone': 'auto'
        }
        m_resp = safe_request('GET', marine_url, params=marine_params)
        if m_resp.status_code == 200:
            m_data = m_resp.json()
            waves = m_data.get('hourly', {}).get('wave_height', ['N/A'])
            print(f"   Wave Height (first hour): {waves[0] if waves else 'N/A'} m (marine API)")
        else:
            print(f"   ⚠️ Marine wave fetch failed {m_resp.status_code} {m_resp.reason}")
    else:
        print(f"❌ Weather API error {r.status_code} {r.reason}")
        try:
            print("   Body:", truncate(r.text, 600))
        except Exception:
            pass

    # Forced error test (invalid latitude)
    bad_params = params.copy()
    bad_params['latitude'] = 90  # invalid
    r_bad = safe_request('GET', base_url, params=bad_params)
    if r_bad.status_code != 200:
        print(f"⚠️  Expected failure test (invalid lat) -> {r_bad.status_code} {r_bad.reason}")
        print("   Body:", truncate(r_bad.text, 300))
    else:
        print("(Unexpected) invalid latitude still returned 200")

def explain_http_error(status: int, body: Optional[Dict[str, Any]]):
    if status == 400:
        return 'Bad Request: parameters invalid or missing.'
    if status == 401:
        return 'Unauthorized: token missing/invalid.'
    if status == 403:
        return 'Forbidden: insufficient permissions.'
    if status == 404:
        return 'Not Found: endpoint or resource does not exist.'
    if status == 422:
        return 'Unprocessable Entity: validation failed (check field names/types).'
    if status == 429:
        return 'Too Many Requests: rate limit; retry later.'
    if 500 <= status < 600:
        return 'Server error: internal failure. Inspect server logs.'
    return 'HTTP status encountered.'

def test_local_backend():
    print("3. Testing Local Backend (FastAPI)")
    base = os.getenv('BACKEND_BASE_URL', 'http://localhost:8000')
    def req(method: str, path: str, token: Optional[str]=None, **kwargs):
        headers = kwargs.pop('headers', {})
        if token:
            headers['Authorization'] = f'Bearer {token}'
        return safe_request(method, f"{base}{path}", headers=headers, **kwargs)

    # Health
    r = req('GET', '/health')
    if r.status_code == 200:
        print("✅ /health:", r.json())
    else:
        print(f"❌ /health {r.status_code} {r.reason}")

    # Register (random email) & login
    import random
    email = f"diag_{random.randint(10000,99999)}@example.com"
    password = 'Passw0rd!'
    reg_payload = {"email": email, "password": password, "full_name": "Diag User"}
    r_reg = req('POST', '/api/auth/register', json=reg_payload)
    if r_reg.status_code == 200:
        print("✅ register success")
    else:
        print(f"⚠️  register {r_reg.status_code}")
        print("   Detail:", truncate(r_reg.text, 300))

    # Login
    r_login = req('POST', '/api/auth/login', json={"email": email, "password": password})
    token = None
    if r_login.status_code == 200:
        token = r_login.json().get('access_token')
        print("✅ login success (token acquired)")
    else:
        print(f"❌ login {r_login.status_code} ->", truncate(r_login.text, 300))
        print("   Explanation:", explain_http_error(r_login.status_code, None))
        return

    # Save location (expected 200 after earlier schema fix)
    loc_payload = {"name": "Diag Loc", "latitude": 10.0, "longitude": 20.0, "location_type": "single"}
    r_loc = req('POST', '/api/weather/locations', token, json=loc_payload)
    if r_loc.status_code == 200:
        print("✅ save location success (id:", r_loc.json().get('id'), ")")
    else:
        print(f"❌ save location {r_loc.status_code}")
        print("   Body:", truncate(r_loc.text, 400))
        print("   Explanation:", explain_http_error(r_loc.status_code, None))

    # Force validation error (missing latitude)
    bad_loc_payload = {"name": "Bad Loc", "longitude": 30.0, "location_type": "single"}
    r_bad_loc = req('POST', '/api/weather/locations', token, json=bad_loc_payload)
    if r_bad_loc.status_code == 422:
        print("⚠️  Expected 422 validation -> good diagnostic")
        print("   Body:", truncate(r_bad_loc.text, 400))
    else:
        print("(Unexpected) validation test status:", r_bad_loc.status_code)

def main():
    print("🔧 Diagnostic Test Suite: Marine Weather & AI")
    banner("AI SERVICE TEST")
    test_openai()
    banner("WEATHER SERVICE TEST")
    test_weather_service()
    banner("LOCAL BACKEND TEST")
    test_local_backend()
    banner("SUMMARY")
    print("Review above sections. Address missing keys, HTTP errors, or schema mismatches as indicated.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print("Fatal error:", e)
        traceback.print_exc()