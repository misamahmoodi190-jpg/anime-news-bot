import os
import json
import time
import hashlib
import requests
import feedparser
from datetime import datetime, timezone
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BALE_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("BALE_CHANNEL_ID", "")
BASE_URL = "https://tapi.bale.ai/bot" + BOT_TOKEN + "/"
DATA_FILE = "posted_news.json"
MAX_POSTS_PER_RUN = 3
MAX_HISTORY = 500

CHANNEL_SIGNATURE = "[◦•●◉✿   چنل اتاکو °•|•° otako chanel ✿◉●•◦](https://ble.ir/join/HtzJvEic6p)"

RSS_FEEDS = {
    "Anime News Network": {
        "url": "https://www.animenewsnetwork.com/news/rss.xml",
        "emoji": "🎌",
        "category": "anime"
    },
    "ANN Manga News": {
        "url": "https://www.animenewsnetwork.com/news/manga/rss.xml",
        "emoji": "📚",
        "category": "manga"
    },
    "MyAnimeList News": {
        "url": "https://myanimelist.net/rss/news.xml",
        "emoji": "⭐",
        "category": "anime"
    },
}


def load_posted_ids():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data) if isinstance(data, list) else set()
    except Exception as e:
        print("خطا در خواندن فایل: " + str(e))
    return set()


def save_posted_ids(posted_set):
    posted_list = list(posted_set)[-MAX_HISTORY:]
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(posted_list, f, ensure_ascii=False, indent=2)


def make_id(url, title=""):
    raw = url or title
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def translate_to_persian(text):
    if not text or len(text.strip()) < 3:
        return text
    try:
        if len(text) > 450:
            text = text[:450] + "..."
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text, "langpair": "en|fa", "de": "animebot@example.com"}
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            translated = data.get("responseData", {}).get("translatedText", "")
            if translated and translated.lower() != text.lower():
                return translated
        return text
    except Exception as e:
        print("خطا در ترجمه: " + str(e))
        return text


def get_category_label(category):
    labels = {"anime": "🎌 انیمه", "manhwa": "📖 مانهوا", "manga": "📚 مانگا"}
    return labels.get(category, "📰 خبر")


def get_hashtag(category):
    hashtags = {"anime": "#انیمه", "manhwa": "#مانهوا", "manga": "#مانگا"}
    return hashtags.get(category, "#انیمه")


def fetch_rss_news():
    all_news = []
    for source_name, config in RSS_FEEDS.items():
        try:
            print("دریافت از: " + source_name + "...")
            feed = feedparser.parse(config["url"])
            for entry in feed.entries[:15]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                summary_raw = entry.get("summary", entry.get("description", ""))
                summary = BeautifulSoup(summary_raw, "html.parser").get_text()
                summary = summary.strip()[:300]
                title_fa = translate_to_persian(title)
                summary_fa = translate_to_persian(summary) if summary else ""
                image_url = ""
                if hasattr(entry, "media_content"):
                    for media in entry.media_content:
                        if "image" in media.get("type", ""):
                            image_url = media["url"]
                            break
                if not image_url and hasattr(entry, "media_thumbnail"):
                    for thumb in entry.media_thumbnail:
                        image_url = thumb.get("url", "")
                        break
                if title:
                    all_news.append({
                        "id": make_id(link, title),
                        "title": title_fa,
                        "summary": summary_fa,
                        "source": source_name,
                        "emoji": config["emoji"],
                        "category": config["category"],
                        "image": image_url,
                    })
                time.sleep(0.5)
        except Exception as e:
            print("خطا در دریافت " + source_name + ": " + str(e))
    return all_news


