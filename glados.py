import os
import json
import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

# 2026 Updated domains and tokens
DOMAINS = ["https://glados.cloud", "https://glados.rocks", "https://glados.one"]
TOKEN = "glados.cloud"  # Key fix for 2026 API

def _safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return None

def try_checkin(base, cookie):
    headers = {
        "cookie": cookie,
        "referer": f"{base}/console/checkin",
        "origin": base,
        "user-agent": USER_AGENT,
        "content-type": "application/json;charset=UTF-8",
        "accept": "application/json, text/plain, */*"
    }
    
    payload = {"token": TOKEN}
    
    try:
        checkin = requests.post(f"{base}/api/user/checkin", headers=headers, json=payload, timeout=20)
        status = requests.get(f"{base}/api/user/status", headers={k:v for k,v in headers.items() if k != 'content-type'}, timeout=20)
        
        sj = _safe_json(status)
        if sj and "data" in sj:
            return sj["data"], checkin, status
        
        print(f"[{base}] failed: status_code={status.status_code} body={status.text[:100]}")
        return None, checkin, status
    except Exception as e:
        print(f"[{base}] error: {e}")
        return None, None, None

if __name__ == "__main__":
    cookies = os.environ.get("GLADOS_COOKIE", "").split("&")
    ptoken = os.environ.get("PUSHPLUS_TOKEN", "")

    if not cookies or not cookies[0].strip():
        print("未获取到 GLADOS_COOKIE")
        exit(0)

    results = []
    for cookie in cookies:
        cookie = cookie.strip()
        if not cookie: continue
        
        data = None
        for base in DOMAINS:
            data, ci, st = try_checkin(base, cookie)
            if data: break
            
        if data:
            email = data.get("email", "unknown")
            left = str(data.get("leftDays", "0")).split(".")[0]
            msg = _safe_json(ci).get("message", "No message") if ci else "Error"
            res_str = f"{email}----{msg}----剩余({left})天"
            print(res_str)
            results.append(res_str)
        else:
            print("所有域名尝试失败，请检查 Cookie 是否正确或被封禁")

    if ptoken and results:
        requests.get("http://www.pushplus.plus/send", params={
            "token": ptoken,
            "title": "GLaDOS 签到结果",
            "content": "\n".join(results)
        })
