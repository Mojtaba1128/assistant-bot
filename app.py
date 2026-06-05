import os
from flask import Flask, request
import requests
from supabase import create_client

app = Flask(__name__)

# ==================== تنظیمات ====================
TOKEN = "8811644080:AAEGT3xaiNi9UORlIWVWz77lZDTp8fKqphY"
SUPABASE_URL = "https://hayyejlukxhzkflwvdjw.supabase.co"
SUPABASE_KEY = "sb_publishable_RXbbfm5cadYSXULJ6ePr4A_MQXsJ4XG"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

# ==================== ساختار نودها (دوزبانه) ====================
NODES_DNA = [
    # ===== شکارچی ترند =====
    {
        "node_name": "trend_hunter",
        "description": "شکارچی ترند - ترندهای روز جهانی و ایران",
        "description_en": "Trend Hunter - Global & Iranian daily trends",
        "status": "active",
        "config": {
            "sources": ["pytrends", "reddit", "nitter", "news_fa", "news_en"],
            "languages": ["fa", "en"],
            "regions": ["iran", "global", "us"]
        }
    },
    # ===== تحقیق‌گر =====
    {
        "node_name": "researcher",
        "description": "خبرنگار تحقیق‌گر - تحقیق عمیق فارسی و انگلیسی",
        "description_en": "Deep Researcher - Bilingual deep research",
        "status": "active",
        "config": {
            "sources": ["brave_search", "tavily", "google_news_fa", "google_news_en"],
            "languages": ["fa", "en"],
            "fact_check": True
        }
    },
    # ===== روانشناس مخاطب =====
    {
        "node_name": "psychologist",
        "description": "روانشناس مخاطب - تحلیل مخاطب فارسی و انگلیسی زبان",
        "description_en": "Audience Psychologist - FA & EN audience analysis",
        "status": "active",
        "config": {
            "languages": ["fa", "en"],
            "hooks_fa": ["شوک", "کنجکاوی", "ترس از دست دادن", "داستان‌سرایی"],
            "hooks_en": ["shock", "curiosity", "fomo", "storytelling"],
            "emotional_map": True
        }
    },
    # ===== فیلمنامه‌نویس =====
    {
        "node_name": "script_genius",
        "description": "فیلمنامه‌نویس - اسکریپت فارسی و انگلیسی",
        "description_en": "Script Genius - FA & EN script writer",
        "status": "active",
        "config": {
            "languages": ["fa", "en"],
            "formats": {
                "short": {"duration_sec": 60, "word_count_fa": 150, "word_count_en": 170},
                "long_5min": {"duration_sec": 300, "word_count_fa": 750, "word_count_en": 850},
                "long_10min": {"duration_sec": 600, "word_count_fa": 1500, "word_count_en": 1700},
                "long_15min": {"duration_sec": 900, "word_count_fa": 2250, "word_count_en": 2550}
            }
        }
    },
    # ===== شکارچی مدیا =====
    {
        "node_name": "media_hunter",
        "description": "شکارچی عکس و مدیا - بدون کپی‌رایت",
        "description_en": "Media Hunter - Copyright-free images & clips",
        "status": "active",
        "config": {
            "sources": ["unsplash", "pexels", "pixabay", "openverse"],
            "search_languages": ["fa", "en"],
            "auto_translate_search": True,
            "min_quality": "1080p"
        }
    },
    # ===== گوینده =====
    {
        "node_name": "voice_engine",
        "description": "گوینده - ویس فارسی و انگلیسی",
        "description_en": "Voice Engine - FA & EN text-to-speech",
        "status": "active",
        "config": {
            "primary": "xtts_v2",
            "fallback": "edge_tts",
            "languages": {
                "fa": {"model": "xtts_v2", "voice": "male_fa"},
                "en": {"model": "xtts_v2", "voice": "male_en"}
            }
        }
    },
    # ===== تدوین‌گر =====
    {
        "node_name": "video_editor",
        "description": "تدوین‌گر - ساخت ویدیو شورت و لانگ",
        "description_en": "Video Editor - Short & Long form",
        "status": "active",
        "config": {
            "engine": "ffmpeg",
            "render": "ram",
            "subtitles": True,
            "subtitles_lang": ["fa", "en"],
            "quality": {"short": "1080x1920", "long": "1920x1080"}
        }
    },
    # ===== جاسوس رقبا =====
    {
        "node_name": "competitor_spy",
        "description": "جاسوس رقبا - رصد ۲۴ ساعته رقبای فارسی و انگلیسی",
        "description_en": "Competitor Spy - 24/7 FA & EN competitor monitoring",
        "status": "active",
        "config": {
            "platforms_fa": ["youtube_fa", "telegram", "instagram_fa"],
            "platforms_en": ["youtube_en", "tiktok", "reddit"],
            "report_interval_hours": 8
        }
    },
    # ===== هماهنگ‌کننده =====
    {
        "node_name": "orchestrator",
        "description": "فرمانده کل - هماهنگ‌کننده تمام نودها",
        "description_en": "Orchestrator - Master coordinator",
        "status": "active",
        "config": {
            "max_parallel_jobs": 3,
            "project_types": ["short", "long"],
            "auto_cleanup_after_approval": True
        }
    }
]

