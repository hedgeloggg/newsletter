#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度产业洞察日报系统（完整生产版）
- 抓取全球顶级科技信源
- 调用 qwen3-max-2026-01-23 进行深度分析
- 自动发送结构化邮件
"""

import os
import logging
from datetime import datetime, timedelta
import feedparser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from typing import List, Dict

# YouTube 依赖
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

# DashScope
import dashscope
from dashscope import Generation

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# === 配置 ===
YOUTUBE_API_KEY = os.environ['YOUTUBE_API_KEY']
DASHSCOPE_API_KEY = os.environ['DASHSCOPE_API_KEY']
EMAIL_USER = os.environ['EMAIL_USER']
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']
TO_EMAIL = os.environ['TO_EMAIL']

dashscope.api_key = DASHSCOPE_API_KEY
MODEL_NAME = 'qwen3-max-2026-01-23'
MAX_TOKENS = 1200
TEMPERATURE = 0.2

# === 信源配置 ===
YOUTUBE_CHANNELS = [
    {"name": "OpenAI", "id": "UC8butISFwT-Wl7EV0hUK0BQ"},
    {"name": "Google DeepMind", "id": "UC9uXsE4oZh8QH6xJp7xUjCw"},
    {"name": "NVIDIA", "id": "UC9vRjuQx5V0Oc0hZ8M_7QjA"},
    {"name": "Lex Fridman Podcast", "id": "UCSHZKyawb77ixDdsGog4iWA"},
]

RSS_FEEDS = [
    "https://a16z.com/feed/",
    "https://www.sequoiacap.com/articles/feed/",
    "https://blog.ycombinator.com/rss/",
    "https://karpathy.ai/feed.xml",
    "https://openai.com/blog/rss/",
]


# === 核心分析函数 ===
def analyze_with_expert_lens(context_desc: str, source_type: str = "未注明信源") -> str:
    prompt = f"""你是一位资深 AI 与芯片产业分析师，拥有斯坦福大学博士学位和 NVIDIA 前战略顾问经验。请基于以下内容，进行深度、严谨、有洞察力的分析。

【输入内容类型】
{source_type}

【输入内容】
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
"""
    try:
        response = Generation.call(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
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


# === YouTube 抓取 ===
def get_youtube_items() -> List[Dict]:
    items = []
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    # 获取频道最新视频
    for channel in YOUTUBE_CHANNELS:
        request = youtube.search().list(
            part="snippet",
            channelId=channel["id"],
            order="date",
            type="video",
            publishedAfter=(datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ'),
            maxResults=2
        )
        response = request.execute()
        
        for item in response.get('items', []):
            vid = item['id']['videoId']
            title = item['snippet']['title']
            link = f"https://www.youtube.com/watch?v={vid}"
            
            # 尝试获取字幕
            transcript = None
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(vid, languages=['en', 'zh-Hans'])
                transcript = ' '.join([t['text'] for t in transcript_list])
            except:
                pass
            
            content = transcript if transcript else f"标题：{title}\n\n描述：{item['snippet'].get('description', '')}"
            summary = analyze_with_expert_lens(content, f"YouTube: {channel['name']}")
            
            items.append({
                "source": channel["name"],
                "title": title,
                "link": link,
                "summary": summary
            })
            logger.info(f"✅ 处理 YouTube: {title[:50]}...")
    
    return items


# === RSS 抓取 ===
def get_rss_items() -> List[Dict]:
    items = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:2]:  # 每源取最新2篇
                if hasattr(entry, 'published'):
                    pub_date = datetime(*entry.published_parsed[:6])
                    if pub_date < datetime.utcnow() - timedelta(days=1):
                        continue
                
                title = entry.get('title', '无标题')
                link = entry.get('link', '#')
                content = entry.get('content', [{}])[0].get('value') or entry.get('summary', '')
                
                summary = analyze_with_expert_lens(content, "Blog/RSS")
                items.append({
                    "source": feed_url.split('/')[2],
                    "title": title,
                    "link": link,
                    "summary": summary
                })
                logger.info(f"✅ 处理 RSS: {title[:50]}...")
        except Exception as e:
            logger.error(f"RSS 抓取失败 {feed_url}: {e}")
    return items


# === 邮件发送 ===
def send_email(subject: str, items: List[Dict]):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = TO_EMAIL

    body = ""
    for item in items:
        body += f"来源：{item['source']}\n"
        body += f"标题：{item['title']}\n"
        body += f"链接：{item['link']}\n\n"
        body += item['summary'] + "\n\n"
        body += "──────────────────────────────\n\n"

    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, TO_EMAIL, msg.as_string())
    logger.info(f"📧 邮件已发送至 {TO_EMAIL}")


# === 主流程 ===
def main():
    logger.info(f"🚀 启动深度日报 (模型: {MODEL_NAME})")
    
    all_items = []
    all_items.extend(get_youtube_items())
    all_items.extend(get_rss_items())
    
    if not all_items:
        logger.warning("⚠️ 今日无新内容")
        return
    
    subject = f"【深度日报】{datetime.now().strftime('%Y-%m-%d')} | {len(all_items)} 条高价值内容"
    send_email(subject, all_items)
    logger.info(f"✅ 完成！共处理 {len(all_items)} 条内容")


if __name__ == "__main__":
    main()
