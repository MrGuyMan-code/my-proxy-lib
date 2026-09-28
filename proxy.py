from playwright.sync_api import sync_playwright
from pathlib import Path
import random
import requests

link = "https://proxyscrape.com/free-proxy-list"
LIB_DIR = Path(__file__).resolve().parent
LIST_FILE = LIB_DIR / "free-proxy-list.txt"

class Proxy_class():
    current_proxy = None
    proxy_list = None

    def __init__(self):
        Proxy_class.load_proxy_list()

    @staticmethod
    def refresh_proxy_list(silent = False):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(accept_downloads=True)

            # BLOCHEAZĂ toate overlay-urile de la sursă
            for pattern in [
                "**/*cookiebot*",
                "**/consent.cookiebot.com/**",
                "**/*intercom*",
                "**/widget.intercom.io/**",
                "**/js.intercomcdn.com/**",
                "**/static.intercomassets.com/**",
            ]:
                context.route(pattern, lambda r: r.abort())

            page = context.new_page()
            page.goto(link, wait_until="networkidle")

            # Ascunde top-bar sticky (singurul care nu vine din script extern)
            page.add_style_tag(content="""
                [data-section="top-bar"] { position: static !important; }
            """)

            # Click direct pe Download — nimic nu-l mai blochează
            buton = page.get_by_role("button", name="Download", exact=True)
            buton.scroll_into_view_if_needed()

            with page.expect_download(timeout=60_000) as dl:
                buton.click()

            dl.value.save_as(str(LIST_FILE))
            if not silent:
                print("Salvat:", LIST_FILE)

            browser.close()

    @staticmethod
    def load_proxy_list(silent = False):
        try:
            with open(LIST_FILE, 'r') as f:
                Proxy_class.proxy_list = [line.rstrip('\n') for line in f]
        except:
            if not silent:
                print("No proxi file found OR file unable to open!!!")
    
    @staticmethod
    def get_random_proxy(timeout = 5, silent = False):
        index = random.randrange(0, len(Proxy_class.proxy_list))

        Proxy_class.current_proxy = Proxy_class.proxy_list[index]

        if Proxy_class._check_proxy(Proxy_class.current_proxy, timeout = timeout, silent=silent) is True:
            return Proxy_class.current_proxy
        
        return None

    @staticmethod
    def get_working_proxy(timeout = 5, max_counter = 30, silent = False):
        proxy = None
        counter = 0
        while not proxy and counter < max_counter:
            proxy = Proxy_class.get_random_proxy(timeout = timeout, silent=silent)
            counter += 1
        
        if not proxy:
            if not silent:
                print("No proxy found and limit reached")
        
        return proxy

    @staticmethod
    def _check_proxy(proxy, timeout=5, silent = False):
        proxies = {"http": proxy, "https": proxy}
        try:
            r = requests.get("https://api.ipify.org",
                            proxies=proxies,
                            timeout=(3, timeout))
            if r.ok:
                if not silent:
                    print(f"✅ {proxy} -> {r.text}")
                return True
            else:
                if not silent:
                    print(f"⚠️ {proxy} -> status {r.status_code}")
                return False
        except Exception as e:
            if not silent:
                print(f"❌ {proxy} -> {type(e).__name__}: {e}")
            return False

    @staticmethod
    def print_first5():
        for i in range(5):
            print(Proxy_class.proxy_list[i])

