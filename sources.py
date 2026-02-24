# sources.py - 全球科技与投资前沿信源（深度版）

# ======================
# 1. AI 技术领袖（公司官方频道）
# ======================
YOUTUBE_CHANNELS = [
    {"name": "OpenAI", "id": "UC8butISFwT-Wl7EV0hUK0BQ"},
    {"name": "Google DeepMind", "id": "UC9uXsE4oZh8QH6xJp7xUjCw"},
    {"name": "NVIDIA", "id": "UC9vRjuQx5V0Oc0hZ8M_7QjA"},      # 黄仁勋
    {"name": "Tesla", "id": "UC5WjFrtBdufl6gufu7yQr7Q"},       # 马斯克
    {"name": "Lex Fridman Podcast", "id": "UCSHZKyawb77ixDdsGog4iWA"},  # 深度访谈
    {"name": "Yannic Kilcher", "id": "UCZHmQkEvTM7K8FxKVt_koGw"},     # AI 论文解读
]

# ======================
# 2. 关键人物 & 主题关键词（中英双语）
# ======================
YOUTUBE_KEYWORDS = [
    # —— AI 技术领袖 ——
    "Sam Altman", "山姆·奥特曼",
    "Ilya Sutskever", "伊利亚·萨茨克韦弗",
    "Dario Amodei", "达里奥·阿莫迪", "Daniela Amodei",
    "Demis Hassabis", "德米斯·哈萨比斯",
    "Geoffrey Hinton", "杰弗里·辛顿",
    "Yoshua Bengio", "约书亚·本吉奥",
    "Andrej Karpathy", "安德烈·卡帕西",
    "Fei-Fei Li", "李飞飞",
    "Yann LeCun", "杨立昆",

    # —— 硅谷投资人 ——
    "Marc Andreessen", "马克·安德森",
    "Ben Horowitz", "本·霍洛维茨",
    "Peter Thiel", "彼得·蒂尔",
    "Naval Ravikant", "纳瓦尔·拉维坎特",
    "Patrick Collison", "帕特里克·克里森",  # Stripe CEO，常谈技术趋势
    "Elad Gil", "伊拉德·吉尔",              # 《High Growth Handbook》作者

    # —— 新兴力量 ——
    "Elon Musk", "马斯克", "xAI",
    "Jensen Huang", "黄仁勋", "Blackwell",
    "Satya Nadella", "萨提亚·纳德拉",

    # —— 主题关键词 ——
    "AGI roadmap", "AI safety", "frontier model",
    "AI investment", "venture capital 2026",
    "AI chip", "quantum computing", "neural interface",
    "open source AI", "sovereign AI",
    "AI regulation", "compute cluster"
]

# ======================
# 3. 高价值 RSS 博客/播客（一手思想）
# ======================
RSS_FEEDS = [
    # —— 投资机构博客 ——
    "https://a16z.com/feed/",                 # a16z（AI、生物科技、加密）
    "https://www.sequoiacap.com/articles/feed/",  # 红杉资本（全球科技趋势）
    "https://blog.ycombinator.com/rss/",      # YC（初创公司洞察）
    "https://eladgil.com/blog?format=rss",    # Elad Gil（前 Google/Stripe，投资策略）

    # —— 技术领袖博客 ——
    "https://karpathy.ai/feed.xml",           # Andrej Karpathy
    "https://deepmind.google/blog/rss/",
    "https://openai.com/blog/rss/",
    "https://www.anthropic.com/news/rss.xml",

    # —— 思想者播客/文章 ——
    "https://naval.com/feed.xml",             # Naval 的人生与投资哲学
    "https://samaltman.com/rss.xml",          # Sam Altman 个人博客
    "https://patrickcollison.com/feed",       # Patrick Collison（技术史与未来）
    "https://fs.blog/feed/",                  # Farnam Street（思维模型）
]
