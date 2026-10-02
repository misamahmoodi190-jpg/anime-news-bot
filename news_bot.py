import os
import json
import time
import html
import hashlib
import requests
import feedparser
from datetime import datetime, timezone
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BALE_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("BALE_CHANNEL_ID", "")
BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}/"
DATA_FILE = "posted_news.json"
MAX_POSTS_PER_RUN = 3
MAX_HISTORY = 500
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

CHANNEL_SIGNATURE = "[◦•●◉✿   چنل اتاکو °•|•° otako chanel ✿◉●•◦](https://ble.ir/join/HtzJvEic6p)"

# منابع RSS فعال و معتبر برای انیمه، مانگا و مانهوا
RSS_FEEDS = {
    "Anime News Network": {
        "url": "https://www.animenewsnetwork.com/news/rss.xml",
        "emoji": "🎌",
        "category": "anime",
    },
    "MyAnimeList News": {
        "url": "https://myanimelist.net/rss/news.xml",
        "emoji": "📚",
        "category": "anime",
    },
    "Anime Corner": {
        "url": "https://animecorner.me/feed/",
        "emoji": "✨",
        "category": "anime",
    },
    "Otaku USA Magazine": {
        "url": "https://otakuusamagazine.com/feed/",
        "emoji": "📖",
        "category": "manga",
    },
}

# کلمات کلیدی برای فیلتر کردن اخبار نامرتبط (مانند گیمینگ و لایو اکشن‌های نامربوط)
FILTER_KEYWORDS = [
    "video game", "gameplay", "playstation", "ps4", "ps5",
    "xbox", "nintendo switch", "steam deck", "live-action film",
    "k-drama", "j-drama"
]

RELEVANT_KEYWORDS = [
    "anime", "manga", "manhwa", "manhua",
    "otaku", "japan animation", "japanese",
    "chapter", "volume", "season", "episode",
    "studio", "mangaka", "artist", "author",
    "voice actor", "seiyuu", "trailer", "visual",
    "teaser", "premiere", "broadcast", "adaptation"
]


