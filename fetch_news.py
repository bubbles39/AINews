#!/usr/bin/env python3
"""AIニュース取得スクリプト（日英併記版）"""

import feedparser
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
from deep_translator import GoogleTranslator
import os
import re
import time

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
    cutoff_time = datetime.now() - timedelta(hours=HOURS_LIMIT)

    try:
        feed = feedparser.parse(feed_info["url"])
        for entry in feed.entries[:10]:  # 各ソースから最大10記事をチェック
            # 日付を取得
            published_dt = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_dt = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published_dt = datetime(*entry.updated_parsed[:6])

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

    # HTMLを生成
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env = Environment(loader=FileSystemLoader(os.path.join(script_dir, "templates")))
    template = env.get_template("index.html")

    html = template.render(
        articles=all_articles,
        updated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        total_count=len(all_articles),
    )

    # 出力
    output_path = os.path.join(script_dir, "output", "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n完了: {len(all_articles)}件の記事を取得しました")
    print(f"出力: {output_path}")


if __name__ == "__main__":
    main()
