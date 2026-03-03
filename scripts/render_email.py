# scripts/render_email.py
import os
import sys
import json
import markdown
from email.mime.text import MIMEText
from email.header import Header
import smtplib

# === 注入 scripts 目录（保持一致性）===
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
# ======================================

# scripts/render_email.py （仅修改 render_html_report 函数）
def render_html_report():
    # ✅ 读取合并后的统一数据
    if os.path.exists('output/unified_today.json'):
        with open('output/unified_today.json') as f:
            results = json.load(f)
    else:
        results = []
    
    md = "# 🎥 AI 领军人物深度洞察日报\n\n"
    md += "> *由 GitHub Actions + Qwen3-Max (2026) 自动生成*\n\n"
    
    if not results:
        md += "📅 **过去 100 天内未发现相关深度内容**\n\n"
        md += "系统已扫描 YouTube、Apple Podcasts、Spotify 等平台的 30+ 权威信源。\n"
    else:
        for item in results:
            # 标注来源类型
            source_tag = "🎧" if item.get('source_type') == 'podcast' else "🎥"
            md += f"## {source_tag} [{item['title']}]({item['url']})\n"
            md += f"**来源**：{item['author']}\n\n"
            # 注意：analysis 字段由 analyze_leaders.py 生成
            md += item.get('analysis', "*分析生成中...*") + "\n---\n\n"
    
    return markdown.markdown(md, extensions=['extra', 'nl2br'])

def send_email(html_content):
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['From'] = Header("AI 领袖洞察", 'utf-8')
    msg['To'] = Header("你", 'utf-8')
    msg['Subject'] = Header("[AI 领袖洞察] 每日深度日报", 'utf-8')
    
    try:
        # ✅ 使用 Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
        server.sendmail(
            os.getenv('EMAIL_USER'),
            os.getenv('TO_EMAIL'),
            msg.as_string()
        )
        server.quit()
        print("✅ Email sent successfully via Gmail")
    except Exception as e:
        print(f"📧 Email Error: {e}")

def main():
    html = render_html_report()
    send_email(html)

if __name__ == '__main__':
    main()
