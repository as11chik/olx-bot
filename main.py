import requests, time, json, re
from bs4 import BeautifulSoup

TOKEN   = "8675707834:AAHB2VIOpYyvzn-yJhv3EtrNZ8Flu8UxYu0"
CHAT_ID = "1806974839"

SEARCH_QUERIES = {
    "iPhone (до 250к)":        "https://m.olx.kz/list/q-iphone/?search[filter_float_price:to]=250000&search[city_id]=87&search[order]=created_at:desc",
    "iPhone 13 (до 90к)":      "https://m.olx.kz/list/q-iphone-13/?search[filter_float_price:to]=90000&search[city_id]=87&search[order]=created_at:desc",
    "iPhone 13 Pro (до 120к)": "https://m.olx.kz/list/q-iphone-13-pro/?search[filter_float_price:to]=120000&search[city_id]=87&search[order]=created_at:desc",
    "iPhone 14 (до 90к)":      "https://m.olx.kz/list/q-iphone-14/?search[filter_float_price:to]=90000&search[city_id]=87&search[order]=created_at:desc",
    "iPhone 14 Pro (до 200к)": "https://m.olx.kz/list/q-iphone-14-pro/?search[filter_float_price:to]=200000&search[city_id]=87&search[order]=created_at:desc",
}

CHECK_INTERVAL = 15
SEEN_FILE = "seen_ads.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 12; Samsung SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
}

def fetch_ads(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        print(f"    HTTP {resp.status_code}")
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        ads = []
        seen_ids = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/d/obyavlenie/" in href or "/obyavlenie/" in href:
                m = re.search(r'(\d+)\.html', href)
                if not m:
                    continue
                ad_id = m.group(1)
                if ad_id in seen_ids:
                    continue
                seen_ids.add(ad_id)
                full_url = href if href.startswith("http") else "https://m.olx.kz" + href
                title = a.get_text(strip=True) or "-"
                ads.append({"id": ad_id, "title": title[:100], "url": full_url})
        return ads
    except Exception as e:
        print(f"    Ошибка: {e}")
        return []

def load_seen():
    try:
        with open(SEEN_FILE) as f: return set(json.load(f))
    except: return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f: json.dump(list(seen), f)

def send_telegram(text):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": False},
            timeout=10)
        return r.status_code == 200
    except: return False

def check_olx(seen):
    print(f"[{time.strftime('%H:%M:%S')}] Проверяю...")
    new_count = 0
    for name, url in SEARCH_QUERIES.items():
        print(f"  ▶ {name}")
        ads = fetch_ads(url)
        new_ads = [a for a in ads if a["id"] not in seen]
        print(f"    Найдено: {len(ads)}, новых: {len(new_ads)}")
        for ad in new_ads:
            seen.add(ad["id"])
            send_telegram(f"⚡️ <b>{name}</b>\n\n📌 {ad['title']}\n📍 Астана\n🔗 {ad['url']}")
            new_count += 1
            time.sleep(0.3)
        time.sleep(1)
    return new_count

seen = load_seen()
if not seen:
    print("Первый запуск — собираю базу...")
    for name, url in SEARCH_QUERIES.items():
        for a in fetch_ads(url): seen.add(a["id"])
        time.sleep(2)
    save_seen(seen)
    print(f"База: {len(seen)} объявлений")

send_telegram("✅ <b>OLX бот запущен (HTML)!</b>\n📍 Астана\n\n" + "\n".join(f"• {n}" for n in SEARCH_QUERIES))

while True:
    n = check_olx(seen)
    save_seen(seen)
    print(f"Новых: {n}. Жду {CHECK_INTERVAL} сек...")
    time.sleep(CHECK_INTERVAL)
