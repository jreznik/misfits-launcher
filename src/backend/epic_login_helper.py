import webview
import time
import json
import sys
import requests
import re

def check_url(window):
    print("DEBUG: Monitor started")
    sys.stdout.flush()
    
    captured_sid = False
    
    while not captured_sid:
        try:
            url = window.get_current_url()
            if url and "api/redirect" in url:
                print(f"DEBUG: Detected redirect URL: {url}")
                sys.stdout.flush()
                
                # Wait a bit for cookies to be fully set
                time.sleep(2)
                
                try:
                    wv_cookies = window.get_cookies()
                    cookie_dict = {}
                    if wv_cookies:
                        for c in wv_cookies:
                            name = getattr(c, 'name', None) or (c.get('name') if isinstance(c, dict) else None)
                            value = getattr(c, 'value', None) or (c.get('value') if isinstance(c, dict) else None)
                            if name:
                                cookie_dict[name] = value
                    
                    print(f"DEBUG: Captured {len(cookie_dict)} cookies.")
                    sys.stdout.flush()
                    
                    if cookie_dict:
                        headers = {
                            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                            "Accept": "application/json, text/plain, */*"
                        }
                        resp = requests.get(url, cookies=cookie_dict, headers=headers)
                        print(f"DEBUG: Fetch status: {resp.status_code}")
                        sys.stdout.flush()
                        
                        if resp.status_code == 200:
                            try:
                                # Look for SID directly in the text first
                                match = re.search(r'"sid"\s*:\s*"([^"]+)"', resp.text)
                                if match:
                                    sid = match.group(1)
                                    print(f"SID:{sid}")
                                    sys.stdout.flush()
                                    captured_sid = True
                                    window.destroy()
                                    return
                                    
                                data = resp.json()
                                sid = data.get("sid")
                                if sid:
                                    print(f"SID:{sid}")
                                    sys.stdout.flush()
                                    captured_sid = True
                                    window.destroy()
                                    return
                            except Exception:
                                pass
                except Exception as e:
                    print(f"DEBUG: Extraction error: {e}")
                    sys.stdout.flush()
                    
        except Exception as e:
            print(f"DEBUG: Loop error: {e}")
            sys.stdout.flush()
            
        time.sleep(1.0)

def main():
    login_url = "https://www.epicgames.com/id/login?redirectUrl=https://www.epicgames.com/id/api/redirect"
    window = webview.create_window("Epic Games Login", login_url, width=500, height=700)
    webview.start(check_url, window)

if __name__ == "__main__":
    main()
