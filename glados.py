import os
import json
import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def _safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return None


def _short(text: str, n: int = 240) -> str:
    text = text or ""
    text = text.replace("\n", " ")
    return text[:n]


def try_checkin(base: str, cookie: str):
    url_checkin = f"{base}/api/user/checkin"
    url_status = f"{base}/api/user/status"

    headers = {
        "cookie": cookie,
        "referer": f"{base}/console/checkin",
        "origin": base,
        "user-agent": USER_AGENT,
        "content-type": "application/json;charset=UTF-8",
    }

    payload = {"token": "glados.one"}

    checkin = requests.post(url_checkin, headers=headers, data=json.dumps(payload), timeout=20)
    status = requests.get(url_status, headers={k: v for k, v in headers.items() if k != "content-type"}, timeout=20)

    sj = _safe_json(status)
    if not sj or "data" not in sj:
        # Usually means cookie invalid / not logged in / blocked.
        print(f"[{base}] status: http={status.status_code} body={_short(status.text)}")
        print(f"[{base}] checkin: http={checkin.status_code} body={_short(checkin.text)}")
        return None, checkin, status

    return sj["data"], checkin, status


if __name__ == "__main__":
    pushplus_token = os.environ.get("PUSHPLUS_TOKEN", "")
    cookies = os.environ.get("GLADOS_COOKIE", "").split("&")

    if not cookies or cookies[0].strip() == "":
        print("未获取到COOKIE变量")
        raise SystemExit(0)

    bases = ["https://glados.rocks", "https://glados.one"]

    send_lines = []

    for cookie in cookies:
        cookie = cookie.strip()
        if not cookie:
            continue

        data = None
        checkin = None
        status = None
        for base in bases:
            data, checkin, status = try_checkin(base, cookie)
            if data is not None:
                break

        if data is None:
            print("cookie可能已失效/未登录/被拦截，请重新抓包更新 GLADOS_COOKIE")
            continue

        left_days = str(data.get("leftDays", ""))
        left_days = left_days.split(".")[0] if left_days else "?"
        email = data.get("email", "(unknown)")

        msg = _safe_json(checkin).get("message") if _safe_json(checkin) else None
        msg = msg or "(no message)"

        line = f"{email}----结果--{msg}----剩余({left_days})天"
        print(line)
        send_lines.append(line)

    # Optional PushPlus notification
    if pushplus_token and send_lines:
        content = "\n".join(send_lines)
        try:
            requests.get(
                "http://www.pushplus.plus/send",
                params={"token": pushplus_token, "title": "GLaDOS 签到", "content": content},
                timeout=20,
            )
        except Exception as e:
            print(f"PushPlus发送失败: {e}")
