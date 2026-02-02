# White_label_AI_Build

## About
Yep — I can help 👍  
I can’t *execute* that cURL from here, but I can absolutely help you **set it up correctly**, fix a couple issues, and show how to use it in cURL, JS, or Python.

You’re very close already — there are just a few syntax + naming problems.

---

### 1. Cleaned-up & Correct cURL
Here’s a **properly formatted** version using your required headers and the `whereUsed` URL you specified:

```bash
curl --request GET \
  --url "https://dpservice-prod-aws.fmr.com/ftgw/dp/content-headless/v2/content?path=%2F600%20Fidelity.Com%2F..." \
  --header "AppId: AP156970" \
  --header "AppName: XYZ" \
  --header "sregid: 1111" \
  --header "whereUsed: https://www.fidelity.com/viewpoints/personal-finance/how-to-start-investing"
```

#### Key fixes vs your original
* ❌ `Appld` → ✅ `AppId`
* ❌ stray pipes (`|`) → removed
* ❌ malformed quotes → fixed
* ❌ multiple `whereUsed` values → single correct URL
* Headers must be **separate `--header` flags**

---

### 2. About the `path` Query Param
Your query param:

```
path=%2F600%20Fidelity.Com%2...
```

That’s **URL-encoded**, which is correct.

If you ever need to encode it yourself:

```js
encodeURIComponent("/600 Fidelity.Com/whatever")
```

Just make sure the backend expects:
* leading `/`
* exact case
* correct spacing

---

### 3. JavaScript (fetch) Example
If you’re wiring this into a Node or frontend service:

```js
const url = new URL(
  "https://dpservice-prod-aws.fmr.com/ftgw/dp/content-headless/v2/content"
);

url.searchParams.set(
  "path",
  "/600 Fidelity.Com/..."
);

const res = await fetch(url.toString(), {
  method: "GET",
  headers: {
    "AppId": "AP156970",
    "AppName": "XYZ",
    "sregid": "1111",
    "whereUsed": "https://www.fidelity.com/viewpoints/personal-finance/how-to-start-investing"
  }
});

const data = await res.json();
console.log(data);
```

⚠️ If this is browser-side, you may hit **CORS** — this usually needs to run server-side.

---

### 4. Python (requests) Example
```python
import requests

url = "https://dpservice-prod-aws.fmr.com/ftgw/dp/content-headless/v2/content"

params = {
    "path": "/600 Fidelity.Com/..."
}

headers = {
    "AppId": "AP156970",
    "AppName": "XYZ",
    "sregid": "1111",
    "whereUsed": "https://www.fidelity.com/viewpoints/personal-finance/how-to-start-investing"
}

response = requests.get(url, params=params, headers=headers)
response.raise_for_status()

print(response.json())
```

---

### 5. Common Gotchas (Very Likely at Fidelity)
* Headers are **case-sensitive** in some gateways
* `whereUsed` is often logged for **content entitlement + audit**
* Missing or mismatched `AppId` usually returns:
  * 401
  * 403
  * or empty payload
* Some endpoints require **VPN / internal network**
* Some require **mutual TLS (mTLS)** — if you get connection resets, that’s likely why

---

### 6. Quick Debug Checklist
If it fails:
1. Try without `whereUsed` → see if error changes
2. Confirm `AppId` is **approved for this endpoint**
3. Verify the **exact path value** expected
4. Check if this must be called **from a Fidelity network**

---

If you want, next we can:
* 🔍 Inspect a sample response and map the schema
* 🧱 Wrap this in a reusable service / proxy
* 🔐 Diagnose auth vs entitlement errors
* ⚙️ Turn this into a LangChain / RAG content loader

Just tell me what you’re plugging this into.
