#!/usr/bin/env python3
"""
从已有新闻数据生成飞书文档格式
"""

import json
from datetime import datetime

# 读取数据
with open("/root/.openclaw/workspace/skills/chongqing-transport-news-map/transport_news.json", 'r', encoding='utf-8') as f:
    data = json.load(f)

news_list = data.get("news", [])

# 生成Markdown
md = f"""# 重庆交通新闻整理

**更新时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**新闻数量：** {len(news_list)} 条
**数据来源：** 最近两周的重庆交通建设、规划、运营相关新闻

---

"""

# 按发布时间排序
sorted_news = sorted(news_list, key=lambda x: x.get("x", ""), reverse=True)

for i, news in enumerate(sorted_news, 1):
    title = news.get("title", "")
    content = news.get("content", "")
    url = news.get("url", "")
    source = news.get("source", "")
    publish_time = news.get("publish_time", "")
    category = news.get("category", "")
    
    # 格式化时间
    try:
        dt = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
        date_str = dt.strftime('%Y-%m-%d %H:%M')
    except:
        date_str = publish_time
    
    md += f"""## {i}. {title}

**发布时间：** {date_str}  
**来源：** {source}  
**分类：** {category}  
**原文链接：** {url}

**内容摘要：**
{content}

---

"""

# 保存到文件
output_file = "/tmp/chongqing_traffic_news.md"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(md)

print(f"✅ Markdown文件已生成: {output_file}")
print(f"📄 总共 {len(news_list)} 条新闻")
print(f"💾 内容已准备，可以发送到飞书文档")

print("\n" + "=" * 60)
print("内容预览（前500字）:")
print("=" * 60)
print(md[:500] + "...")
