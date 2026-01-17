# AINews

AIニュースを自動収集してGitHub Pagesで公開するプロジェクト

## 仕組み

- **GitHub Actions** が毎朝6時（JST）に自動実行
- 各種RSSフィードから直近48時間のAIニュースを取得
- 記事のタイトル・要約を日本語に翻訳
- **GitHub Pages** にHTMLとして公開

## 公開URL

https://bubbles39.github.io/AINews/

## ニュースソース

- MIT Technology Review - AI
- VentureBeat - AI
- The Verge - AI
- TechCrunch - AI
- Google AI Blog
- OpenAI Blog
