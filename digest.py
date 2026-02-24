import os
import feedparser
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import dashscope
from dashscope import Generation
from sources import YOUTUBE_CHANNELS, YOUTUBE_KEYWORDS, RSS_FEEDS

# 配置
YOUTUBE_API_KEY = os.environ['YOUTUBE_API_KEY']
DASHSCOPE_API_KEY = os.environ['DASHSCOPE_API_KEY']
EMAIL_USER = os.environ['EMAIL_USER']
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']
TO_EMAIL = os.environ['TO_EMAIL']

dashscope.api_key = DASHSCOPE_API_KEY

def get_videos_from_channels():
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    yesterday = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
    items = []
    for channel in YOUTUBE_CHANNELS:
        request = youtube.search().list(
            channelId=channel["id"],
            part='snippet',
            type='video',
            publishedAfter=yesterday,
            maxResults=5
        )
        response = request.execute()
        for item in response.get('items', []):
            item['source'] = f"[频道] {channel['name']}"
            items.append(item)
    return items

def search_videos_by_keywords():
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    q = " OR ".join(f'"{kw}"' for kw in YOUTUBE_KEYWORDS)
    request = youtube.search().list(
        q=q,
        part='snippet',
        type='video',
        publishedAfter=yesterday,
        maxResults=10,
        order='date'
    )
    response = request.execute()
    items = response.get('items', [])
    for item in items:
        item['source'] = "[关键词]"
    return items

def get_rss_items():
    yesterday = datetime.utcnow() - timedelta(days=1)
    items = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                pub_date = entry.get('published_parsed')
                if pub_date:
                    entry_date = datetime(*pub_date[:6])
                    if entry_date > yesterday:
                        items.append({
                            "title": entry.title,
                            "link": entry.link,
                            "summary": entry.get('summary', '') or entry.get('description', ''),
                            "source": "[RSS]",
                            "content": entry.get('content', [{}])[0].get('value', '')
                        })
        except Exception as e:
            print(f"RSS error ({feed_url}): {e}")
    return items

def get_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'zh-Hans'])
        return ' '.join([t['text'] for t in transcript_list])
    except:
        return None

def summarize_with_qwen(title, content, source_type):
    if not content:
        return "（无可用内容）"
    truncated_content = content[:10000]
    prompt = f"""
你是一位资深科技分析师，请基于以下{source_type}内容，按以下结构输出中文分析：

【核心论点】
- 用 1–2 句话概括核心主张。

【关键论据】
- 列出 2–3 个具体事实、数据、案例或逻辑推理。

【背景关联】
- 此内容与该人物过去 6 个月的公开言论是否一致？属于延续、修正还是转折？

【信息增量】
- 相比主流媒体报道，是否有新披露的技术细节、战略方向或未公开信息？（回答：✅ 有新信息 / ⚠️ 已知信息复述 / ❓ 无法判断）

要求：
- 语言简洁、专业；
- 若原文无足够信息，对应部分写“未提及”；
- 不要使用 Markdown。

---
标题：{title}
内容：{truncated_content}
"""
    response = Generation.call(
        model='qwen-max',
        prompt=prompt,
        max_tokens=1000,
        temperature=0.3
    )
    return response.output.text.strip() if response.status_code == 200 else "（AI 分析失败）"

def send_email(subject, items):
    msg = MIMEMultipart("alternative")
    msg['From'] = EMAIL_USER
    msg['To'] = TO_EMAIL
    msg['Subject'] = subject

    text_parts = []
    html_items = ""
    for item in items:
        summary = item['summary']
        text_parts.append(f"{item['source']} {item['title']}\n🔗 {item['link']}\n{summary}\n{'─' * 50}\n")
        
        summary_html = summary.replace('\n', '<br>').replace(' ', '&nbsp;')
        html_items += f'''
        <div style="border-left: 4px solid #0d6efd; padding-left: 15px; margin: 20px 0;">
            <div style="font-size: 14px; color: #6c757d; margin-bottom: 5px;">{item['source']}</div>
            <div style="font-weight: bold; font-size: 18px; color: #0d6efd;">{item['title']}</div>
            <div style="color: #6c757d; font-size: 14px;"><a href="{item['link']}">{item['link']}</a></div>
            <div style="margin-top: 10px; white-space: pre-wrap;">{summary_html}</div>
        </div>
        '''

    text_body = "".join(text_parts) if items else "过去24小时未发现新内容。"
    html_body = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); color: white; padding: 25px; border-radius: 12px; text-align: center; margin-bottom: 30px; }}
            hr {{ border: 0; border-top: 1px dashed #ccc; margin: 25px 0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🤖 全球 AI 与科技领袖日报</h2>
            <p>覆盖技术 · 产业 · 投资 · 思想</p>
        </div>
        {html_items if items else '<p style="text-align: center; color: #666;">过去24小时未发现新内容。</p>'}
        <p style="color: #6c757d; font-size: 12px; text-align: center;">由 AI 自动生成 · 每日 10:00 更新</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)

def main():
    print("🔍 开始收集多源信息...")
    all_items = []

    # 1. YouTube 频道
    print("  → 监控指定 YouTube 频道...")
    youtube_items = get_videos_from_channels()
    for item in youtube_items:
        vid = item['id']['videoId']
        title = item['snippet']['title']
        link = f"https://www.youtube.com/watch?v={vid}"
        transcript = get_transcript(vid)
        summary = summarize_with_qwen(title, transcript, "YouTube 视频")
        all_items.append({"source": item['source'], "title": title, "link": link, "summary": summary})

    # 2. YouTube 关键词
    print("  → 搜索关键词视频...")
    keyword_items = search_videos_by_keywords()
    for item in keyword_items:
        vid = item['id']['videoId']
        title = item['snippet']['title']
        link = f"https://www.youtube.com/watch?v={vid}"
        transcript = get_transcript(vid)
        summary = summarize_with_qwen(title, transcript, "YouTube 视频")
        all_items.append({"source": item['source'], "title": title, "link": link, "summary": summary})

    # 3. RSS 博客/播客
    print("  → 检查 RSS 源...")
    rss_items = get_rss_items()
    for item in rss_items:
        content = item['content'] or item['summary']
        summary = summarize_with_qwen(item['title'], content, "博客/播客文章")
        all_items.append({
            "source": item['source'],
            "title": item['title'],
            "link": item['link'],
            "summary": summary
        })

    subject = f"【AI全景日报】{datetime.now().strftime('%Y-%m-%d')} 全球科技领袖动态"
    send_email(subject, all_items)
    print(f"✅ 共处理 {len(all_items)} 条新内容，邮件已发送！")

if __name__ == '__main__':
    main()
