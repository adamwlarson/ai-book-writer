# OpenRouter Integration Guide

## Purpose  
Minimal directives for integrating and enumerating OpenRouter models using its REST interface. :contentReference[oaicite:0]{index=0}  

---

## Project Quick Start (ai-book-writer)  
1. Copy `.env.example` to `.env` and set `OPENROUTER_API_KEY=sk-...`.  
2. Optional overrides go in `.env` (OPENROUTER_MODEL, OPENROUTER_BASE_URL, OPENROUTER_HTTP_REFERER, OPENROUTER_APP_TITLE) or your shell environment.  
3. Run `python main.py` or `streamlit run streamlit_app.py`; choose **OpenRouter** in the provider selector.  
4. Programmatic access: `get_config(use_openrouter=True, model="mistralai/mistral-large")`.  
5. Clear the provider toggle or remove the API key to fall back to the local endpoint.  

## Base URL  
`https://openrouter.ai/api/v1`  

OpenRouter mirrors the OpenAI schema for `/chat/completions` and `/completions`; drop-in replacement feasible. :contentReference[oaicite:1]{index=1}  

---

## Authentication  
1. Register at **openrouter.ai** → **API Keys**.  
2. Retrieve key string `sk-...`.  
3. Attach header:  

```http
Authorization: Bearer <YOUR_API_KEY>
```  

Bearer token required on every call. :contentReference[oaicite:2]{index=2}  

---

## Enumerate All Models  

```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```  

Returns JSON:

```json
{
  "data": [
    {
      "id": "openai/gpt-4o",
      "name": "GPT-4o",
      "context_length": 128000,
      "pricing": { "prompt": 5e-5, "completion": 1e-4 },
      "supported_parameters": ["temperature","top_p",...]
    }
  ]
}
```  

Endpoint lists every model currently routable. :contentReference[oaicite:3]{index=3}  

---

## Inspect Endpoints for One Model  

```bash
curl https://openrouter.ai/api/v1/models/openai/gpt-4o/endpoints \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```  

Reveals provider-specific hostnames, useful for latency testing or self-routing. :contentReference[oaicite:4]{index=4}  

---

## Chat Completion Request  

```bash
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "model": "openai/gpt-4o",
        "messages": [
          {"role":"system","content":"You are concise."},
          {"role":"user","content":"Ping"}
        ],
        "temperature": 0.5,
        "stream": false
      }'
```  

Schema identical to OpenAI; supply `messages` array plus optional sampling parameters. :contentReference[oaicite:5]{index=5}  

---

## Streaming  

Add `"stream": true`; server yields SSE chunks with `data:` payloads. :contentReference[oaicite:6]{index=6}  

---

## Provider Routing Control  

Include optional `provider` object:

```json
"provider": {
  "order": ["anthropic","openai"],
  "ignore": ["google"],
  "allow_fallbacks": true
}
```  

Dictates provider precedence, exclusion, and fallback logic. :contentReference[oaicite:7]{index=7}  

---

## Example Python 3.x  

```python
import os, requests, json

KEY = os.getenv("OPENROUTER_API_KEY")
url = "https://openrouter.ai/api/v1/chat/completions"
headers = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
payload = {
    "model": "mistralai/mistral-large",
    "messages": [{"role": "user", "content": "Summarize RFC 2616"}],
    "stream": False,
    "temperature": 0.4
}

resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
resp.raise_for_status()
print(resp.json()["choices"][0]["message"]["content"])
```  

---

## Minimal Model Listing in Code  

```python
import os, requests, pprint, json
url = "https://openrouter.ai/api/v1/models"
headers = {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"}
data = requests.get(url, headers=headers, timeout=30).json()
pprint.pp([m["id"] for m in data["data"]])
```  

---

## Reference Parameters Snapshot  
| Key | Default | Notes |
|-----|---------|-------|
| `temperature` | `1.0` | Lower = deterministic |  
| `top_p` | `1.0` | Nucleus sampling cutoff |  
| `max_tokens` | provider-specific | Hard cap per call |  
Further custom parameters pass-through to underlying providers when supported. :contentReference[oaicite:8]{index=8}  
