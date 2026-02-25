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

# === 配置 ===
YOUTUBE_API_KEY = os.environ['YOUTUBE_API_KEY']
DASHSCOPE_API_KEY = os.environ['DASHSCOPE_API_KEY']  # 必须是新申请的 Key
EMAIL_USER = os.environ['EMAIL_USER']
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']
TO_EMAIL = os.environ['TO_EMAIL']

dashscope.api_key = DASHSCOPE_API_KEY

# === 模型配置 ===
MODEL_NAME = 'qwen3-max-2026-01-23'  # ← 使用最强模型
MAX_TOKENS = 1200
TEMPERATURE = 0.2  # 降低随机性，提升严谨性

def get_videos_from_channels():
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
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
            print(f"⚠️ RSS error ({feed_url}): {e}")
    return items

def get_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'zh-Hans'])
        return ' '.join([t['text'] for t in transcript_list])
    except:
        return None

def summarize_with_qwen(title, content):
    if not content or len(content.strip()) < 50:
        return "（内容过短，无法分析）"
    
    full_prompt = PROMPT_TEMPLATE.format(
        title=title[:200],
        content=content[:12000]
    )
    
    try:
        response = Generation.call(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": full_prompt}],  # 关键：用 messages
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            result_format='text'
        )
        if response.status_code == 200:
            return response.output.text.strip()
        else:
            return f"（AI分析失败: {response.code} | {getattr(response, 'message', '')}）"
    except Exception as e:
        return f"（调用异常: {str(e)[:150]}）"
    
    is_fallback = "标题：" in content and "\n\n描述：" in content
    context_desc = "含完整字幕的视频" if not is_fallback else "仅含标题与描述的视频（无字幕）"
    
    prompt = f"""
你是一位资深 AI 与芯片产业分析师，拥有斯坦福大学博士学位和 NVIDIA 前战略顾问经验。请基于以下{context_desc}内容，进行深度、严谨、有洞察力的分析。

【输入内容类型】
{context_desc}

【任务要求】
1. 【核心主张提炼】  
   - 用一句话概括发言人的核心论点（不超过 30 字）。
   - 指出该主张属于：技术路线宣示 / 商业战略调整 / 行业趋势判断 / 个人理念表达。

2. 【证据链拆解】  
   - 列出支撑该主张的 2–3 个关键证据（数据、案例、逻辑推导）。
   - 若为推测，请标注“（推测）”，并说明依据。

3. 【历史一致性检验】  
   - 对比该人物过去 6 个月公开言论，判断本次发言是：
     □ 延续原有立场  
     □ 微调表述  
     □ 明显转向  
   - 简要说明理由。

4. 【产业影响评估】  
   - 对以下领域可能产生的影响（选 1–2 个最相关的）：
     • AI 芯片竞争格局  
     • 云计算厂商策略  
     • 自动驾驶技术路径  
     • 开源 vs 闭源生态  
     • 投资者预期

5. 【信息新颖性评级】  
   - ✅ 全新披露（首次提及技术细节/合作/时间表）  
   - ⚠️ 已知信息强化（重复强调但无新细节）  
   - ❓ 语义模糊（缺乏可验证内容）

【输出格式】
- 使用中文；
- 每部分以【】开头；
- 不使用 Markdown；
- 避免主观评价，聚焦事实与逻辑。

---
标题：{title}
内容：{content[:12000]}
"""
    try:
        response = Generation.call(
            model=MODEL_NAME,
            prompt=prompt,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            result_format='text'
        )
        if response.status_code == 200:
            return response.output.text.strip()
        else:
            return f"（AI 分析失败: {response.code}）"
    except Exception as e:
        return f"（调用异常: {str(e)}）"

def send_email(subject, items):
    msg = MIMEMultipart("alternative")
    msg['From'] = EMAIL_USER
    msg['To'] = TO_EMAIL
    msg['Subject'] = subject

    html_items = ""
    for item in items:
        summary_html = item['summary'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        summary_html = summary_html.replace('\n', '<br>').replace(' ', '&nbsp;')
        html_items += f'''
        <div style="border-left: 4px solid #0d6efd; padding-left: 15px; margin: 20px 0;">
            <div style="font-size: 14px; color: #6c757d; margin-bottom: 5px;">{item['source']}</div>
            <div style="font-weight: bold; font-size: 18px; color: #0d6efd;">{item['title']}</div>
            <div style="color: #6c757d; font-size: 14px;"><a href="{item['link']}" style="color: #0d6efd;">{item['link']}</a></div>
            <div style="margin-top: 10px; white-space: pre-wrap; line-height: 1.6;">{summary_html}</div>
        </div>
        '''

    html_body = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
                line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
                color: white; padding: 25px; border-radius: 12px; text-align: center; margin-bottom: 30px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🤖 全球 AI 与科技领袖深度日报</h2>
            <p>基于 qwen3-max-2026-01-23 模型 | 聚焦一手信源</p>
        </div>
        {html_items if items else '<p style="text-align: center; color: #666; font-size: 16px;">过去24小时未发现高价值内容。</p>'}
        <p style="color: #6c757d; font-size: 12px; text-align: center; margin-top: 40px;">由 AI 自动生成 · 仅供参考</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)

def main():
    print(f"🔍 开始收集高价值信源... (模型: {MODEL_NAME})")
    all_items = []

    # YouTube 处理
    for item in get_videos_from_channels() + search_videos_by_keywords():
        vid = item['id']['videoId']
        title = item['snippet']['title']
        description = item['snippet'].get('description', '')
        link = f"https://www.youtube.com/watch?v={vid}"
        
        transcript = get_transcript(vid)
        content_for_ai = transcript if transcript else f"标题：{title}\n\n描述：{description[:2000]}"
        
        summary = summarize_with_qwen(title, content_for_ai, "YouTube 视频")
        all_items.append({"source": item['source'], "title": title, "link": link, "summary": summary})

    # RSS 处理
    for item in get_rss_items():
        content = item['content'] or item['summary']
        summary = summarize_with_qwen(item['title'], content, "博客文章")
        all_items.append({"source": item['source'], "title": item['title'], "link": item['link'], "summary": summary})

    subject = f"【深度日报】{datetime.now().strftime('%Y-%m-%d')} | {len(all_items)} 条高价值内容"
    send_email(subject, all_items)
    print(f"✅ 共处理 {len(all_items)} 条内容，邮件已发送！")

if __name__ == '__main__':
    main()
