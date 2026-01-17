#!/usr/bin/env python3
"""AIニュース取得スクリプト（日英併記版・アーカイブ対応）"""

import feedparser
from datetime import datetime, timedelta, timezone
from jinja2 import Environment, FileSystemLoader
from deep_translator import GoogleTranslator
import os
import re
import time
import json

# 日本標準時 (JST = UTC+9)
JST = timezone(timedelta(hours=9))

# 過去何時間以内の記事を取得するか
HOURS_LIMIT = 48

# AIニュース RSSフィード一覧
RSS_FEEDS = [
    {
        "name": "MIT Technology Review - AI",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed",
    },
    {
        "name": "VentureBeat - AI",
        "url": "https://venturebeat.com/category/ai/feed/",
    },
    {
        "name": "The Verge - AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    },
    {
        "name": "TechCrunch - AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
    },
    {
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
    },
    {
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog/rss.xml",
    },
]

translator = GoogleTranslator(source='en', target='ja')


def translate_text(text: str) -> str:
    """英語を日本語に翻訳"""
    if not text:
        return ""
    try:
        time.sleep(0.5)  # API制限対策
        return translator.translate(text)
    except Exception as e:
        print(f"    翻訳エラー: {e}")
        return ""


def fetch_feed(feed_info: dict) -> list:
    """RSSフィードから記事を取得（日付フィルター適用）"""
    articles = []
    cutoff_time = datetime.now(JST) - timedelta(hours=HOURS_LIMIT)

    try:
        feed = feedparser.parse(feed_info["url"])
        for entry in feed.entries[:10]:  # 各ソースから最大10記事をチェック
            # 日付を取得（UTC として解釈して JST に変換）
            published_dt = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).astimezone(JST)
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published_dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc).astimezone(JST)

            # 日付がない、または古い記事はスキップ
            if not published_dt or published_dt < cutoff_time:
                continue

            published = published_dt.strftime("%Y-%m-%d")

            summary = ""
            if hasattr(entry, "summary"):
                summary = entry.summary
                summary = re.sub(r'<[^>]+>', '', summary)
                summary = summary[:200] + "..." if len(summary) > 200 else summary

            # 翻訳
            print(f"    翻訳中: {entry.title[:30]}...")
            title_ja = translate_text(entry.title)
            summary_ja = translate_text(summary) if summary else ""

            articles.append({
                "title": entry.title,
                "title_ja": title_ja,
                "link": entry.link,
                "published": published,
                "summary": summary,
                "summary_ja": summary_ja,
                "source": feed_info["name"],
            })
    except Exception as e:
        print(f"Error fetching {feed_info['name']}: {e}")

    return articles


def load_archives(output_dir: str) -> list:
    """過去のアーカイブ一覧を読み込む"""
    archives_file = os.path.join(output_dir, "archives.json")
    if os.path.exists(archives_file):
        with open(archives_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_archives(output_dir: str, archives: list):
    """アーカイブ一覧を保存"""
    archives_file = os.path.join(output_dir, "archives.json")
    with open(archives_file, "w", encoding="utf-8") as f:
        json.dump(archives, f, ensure_ascii=False, indent=2)


def main():
    """メイン処理"""
    print("AIニュースを取得中...")

    all_articles = []
    for feed_info in RSS_FEEDS:
        print(f"  - {feed_info['name']}")
        articles = fetch_feed(feed_info)
        all_articles.extend(articles)

    # 日付でソート（新しい順）
    all_articles.sort(key=lambda x: x["published"], reverse=True)

    # パス設定
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    archives_dir = os.path.join(output_dir, "archives")
    os.makedirs(archives_dir, exist_ok=True)

    # テンプレート読み込み
    env = Environment(loader=FileSystemLoader(os.path.join(script_dir, "templates")))

    today = datetime.now(JST).strftime("%Y-%m-%d")
    updated_at = datetime.now(JST).strftime("%Y-%m-%d %H:%M")

    # アーカイブ一覧を読み込み・更新
    archives = load_archives(output_dir)
    if today not in archives:
        archives.insert(0, today)  # 最新を先頭に
    # 最大30日分保持
    archives = archives[:30]
    save_archives(output_dir, archives)

    # 今日のアーカイブを保存
    if all_articles:
        archive_template = env.get_template("archive.html")
        archive_html = archive_template.render(
            articles=all_articles,
            date=today,
            total_count=len(all_articles),
        )
        archive_path = os.path.join(archives_dir, f"{today}.html")
        with open(archive_path, "w", encoding="utf-8") as f:
            f.write(archive_html)
        print(f"アーカイブ保存: {archive_path}")

    # メインページ（index.html）を生成
    index_template = env.get_template("index.html")
    html = index_template.render(
        articles=all_articles,
        updated_at=updated_at,
        total_count=len(all_articles),
        archives=archives,
    )

    output_path = os.path.join(output_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n完了: {len(all_articles)}件の記事を取得しました")
    print(f"出力: {output_path}")


if __name__ == "__main__":
    main()
