#!/usr/bin/env python3
"""
🤖 بات خبری انیمه و مانهوا - مخصوص پیام‌رسان بله
هر بار اجرا، اخبار جدید را از منابع مختلف جمع‌آوری و در کانال منتشر می‌کند.
"""

import os
import json
import time
import hashlib
import requests
import feedparser
from datetime import datetime, timezone
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# ⚙️ تنظیمات (از Environment Variables خوانده می‌شود)
# ─────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BALE_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("BALE_CHANNEL_ID", "")  # مثال: @my_anime_channel
BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}/"
DATA_FILE = "posted_news.json"
MAX_POSTS_PER_RUN = 3  # حداکثر تعداد پست در هر اجرا
MAX_HISTORY = 500      # حداکثر تعداد آیتم ذخیره‌شده برای جلوگیری از تکرار

# ─────────────────────────────────────────────
# 📡 منابع خبری (RSS Feeds)
# ─────────────────────────────────────────────
RSS_FEEDS = {
    "Anime News Network": {
        "url": "https://www.animenewsnetwork.com/news/rss.xml",
        "emoji": "🎌",
        "category": "anime"
    },
    "MyAnimeList News": {
        "url": "https://myanimelist.net/rss/news.xml",
        "emoji": "⭐",
        "category": "anime"
    },
}

