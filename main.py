import asyncio
import os
from datetime import datetime

from google import genai
import telegram
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ====================== 從 Railway Variables 讀取 ======================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ====================== Debug 檢查 ======================
print("🔍 DEBUG - Bot 啟動（Gemini 直接總結模式）")
print(f"GEMINI_API_KEY = {'✅ 已填寫' if GEMINI_API_KEY and GEMINI_API_KEY.startswith('AIzaSy') else '❌ 未設定或錯誤'}")
print(f"TELEGRAM_TOKEN = {'✅ 已填寫' if TELEGRAM_TOKEN else '❌ 未設定'}")
print(f"TELEGRAM_CHAT_ID = {'✅ 已填寫' if TELEGRAM_CHAT_ID else '❌ 未設定'}")
print("-----------------------------------")

if not GEMINI_API_KEY or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ Railway Variables 中缺少 GEMINI_API_KEY、TELEGRAM_TOKEN 或 TELEGRAM_CHAT_ID，請先設定！")

# ====================== 初始化 ======================
client = genai.Client(api_key=GEMINI_API_KEY)
scheduler = AsyncIOScheduler()

async def fetch_and_send():
    print(f"[{datetime.now()}] 讓 Gemini 總結最近 Crypto & AI 熱點...")

    prompt = f"""
你是 Crypto 和 AI 領域的專業分析師。
現在時間是 {datetime.now().strftime('%Y-%m-%d %H:%M')}。

請直接瀏覽 X（Twitter）上最新的 Crypto 和 AI 相關討論，用繁體中文輸出「Crypto & AI 每4小時熱點摘要」：

格式要求：
**Crypto & AI 每4小時熱點摘要**（{datetime.now().strftime('%Y-%m-%d %H:%M')}）

1. **Top 熱點**（5-8 則最重要）
   - [重點] 簡短說明 + 相關連結（如果有）
2. **潛在機會 / 風險提醒**

請盡量包含最近幾小時內的熱門話題、價格波動、重要項目新聞、技術發展等。
用條列式，讓人容易快速閱讀。
"""

    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",   # 穩定模型
                contents=prompt
            )
            summary_text = response.text
            print(f"[{datetime.now()}] Gemini 總結完成")
            break
        except Exception as e:
            error_str = str(e).lower()
            if "503" in error_str or "unavailable" in error_str or "high demand" in error_str:
                wait = 45 * (attempt + 1)
                print(f"[{datetime.now()}] Gemini 伺服器高負載，等待 {wait} 秒後重試... ({attempt+1}/4)")
                await asyncio.sleep(wait)
                continue
            elif "429" in error_str:
                summary_text = "❌ Gemini 今日免費額度已用完。\n\n請明天再試，或升級付費方案。"
            elif "403" in error_str or "permission_denied" in error_str:
                summary_text = "❌ Gemini API Key 無效或已被封鎖。\n\n請申請新的 API Key。"
            else:
                summary_text = f"❌ Gemini 總結失敗：{str(e)[:200]}"
            print(f"❌ Gemini 錯誤：{str(e)}")

    # 發送到 Telegram
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=summary_text,
            parse_mode="HTML"
        )
        print(f"[{datetime.now()}] ✅ 摘要已發送到 Telegram")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Telegram 發送失敗：{str(e)}")

async def main():
    print("🤖 Bot 已啟動（Gemini 直接模式），每 4 小時執行一次...")
    await fetch_and_send()   # 先跑一次測試
    scheduler.add_job(fetch_and_send, 'interval', hours=4)
    scheduler.start()

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
