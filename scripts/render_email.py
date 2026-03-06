# scripts/render_email.py
import os
import json
import re

def parse_analysis(analysis_text):
    """
    将 Qwen 生成的分析文本按五大维度拆解为字典
    支持多种格式：
      - "核心论点：xxx；yyy。"
      - "- 核心论点\n  - xxx\n  - yyy"
      - "1. 核心论点 - ..."
    """
    sections = {
        "核心论点": [],
        "证据链拆解": [],
        "历史一致性检验": [],
        "产业影响评估": [],
        "潜在风险提示": []
    }

    # 统一换行符，移除开头结尾空白
    text = analysis_text.strip()

    # 尝试按标准标题分割（优先级最高）
    parts = re.split(
        r'\n(?=\s*(?:\d+\.\s*)?(?:核心论点|证据链拆解|历史一致性检验|产业影响评估|潜在风险提示)\s*[:：\-]?)',
        text,
        flags=re.MULTILINE
    )

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # 提取标题（支持：冒号、破折号、或直接标题）
        title_match = re.match(
            r'^(\d+\.\s*)?(.*?)(?:[:：\-]|\s*$)',
            part,
            re.DOTALL
        )
        if not title_match:
            continue

        raw_title = title_match.group(2).strip()
        content_part = part[title_match.end():].strip()

        # 标准化标题名
        normalized_title = None
        for key in sections:
            if key in raw_title:
                normalized_title = key
                break
        if not normalized_title:
            continue

        # 提取内容条目：支持 -、1.、2.、• 等格式
        items = []
        if content_part:
            # 按常见列表符号分割
            lines = re.split(r'\n\s*[-•]\s*|\n\s*\d+\.\s*', content_part)
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # 移除行首可能残留的数字或符号
                clean_line = re.sub(r'^(\d+\.\s*|[-•]\s*)', '', line)
                clean_line = clean_line.strip('：: ')
                if clean_line:
                    items.append(clean_line)

        if items:
            sections[normalized_title] = items

    return sections


def render_html_report():
    if os.path.exists('output/unified_today.json'):
        with open('output/unified_today.json', encoding='utf-8') as f:
            results = json.load(f)
    else:
        results = []

    html = """
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
          line-height: 1.8; /* 增大行高 */
          color: #333;
        }
        h1 {
          color: #2c3e50;
          margin-bottom: 0.5em;
        }
        h2 {
          color: #3498db;
          margin-top: 1.8em;
          margin-bottom: 0.6em;
        }
        h3 {
          font-weight: bold;
          font-size: 1.1em;
          margin-top: 1.4em;
          margin-bottom: 0.6em;
          color: #2c3e50;
        }
        .item {
          margin-bottom: 0.7em;
          padding-left: 0.8em;
        }
        hr {
          margin: 2.2em 0;
          border: 0;
          border-top: 1px solid #eee;
        }
        a {
          color: #2980b9;
          text-decoration: none;
        }
        a:hover {
          text-decoration: underline;
        }
      </style>
    </head>
    <body>
    """

    html += "<h1>🎥 AI 领军人物深度洞察日报</h1>\n"
    html += "<p><em>由 GitHub Actions + Qwen-Max (2026) 自动生成</em></p>\n"

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

            html += f"<h2>{source_tag} <a href='{url}'>{title}</a></h2>\n"
            html += f"<p><strong>来源</strong>：{author}</p>\n"
            html += f"<p><strong>原文</strong>：<a href='{url}' target='_blank'>{url}</a></p>\n"

            try:
                sections = parse_analysis(analysis)
                for section_name, items in sections.items():
                    if not items:
                        continue
                    # 使用 <h3> 呈现标题（加粗、放大、单独一行）
                    html += f"<h3>{section_name}</h3>\n"
                    for idx, content in enumerate(items, 1):
                        # 转义 HTML 特殊字符
                        safe_content = (
                            content
                            .replace('&', '&amp;')
                            .replace('<', '&lt;')
                            .replace('>', '&gt;')
                            .replace('"', '&quot;')
                        )
                        html += f"<div class='item'>{idx}. {safe_content}</div>\n"
            except Exception as e:
                html += f"<p><em>解析分析失败：{str(e)}</em></p>"
                html += f"<pre>{analysis}</pre>"

            html += "<hr>\n"

    html += "</body></html>"
    return html


# ===== 发送邮件部分 =====
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