# ─────────────────────────────────────────────
# 📦 توابع مدیریت داده (جلوگیری از تکرار)
# ─────────────────────────────────────────────
def load_posted_ids():
    """بارگذاری لیست اخبار قبلاً منتشر شده"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data) if isinstance(data, list) else set()
    except Exception as e:
        print(f"⚠️ خطا در خواندن فایل داده: {e}")
    return set()


def save_posted_ids(posted_set):
    """ذخیره لیست اخبار منتشر شده"""
    # فقط آخرین N مورد را نگه می‌داریم تا فایل بزرگ نشود
    posted_list = list(posted_set)[-MAX_HISTORY:]
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(posted_list, f, ensure_ascii=False, indent=2)


def make_id(url, title=""):
    """ساخت شناسه یکتا برای هر خبر"""
    raw = url or title
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


# ─────────────────────────────────────────────
# 🌐 دریافت اخبار از RSS
# ─────────────────────────────────────────────
def fetch_rss_news():
    """دریافت اخبار از تمام فیدهای RSS"""
    all_news = []

    for source_name, config in RSS_FEEDS.items():
        try:
            print(f"📡 دریافت از: {source_name}...")
            feed = feedparser.parse(config["url"])

            for entry in feed.entries[:15]:  # ۱۵ خبر آخر از هر منبع
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                summary_raw = entry.get("summary", entry.get("description", ""))
                published = entry.get("published", "")

                # تمیز کردن خلاصه (حذف تگ‌های HTML)
                summary = BeautifulSoup(summary_raw, "html.parser").get_text()
                summary = summary.strip()[:300]  # حداکثر ۳۰۰ کاراکتر

                # استخراج تصویر از فید
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

                if title and link:
                    all_news.append({
                        "id": make_id(link, title),
                        "title": title,
                        "link": link,
                        "summary": summary,
                        "source": source_name,
                        "emoji": config["emoji"],
                        "category": config["category"],
                        "image": image_url,
                        "published": published,
                    })

        except Exception as e:
            print(f"❌ خطا در دریافت {source_name}: {e}")

    return all_news


# ─────────────────────────────────────────────
# 📚 دریافت مانهواهای پرطرفدار (MangaDex API)
# ─────────────────────────────────────────────
def fetch_manhwa_updates():
    """دریافت آخرین آپدیت‌های مانهوا از MangaDex"""
    manhwa_list = []
    try:
        print("📡 دریافت مانهوا از MangaDex...")
        url = "https://api.mangadex.org/manga"
        params = {
            "order[latestUploadedChapter]": "desc",
            "limit": 10,
            "includes[]": ["cover_art"],
            "originalLanguage[]": ["ko"],  # فقط مانهواهای کره‌ای
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

                # استخراج تصویر جلد
                cover_filename = ""
                for rel in manga.get("relationships", []):
                    if rel.get("type") == "cover_art":
                        cover_attrs = rel.get("attributes", {})
                        cover_filename = cover_attrs.get("fileName", "")
                        break

                image_url = ""
                if cover_filename and manga_id:
                    image_url = f"https://uploads.mangadex.org/covers/{manga_id}/{cover_filename}.256.jpg"

                description = attrs.get("description", {}).get("en", "")
                if description:
                    description = description[:200]

                manga_link = f"https://mangadex.org/title/{manga_id}"

                if title:
                    manhwa_list.append({
                        "id": make_id(manga_link, title),
                        "title": title,
                        "link": manga_link,
                        "summary": description,
                        "source": "MangaDex",
                        "emoji": "📖",
                        "category": "manhwa",
                        "image": image_url,
                        "published": "",
                    })

    except Exception as e:
        print(f"❌ خطا در دریافت مانهوا: {e}")

    return manhwa_list


# ─────────────────────────────────────────────
# 🎨 قالب‌بندی پیام
# ─────────────────────────────────────────────
def format_news_message(item):
    """قالب‌بندی زیبای پیام برای ارسال به کانال"""
    emoji = item.get("emoji", "📰")
    category_label = "🎌 انیمه" if item["category"] == "anime" else "📖 مانهوا"

    lines = [
        f"{emoji} <b>{item['title']}</b>",
        "",
    ]

    if item.get("summary"):
        lines.append(f"{item['summary']}")
        lines.append("")

    lines.append(f"📂 {category_label}")
    lines.append(f"📌 منبع: {item['source']}")

    if item.get("link"):
        lines.append(f"🔗 <a href=\"{item['link']}\">ادامه مطلب</a>")

    lines.append("")
    lines.append("➖➖➖➖➖➖➖➖➖")
    lines.append("🤖 بات خبری انیمه و مانهوا")

    return "\n".join(lines)


def format_manhwa_message(item):
    """قالب‌بندی پیام مخصوص مانهوا"""
    lines = [
        "📖 <b>مانهوا آپدیت شد!</b>",
        "",
        f"📌 <b>{item['title']}</b>",
        "",
    ]

    if item.get("summary"):
        lines.append(f"{item['summary']}")
        lines.append("")

    lines.append(f"🔗 <a href=\"{item['link']}\">مشاهده در MangaDex</a>")
    lines.append("")
    lines.append("➖➖➖➖➖➖➖➖➖")
    lines.append("🤖 بات خبری انیمه و مانهوا")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# 📤 ارسال پیام به کانال بله
# ─────────────────────────────────────────────
def send_text(text):
    """ارسال پیام متنی به کانال"""
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
            print(f"⚠️ خطا در ارسال: {result}")
            return False
    except Exception as e:
        print(f"❌ خطای شبکه: {e}")
        return False


def send_photo_with_caption(image_url, caption):
    """ارسال عکس با کپشن به کانال"""
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
            # اگر عکس ارسال نشد، به صورت متنی ارسال کن
            print(f"⚠️ عکس ارسال نشد، ارسال متنی...")
            return send_text(caption + f"\n\n🖼️ <a href=\"{image_url}\">تصویر</a>")
    except Exception as e:
        print(f"❌ خطا: {e}")
        return send_text(caption)


def post_to_channel(item):
    """ارسال یک خبر به کانال"""
    if item["category"] == "manhwa":
        text = format_manhwa_message(item)
    else:
        text = format_news_message(item)

    if item.get("image"):
        return send_photo_with_caption(item["image"], text)
    else:
        return send_text(text)


# ─────────────────────────────────────────────
# 🚀 تابع اصلی
# ─────────────────────────────────────────────
def main():
    print("=" * 50)
    print(f"🤖 شروع اجرای بات - {datetime.now(timezone.utc).isoformat()}")
    print("=" * 50)

    if not BOT_TOKEN or not CHANNEL_ID:
        print("❌ لطفاً متغیرهای BALE_BOT_TOKEN و BALE_CHANNEL_ID را تنظیم کنید!")
        return

    # ۱. بارگذاری اخبار قبلاً ارسال شده
    posted_ids = load_posted_ids()
    print(f"📊 تعداد اخبار قبلاً ارسال شده: {len(posted_ids)}")

    # ۲. دریافت اخبار جدید
    rss_news = fetch_rss_news()
    manhwa_updates = fetch_manhwa_updates()

    # ترکیب همه اخبار (اخبار RSS اولویت دارند)
    all_items = rss_news + manhwa_updates
    print(f"📥 مجموع اخبار دریافتی: {len(all_items)}")

    # ۳. فیلتر کردن اخبار تکراری
    new_items = [item for item in all_items if item["id"] not in posted_ids]
    print(f"✨ اخبار جدید (ارسال نشده): {len(new_items)}")

    # ۴. ارسال اخبار جدید
    posted_count = 0
    for item in new_items[:MAX_POSTS_PER_RUN]:
        print(f"\n📤 ارسال: {item['title'][:60]}...")

        success = post_to_channel(item)

        if success:
            posted_ids.add(item["id"])
            posted_count += 1
            print("✅ ارسال موفق!")
            time.sleep(3)  # رعایت محدودیت نرخ ارسال
        else:
            print("❌ ارسال ناموفق!")

        time.sleep(1)

    # ۵. ذخیره لیست به‌روز شده
    save_posted_ids(posted_ids)

    print(f"\n{'=' * 50}")
    print(f"✅ پایان اجرا - {posted_count} خبر جدید ارسال شد")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