def load_posted_ids():
    """بارگذاری شناسه‌های اخبار ارسال شده قبلی با حفظ ترتیب زمانی"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
    except Exception as e:
        print(f"خطا در خواندن فایل تاریخچه: {e}")
    return []


def save_posted_ids(posted_list):
    """ذخیره شناسه‌های اخبار با محدود کردن به سقف MAX_HISTORY و حفظ ترتیب"""
    try:
        # حذف تکراری‌ها با حفظ ترتیب
        seen = set()
        unique_list = []
        for item_id in posted_list:
            if item_id not in seen:
                seen.add(item_id)
                unique_list.append(item_id)

        trimmed_list = unique_list[-MAX_HISTORY:]
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(trimmed_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"خطا در ذخیره فایل تاریخچه: {e}")


def make_id(url, title=""):
    """تولید هش یکتا بر اساس لینک یا عنوان"""
    raw = url or title
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def is_relevant(title, summary=""):
    """بررسی هوشمند مرتبط بودن خبر با انیمه/مانگا/مانهوا"""
    text = (title + " " + summary).lower()

    # بررسی کلمات نامرتبط
    for keyword in FILTER_KEYWORDS:
        if keyword in text:
            # اگر همزمان کلمات کاملاً مرتبط انیمه‌ای دارد، تایید کن
            if any(rel in text for rel in ["anime", "manga", "manhwa", "adaptation"]):
                return True
            return False

    return True


def translate_to_persian(text):
    """ترجمه متن به فارسی با پشتیبانی از کش و تمیزکاری موجودیت‌های HTML"""
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
                # پاکسازی موجودیت‌های HTML از خروجی ترجمه
                return html.unescape(translated).strip()
        return text
    except Exception as e:
        print(f"خطا در ترجمه: {e}")
        return text


def get_category_label(category):
    labels = {"anime": "🎌 انیمه", "manhwa": "📖 مانهوا", "manga": "📚 مانگا"}
    return labels.get(category, "📰 خبر")


def get_hashtag(category):
    hashtags = {"anime": "#انیمه", "manhwa": "#مانهوا", "manga": "#مانگا"}
    return hashtags.get(category, "#انیمه")


def fetch_rss_news():
    """دریافت اخبار از فیدهای RSS بدون ترجمه زودهنگام برای حفظ سهمیه API"""
    all_news = []
    headers = {"User-Agent": DEFAULT_USER_AGENT}

    for source_name, config in RSS_FEEDS.items():
        try:
            print(f"دریافت از: {source_name}...")
            res = requests.get(config["url"], headers=headers, timeout=15)
            if res.status_code != 200:
                print(f"خطای HTTP {res.status_code} در دریافت {source_name}")
                continue

            feed = feedparser.parse(res.content)
            for entry in feed.entries[:20]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                summary_raw = entry.get("summary", entry.get("description", ""))
                summary = BeautifulSoup(summary_raw, "html.parser").get_text()
                summary = summary.strip()[:300]

                # فیلتر کردن اخبار نامرتبط
                if not is_relevant(title, summary):
                    continue

                image_url = ""
                # بررسی تصاویر موجود در تگ‌های مختلف مدیا
                if hasattr(entry, "media_content") and entry.media_content:
                    for media in entry.media_content:
                        if "image" in media.get("type", "") or media.get("medium") == "image":
                            image_url = media.get("url", "")
                            if image_url:
                                break
                if not image_url and hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                    for thumb in entry.media_thumbnail:
                        image_url = thumb.get("url", "")
                        if image_url:
                            break
                if not image_url and hasattr(entry, "links"):
                    for lk in entry.links:
                        if "image" in lk.get("type", ""):
                            image_url = lk.get("href", "")
                            if image_url:
                                break

                if title:
                    all_news.append({
                        "id": make_id(link, title),
                        "title_en": title,
                        "summary_en": summary,
                        "source": source_name,
                        "emoji": config["emoji"],
                        "category": config["category"],
                        "image": image_url,
                    })
        except Exception as e:
            print(f"خطا در دریافت {source_name}: {e}")
    return all_news


def fetch_manhwa_updates():
    """دریافت به‌روزرسانی‌های مانهوا از MangaDex"""
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

                # استخراج عنوان با پشتیبانی از نویسه‌گردانی کره‌ای (ko-ro) و زبان‌های دیگر
                title = (
                    title_data.get("en")
                    or title_data.get("ko-ro")
                    or title_data.get("ko")
                    or title_data.get("ja")
                    or (next(iter(title_data.values())) if title_data else "")
                )

                cover_filename = ""
                for rel in manga.get("relationships", []):
                    if rel.get("type") == "cover_art":
                        cover_filename = rel.get("attributes", {}).get("fileName", "")
                        break

                image_url = ""
                if cover_filename and manga_id:
                    image_url = f"https://uploads.mangadex.org/covers/{manga_id}/{cover_filename}.256.jpg"

                description_data = attrs.get("description", {})
                description = description_data.get("en") or (next(iter(description_data.values())) if description_data else "")
                if description:
                    description = BeautifulSoup(description, "html.parser").get_text().strip()[:200]

                if title:
                    manhwa_list.append({
                        "id": make_id(f"https://mangadex.org/title/{manga_id}", title),
                        "title_en": title,
                        "summary_en": description,
                        "source": "MangaDex",
                        "emoji": "📖",
                        "category": "manhwa",
                        "image": image_url,
                    })
    except Exception as e:
        print(f"خطا در دریافت مانهوا: {e}")
    return manhwa_list


def format_message(item):
    """فرمت‌دهی پیام ارسالی با ایمن‌سازی کاراکترهای HTML"""
    emoji = item.get("emoji", "📰")
    category_label = get_category_label(item["category"])
    hashtag = get_hashtag(item["category"])

    # گریز دادن کاراکترهای خاص HTML برای جلوگیری از خطای parse_mode در پیام‌رسان
    title = html.escape(item.get("title", "").strip())
    summary = html.escape(item.get("summary", "").strip())
    source = html.escape(item.get("source", "").strip())

    lines = [f"{emoji} <b>{title}</b>", ""]
    if summary:
        lines.append(summary)
        lines.append("")
    lines.append(f"📂 {category_label}")
    lines.append(f"📌 منبع: {source}")
    lines.append("")
    lines.append(hashtag)
    lines.append("")
    lines.append(CHANNEL_SIGNATURE)
    return "\n".join(lines)


def send_text(text):
    """ارسال پیام متنی به کانال بله"""
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
            print(f"خطا در ارسال sendMessage: {result}")
            return False
    except Exception as e:
        print(f"خطای شبکه در send_text: {e}")
        return False


def send_photo_with_caption(image_url, caption):
    """ارسال تصویر به همراه کپشن به کانال بله، با fallback به متن ساده در صورت شکست"""
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
            print(f"خطا در sendPhoto: {result} - تلاش مجدد با ارسال متن...")
            return send_text(caption)
    except Exception as e:
        print(f"خطا در ارسال تصویر: {e} - ارسال متن ساده...")
        return send_text(caption)


def post_to_channel(item):
    """ارسال پست به کانال (تصویردار یا متنی)"""
    text = format_message(item)
    if item.get("image"):
        return send_photo_with_caption(item["image"], text)
    else:
        return send_text(text)


def main():
    print("=" * 50)
    print("شروع اجرای Anime News Bot")
    print("=" * 50)

    if not BOT_TOKEN or not CHANNEL_ID:
        print("خطا: متغیرهای BALE_BOT_TOKEN و BALE_CHANNEL_ID تنظیم نشده‌اند!")
        return

    posted_ids = load_posted_ids()
    posted_set = set(posted_ids)
    print(f"تعداد رکوردهای تاریخچه قبلی: {len(posted_ids)}")

    rss_news = fetch_rss_news()
    manhwa_updates = fetch_manhwa_updates()
    all_items = rss_news + manhwa_updates
    print(f"مجموع اخبار و آپدیت‌های دریافت شده: {len(all_items)}")

    # فیلتر کردن آیتم‌های واقعاً جدید
    new_items = [item for item in all_items if item["id"] not in posted_set]
    print(f"تعداد اخبار جدید ارسال نشده: {len(new_items)}")

    posted_count = 0
    # فقط به تعداد مجاز در هر اجرا پردازش و ترجمه انجام می‌شود (Lazy Translation)
    for item in new_items[:MAX_POSTS_PER_RUN]:
        print(f"\nآماده‌سازی و ترجمه: {item['title_en'][:60]}...")

        title_fa = translate_to_persian(item["title_en"])
        summary_fa = translate_to_persian(item["summary_en"]) if item.get("summary_en") else ""
        time.sleep(0.5)

        item["title"] = title_fa
        item["summary"] = summary_fa

        print(f"ارسال به کانال: {item['title'][:60]}...")
        success = post_to_channel(item)
        if success:
            posted_ids.append(item["id"])
            posted_set.add(item["id"])
            posted_count += 1
            print("✓ ارسال موفق!")
            time.sleep(3)
        else:
            print("✗ ارسال ناموفق!")
        time.sleep(1)

    save_posted_ids(posted_ids)
    print("=" * 50)
    print(f"پایان اجرا - {posted_count} خبر با موفقیت ارسال شد.")
    print("=" * 50)


if __name__ == "__main__":
    main()
