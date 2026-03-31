import asyncio
from datetime import datetime
from google import genai
import telegram
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import time

# ====================== 變數設定 ======================
GEMINI_API_KEY = "AIzaSyCHrDcXab742GW097ApwOx0c760t7hEBcM"
TELEGRAM_TOKEN = "8700350043:AAEWenpl6_MJFLwsj9KZBp-wSaW80RQKRAE"
TELEGRAM_CHAT_ID = "761195164"

print("🔍 DEBUG - Bot 啟動（Gemini 直接總結模式）")
print(f"GEMINI_API_KEY = {'✅ 已填寫' if GEMINI_API_KEY else '❌ 空的！'}")
print(f"TELEGRAM_TOKEN = {'✅ 已填寫' if TELEGRAM_TOKEN else '❌ 空的！'}")
print("-----------------------------------")

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

    for attempt in range(3):  # 最多重試 3 次
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",   # ← 正確的當前模型名稱
                contents=prompt
            )
            summary_text = response.text
            print(f"[{datetime.now()}] Gemini 總結完成")
            break
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                wait_time = 30
                print(f"[{datetime.now()}] Gemini 額度用完，等待 {wait_time} 秒後重試... ({attempt+1}/3)")
                if attempt < 2:
                    await asyncio.sleep(wait_time)
                    continue
                summary_text = "❌ Gemini 今日免費額度已用完。\n\n請稍後再試，或升級 Gemini API 方案。"
            else:
                summary_text = f"❌ Gemini 總結失敗：{error_str}"
            print(f"❌ Gemini 錯誤：{error_str}")

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
