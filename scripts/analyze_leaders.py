# scripts/analyze_leaders.py
import os
import json
import sys
from dashscope import Generation

def clean_text(text):
    """清理文本，移除控制字符，确保 API 安全"""
    if not isinstance(text, str):
        text = str(text)
    return ''.join(c for c in text if ord(c) >= 32 or c in '\n\r\t')
...

def analyze_item(title, author):
    prompt = f"""你是一位资深AI与科技趋势分析师，请用中文对以下内容进行深度解读（150字以内）：
标题：{title}
来源：{author}
请严格按以下结构输出（中文）：
1. **核心论点**（≤3条，每条≤50字）
2. **证据链拆解**（技术/数据/逻辑支撑）
3. **历史一致性检验**（与该人物过去观点是否一致？引用具体事件）
4. **产业影响评估**（对AI芯片/模型/应用/监管的影响，分短期<1年、长期>3年）
5. **潜在风险提示**（技术滥用、夸大宣传、逻辑漏洞等）

要求：聚焦技术战略、行业影响或思想洞见，避免客套话。
请严格按照以下格式输出，不要添加任何其他文字：

核心论点：
- 观点1
- 观点2

证据链拆解：
- 证据1
- 证据2

...
"""
    
    try:
        response = Generation.call(
            model="qwen-max",
            prompt=prompt,
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            timeout=30
        )
        if response.status_code == 200:
            return response.output.text.strip()
        else:
            return f"[Qwen API error: {response.code}]"
    except Exception as e:
        return f"[分析异常: {str(e)[:80]}]"

def main():
    input_file = 'output/unified_today.json'
    
    # 检查文件是否存在
    if not os.path.exists(input_file):
        print("⚠️ unified_today.json not found. Skipping analysis.")
        sys.exit(0)
    
    # 读取数据
    with open(input_file, 'r', encoding='utf-8') as f:
        items = json.load(f)
    
    if not items:
        print("📭 No items to analyze.")
        sys.exit(0)
    
    print(f"🧠 Starting analysis for {len(items)} items...")
    
    # 逐个分析
    for i, item in enumerate(items):
        title = item.get('title', '')
        author = item.get('author', '')
        print(f"  {i+1}. Analyzing: {title[:50]}...")
        
        analysis = analyze_item(title, author)
        item['analysis'] = analysis
    
    # 写回文件
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    
    print("✅ Analysis completed and saved.")

if __name__ == '__main__':
    main()