# ==================== ذخیره نودها ====================
def init_nodes():
    results = {"new": [], "existing": []}
    for node in NODES_DNA:
        existing = supabase.table("node_dna").select("*").eq("node_name", node["node_name"]).execute()
        if not existing.data:
            supabase.table("node_dna").insert(node).execute()
            results["new"].append(node["node_name"])
        else:
            results["existing"].append(node["node_name"])
    return results

# ==================== تلگرام ====================
def send_message(chat_id, text):
    requests.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": chat_id, "text": text})

def handle_update(update):
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        
        if "text" in msg:
            text = msg["text"]
            
            if text == "/start":
                send_message(chat_id, 
                    "🚀 سلام! من دستیار فوق‌پیشرفته‌ات هستم.\n"
                    "🎯 پشتیبانی از محتوای فارسی و انگلیسی\n"
                    "📹 شورت (۶۰ ثانیه) و لانگ (تا ۱۵ دقیقه)\n\n"
                    "برای دیدن نودهای فعال: /nodes\n"
                    "برای راهنما: /help"
                )
            elif text == "/nodes":
                nodes = supabase.table("node_dna").select("*").execute()
                fa = [n for n in nodes.data if n["description"]]
                en = [n for n in nodes.data if n.get("description_en")]
                
                msg_text = "🧠 نودهای فعال:\n\n🇮🇷 فارسی:\n"
                msg_text += "\n".join([f"🔹 {n['node_name']}: {n['description']}" for n in fa])
                msg_text += "\n\n🇬🇧 English:\n"
                msg_text += "\n".join([f"🔹 {n['node_name']}: {n['description_en']}" for n in en])
                
                send_message(chat_id, msg_text)
            elif text == "/help":
                send_message(chat_id,
                    "📋 دستورات:\n"
                    "/start - شروع\n"
                    "/nodes - نودهای فعال\n"
                    "/help - راهنما\n\n"
                    "📹 پروژه جدید:\n"
                    "فارسی: «یه شورت درباره ترند امروز بساز»\n"
                    "English: «Make a short about today's trend»\n"
                    "لانگ: «یه ویدیو ۱۰ دقیقه‌ای درباره فلان موضوع»"
                )
            else:
                send_message(chat_id, "✅ دریافت شد. سیستم در حال راه‌اندازی کامل. به زودی پاسخ می‌دم.")

# ==================== Webhook ====================
@app.route("/", methods=["POST"])
def webhook():
    handle_update(request.get_json())
    return "ok"

@app.route("/", methods=["GET"])
def health():
    return "✅ Bot is alive | ربات زنده‌ست"

# ==================== شروع ====================
if __name__ == "__main__":
    results = init_nodes()
    print(f"✅ نودهای جدید: {len(results['new'])} | ⏭️ قبلی: {len(results['existing'])}")
    print("🚀 ربات آماده‌ست")
    app.run(host="0.0.0.0", port=10000)
