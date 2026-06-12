import logging
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://auto.drom.ru/",
}

BASE_URL = "https://auto.drom.ru/?state=1"
OUTPUT_DIR = Path("data/car_clear_parsed")
START_PAGE = 1
END_PAGE = 300
DELAY_MIN = 0
DELAY_MAX = 1
BATCH_SIZE = 10
DOWNLOAD_WORKERS = 8
MIN_IMG_BYTES = 30_000

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
_log_file = LOG_DIR / f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(_log_file, encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


def get_url_photos_from_post(session, post_url):
    try:
        resp = session.get(post_url, timeout=15)
        resp.encoding = "windows-1251"
    except requests.RequestException:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    urls = []

    for img in soup.find_all("a"):
        src = (
            img.get("href")
            or ""
        )
        if "drom.ru/photo" in src and src.startswith("http"):
            urls.append(src)

    if not urls:
        for script in soup.find_all("script"):
            text = script.string or ""
            matches = re.findall(r'https://[^\s"\']+drom\.ru/photo[^\s"\']*gen1200\.jpg', text)
            urls.extend(matches)

    return urls[1:3]


def get_posts_from_page(session, n):
    url = f"{BASE_URL}&page={n}"
    # log.info("Страница %s: %s", n, url)

    try:
        resp = session.get(url, timeout=15)
        resp.encoding = "windows-1251"   # ← Drom использует cp1251!
    except requests.RequestException as e:
        log.warning("Ошибка запроса страницы %s: %s", n, e)
        raise e

    soup = BeautifulSoup(resp.text, "html.parser")
    links = soup.find_all("a", href=True)
    page_listings = [
        a["href"] for a in links
        if a["href"].startswith("https://auto.drom.ru/")
        and a["href"].endswith(".html")
        and "/dealers/" not in a["href"]
    ]

    page_listings = list(set(page_listings))
    if not page_listings:
        log.info("Страница %s пустая, стоп.", n)
        raise requests.RequestException(f"Страница {n} пустая, стоп.")

    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    return page_listings


def save_picture(session, pic_url, save_path):
    try:
        resp = session.get(pic_url, timeout=15, stream=True)
        ct = resp.headers.get("Content-Type", "")
        if resp.status_code == 200 and "image" in ct:
            data = b"".join(resp.iter_content(8192))
            if len(data) < MIN_IMG_BYTES:
                log.debug("Слишком мало байт (%s) — пропуск %s", len(data), pic_url)
                return False
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(data)
            log.debug("OK %s KB %s", len(data)//1024, pic_url)
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            return True
        else:
            log.debug("Пропуск %s: status=%s", pic_url, resp.status_code)
    except requests.exceptions.SSLError as e:
        log.debug("Ошибка %s: %s", pic_url, e)
    return False


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    session = requests.Session()
    session.headers.update(HEADERS)

    for batch_i in range(22, END_PAGE // BATCH_SIZE):
        log.info("batch %s is loading", batch_i)

        posts_urls = []
        for i in range( batch_i * BATCH_SIZE, (batch_i+1) * BATCH_SIZE):
            posts_urls.extend(get_posts_from_page(session, i))
        log.info("totally scraped %s posts in batch %s", len(posts_urls), batch_i)

        images_urls = []
        n_posts = len(posts_urls)
        for post_i, post in enumerate(posts_urls, 1):
            found = get_url_photos_from_post(session, post)
            images_urls.extend(found)
            log.info("  post %s/%s batch %s — found %s photos | %s", post_i, n_posts, batch_i, len(found), post)
        log.info("got %s urls on photos total in batch %s", len(images_urls), batch_i)

        count_success_url = 0
        n_imgs = len(images_urls)

        with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as ex:
            futures = {
                ex.submit(save_picture, session, img_url, OUTPUT_DIR / f"{img_url.split('/')[-2][-15:]}.jpg"): img_url
                for img_url in images_urls
            }
            for future in as_completed(futures):
                if future.result():
                    count_success_url += 1
                log.info("  pics %s/%s downloaded so far in batch %s", count_success_url, n_imgs, batch_i)

        log.info("%s out of %s pictures downloaded in batch %s", count_success_url, n_imgs, batch_i)



if __name__ == "__main__":
    main()
