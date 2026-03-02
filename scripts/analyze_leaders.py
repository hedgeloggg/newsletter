# scripts/analyze_leaders.py
import os
import json
from dashscope import Generation
from transcribe_video import get_transcript

def analyze_video(title, author, transcript):
    prompt = f"""你是一位顶级科技产业分析师。请对以下视频内容进行深度拆解：

【视频标题】{title}
【主讲人】{author}
【全文转录】{transcript}

请严格按以下结构输出（中文）：
1. **核心论点**（≤3条，每条≤50字）
2. **证据链拆解**（技术/数据/逻辑支撑）
3. **历史一致性检验**（与该人物过去观点是否一致？引用具体事件）
4. **产业影响评估**（对AI芯片/模型/应用/监管的影响，分短期<1年、长期>3年）
5. **潜在风险提示**（技术滥用、夸大宣传、逻辑漏洞等）

要求：避免套话，用 bullet points，保持专业冷静。
"""
    response = Generation.call(
        model='qwen-max-2026-01-23',
        prompt=prompt,
        api_key=os.getenv('DASHSCOPE_API_KEY'),
        max_tokens=2000,
        temperature=0.3
    )
    return response.output.text.strip()

def main():
    with open('output/today_videos.json') as f:
        videos = json.load(f)
    
    results = []
    for video in videos:
        print(f"Analyzing: {video['title']}")
        transcript = get_transcript(video['video_id'])
        analysis = analyze_video(video['title'], video['author'], transcript)
        
        results.append({
            'title': video['title'],
            'url': video['url'],
            'author': video['author'],
            'analysis': analysis
        })
    
    with open('output/analysis_results.json', 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("✅ Analysis completed")

if __name__ == '__main__':
    main()
