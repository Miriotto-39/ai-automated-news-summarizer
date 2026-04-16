import os
import requests
import schedule
import time
import threading
from datetime import datetime
from bs4 import BeautifulSoup
from fastapi import FastAPI
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

# --- ニュース取得と保存のメイン処理 ---
def fetch_and_summarize():
    print(f"[{datetime.now()}] ニュース取得を開始します...")
    
    # URL指定
    url = "https://news.google.com/home?hl=ja&gl=JP&ceid=JP%3Aja"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # タイトルを抽出
        articles = soup.find_all("a", class_="gPFEn", limit=15)
        news_titles = [article.get_text() for article in articles]
        combined_titles = "\n".join(news_titles)

        if not combined_titles:
            print("ニュースが取得できませんでした。")
            return

        # AIで要約
        ai_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "IT専門アナリストとして、ビジネスに重要なニュースを3つ厳選し、1行ずつ要約してください。"},
                {"role": "user", "content": combined_titles}
            ]
        )
        summary = ai_response.choices[0].message.content

        # ファイル保存
        now = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"auto_news_{now}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"【定期実行レポート：{now}】\n")
            f.write(summary)
        print(f"レポートを作成しました: {filename}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

# --- スケジュール設定（ここが重要！） ---
schedule.every().day.at("08:00").do(fetch_and_summarize) # 朝8時
schedule.every().day.at("12:00").do(fetch_and_summarize) # 昼12時
schedule.every().day.at("19:00").do(fetch_and_summarize) # 夜19時

# 裏側で時計を動かし続けるための関数
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# プログラム起動時に、スケジュール機能を別スレッドで開始
threading.Thread(target=run_scheduler, daemon=True).start()

@app.get("/status")
def get_status():
    return {"status": "自動監視中", "info": "毎日08:00, 12:00, 19:00に自動実行されます。"}
