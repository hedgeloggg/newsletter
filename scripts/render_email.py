# scripts/render_email.py
import os
import json
import markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import re

def parse_analysis(analysis_text):
    """将 Qwen 生成的分析文本按五大维度拆解为字典"""
    sections = {
        "核心论点": [],
        "证据链拆解": [],
        "历史一致性检验": [],
        "产业影响评估": [],
        "潜在风险提示": []
    }
    
    # 按维度分割（支持中英文冒号）
    parts = re.split(r'\n(?=(?:核心论点|证据链拆解|历史一致性检验|产业影响评估|潜在风险提示)\s*[:：])', analysis_text.strip())
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # 提取标题和内容
        match = re.match(r'^(.*?)(?:[:：])\s*(.*)', part, re.DOTALL)
        if not match:
            continue
        
        title, content = match.groups()
        title = title.strip()
        content = content.strip()
        
        # 清理内容中的多余换行，按句/点拆分为列表
        if content:
            # 按句号、分号、或手动换行拆分
            items = [item.strip() for item in re.split(r'[；;。]\s*', content) if item.strip()]
            if not items:
                items = [content]
            sections[title] = items
    
    return sections

def render_html_report():
    if os.path.exists('output/unified_today.json'):
        with open('output/unified_today.json') as f:
            results = json.load(f)
    else:
        results = []

    # 使用内联 CSS 控制行高（更可靠）
    html = """
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; line-height: 1.6; }
        h1 { color: #2c3e50; }
        h2 { color: #3498db; margin-top: 1.5em; }
        .section-title { font-weight: bold; margin-top: 1.2em; margin-bottom: 0.4em; }
        .item { margin-bottom: 0.8em; }
        hr { margin: 2em 0; }
      </style>
    </head>
    <body>
    """

    if not results:
        html += "<p>📅 <strong>过去 1 天内未发现相关深度内容</strong></p>\n"
        html += "<p>系统已扫描 YouTube、Apple Podcasts、Spotify 等平台的 30+ 权威信源。</p>\n"
    else:
        for item in results:
            source_tag = "🎧" if item.get('source_type') == 'podcast' else "🎥"
            title = item['title']
            url = item['url']
            author = item['author']
            analysis = item.get('analysis', "*分析生成中...*")

            html += f"<h2>{source_tag} <a href='{url}' style='text-decoration:none; color:#2980b9;'>{title}</a></h2>\n"
            html += f"<p><strong>来源</strong>：{author}</p>\n"
            html += f"<p><strong>原文</strong>：<a href='{url}' target='_blank'>{url}</a></p>\n"

            # 解析分析内容
            try:
                sections = parse_analysis(analysis)
                for section_name, items in sections.items():
                    if not items:
                        continue
                    html += f"<div class='section-title'>{section_name}</div>\n"
                    for idx, content in enumerate(items, 1):
                        # 转义 HTML 特殊字符
                        safe_content = (content
                                        .replace('&', '&amp;')
                                        .replace('<', '&lt;')
                                        .replace('>', '&gt;'))
                        html += f"<div class='item'>{idx}. {safe_content}</div>\n"
            except Exception as e:
                html += f"<p><em>解析分析失败：{str(e)}</em></p>"
                html += f"<pre>{analysis}</pre>"

            html += "<hr>\n"

    html += "</body></html>"
    return html

# ===== 以下是发送邮件部分（保持不变）=====
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(html_content):
    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")
    to_email = os.getenv("TO_EMAIL")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "AI 领军人物深度洞察日报"
    msg["From"] = sender
    msg["To"] = to_email

    html_part = MIMEText(html_content, "html", "utf-8")
    msg.attach(html_part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, to_email, msg.as_string())

if __name__ == "__main__":
    html_report = render_html_report()
    send_email(html_report)