def fetch_manhwa_updates():
    manhwa_list = []
    try:
        print("دریافت مانهوا از MangaDex...")
        url = "https://api.mangadex.org/manga"
        params = {
            "order[latestUploadedChapter]": "desc",
            "limit": 10,
            "includes[]": ["cover_art"],
            "originalLanguage[]": ["ko"],
            "contentRating[]": ["safe", "suggestive"],
        }
        headers = {"User-Agent": "BaleAnimeBot/1.0"}
        res = requests.get(url, params=params, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json().get("data", [])
            for manga in data:
                attrs = manga.get("attributes", {})
                manga_id = manga.get("id", "")
                title_data = attrs.get("title", {})
                title = title_data.get("en") or title_data.get("ko") or title_data.get("ja", "")
                cover_filename = ""
                for rel in manga.get("relationships", []):
                    if rel.get("type") == "cover_art":
                        cover_filename = rel.get("attributes", {}).get("fileName", "")
                        break
                image_url = ""
                if cover_filename and manga_id:
                    image_url = "https://uploads.mangadex.org/covers/" + manga_id + "/" + cover_filename + ".256.jpg"
                description = attrs.get("description", {}).get("en", "")
                if description:
                    description = description[:200]
                title_fa = translate_to_persian(title) if title else ""
                summary_fa = translate_to_persian(description) if description else ""
                time.sleep(0.5)
                if title:
                    manhwa_list.append({
                        "id": make_id("https://mangadex.org/title/" + manga_id, title),
                        "title": title_fa,
                        "summary": summary_fa,
                        "source": "MangaDex",
                        "emoji": "📖",
                        "category": "manhwa",
                        "image": image_url,
                    })
    except Exception as e:
        print("خطا در دریافت مانهوا: " + str(e))
    return manhwa_list


def format_message(item):
    emoji = item.get("emoji", "📰")
    category_label = get_category_label(item["category"])
    hashtag = get_hashtag(item["category"])
    lines = [emoji + " <b>" + item["title"] + "</b>", ""]
    if item.get("summary"):
        lines.append(item["summary"])
        lines.append("")
    lines.append("📂 " + category_label)
    lines.append("📌 منبع: " + item["source"])
    lines.append("")
    lines.append(hashtag)
    lines.append("")
    lines.append(CHANNEL_SIGNATURE)
    return "\n".join(lines)


def send_text(text):
    url = BASE_URL + "sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        res = requests.post(url, json=payload, timeout=30)
        result = res.json()
        if result.get("ok"):
            return True
        else:
            print("خطا در ارسال: " + str(result))
            return False
    except Exception as e:
        print("خطای شبکه: " + str(e))
        return False


def send_photo_with_caption(image_url, caption):
    url = BASE_URL + "sendPhoto"
    payload = {
        "chat_id": CHANNEL_ID,
        "photo": image_url,
        "caption": caption,
        "parse_mode": "HTML",
    }
    try:
        res = requests.post(url, json=payload, timeout=30)
        result = res.json()
        if result.get("ok"):
            return True
        else:
            return send_text(caption)
    except Exception as e:
        print("خطا: " + str(e))
        return send_text(caption)


def post_to_channel(item):
    text = format_message(item)
    if item.get("image"):
        return send_photo_with_caption(item["image"], text)
    else:
        return send_text(text)


def main():
    print("=" * 50)
    print("شروع اجرا")
    print("=" * 50)
    if not BOT_TOKEN or not CHANNEL_ID:
        print("لطفاً متغیرهای BALE_BOT_TOKEN و BALE_CHANNEL_ID را تنظیم کنید!")
        return
    posted_ids = load_posted_ids()
    print("تعداد اخبار قبلی: " + str(len(posted_ids)))
    rss_news = fetch_rss_news()
    manhwa_updates = fetch_manhwa_updates()
    all_items = rss_news + manhwa_updates
    print("مجموع اخبار دریافتی: " + str(len(all_items)))
    new_items = [item for item in all_items if item["id"] not in posted_ids]
    print("اخبار جدید: " + str(len(new_items)))
    posted_count = 0
    for item in new_items[:MAX_POSTS_PER_RUN]:
        print("ارسال: " + item["title"][:60] + "...")
        success = post_to_channel(item)
        if success:
            posted_ids.add(item["id"])
            posted_count += 1
            print("ارسال موفق!")
            time.sleep(3)
        else:
            print("ارسال ناموفق!")
        time.sleep(1)
    save_posted_ids(posted_ids)
    print("=" * 50)
    print("پایان اجرا - " + str(posted_count) + " خبر ارسال شد")
    print("=" * 50)


if __name__ == "__main__":
    main()
