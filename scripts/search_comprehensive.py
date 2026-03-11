#!/usr/bin/env python3
"""
使用Tavily搜索最近两周重庆交通新闻（多源综合版）
"""

import json
import hashlib
import requests
from datetime import datetime, timedelta
import os
import re

# Tavily API配置
TAVILY_API_KEY = "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"

# 数据文件
DATA_FILE = "/root/.openclaw/workspace/skills/chongqing-transport-news-map/transport_news.json"

class NewsProcessor:
    def __init__(self):
        self.existing_news = self._load_existing_news()
        
    def _load_existing_news(self):
        """加载已有新闻用于去重"""
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("news", [])
        except:
            return []
    
    def _get_content_hash(self, title, content):
        """生成内容哈希"""
        combined = f"{title}_{content[:200]}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()
    
    def is_duplicate(self, title, content):
        """检查是否重复"""
        content_hash = self._get_content_hash(title, content)
        existing_hashes = [n.get("hash") for n in self.existing_news]
        return content_hash in existing_hashes
    
    def search_multi_sources(self, days=14):
        """从多个来源搜索新闻"""
        print("🔍 从多个来源搜索重庆交通新闻...")
        
        # 搜索来源配置
        sources = [
            {
                "name": "华龙网",
                "queries": [
                    "重庆交通",
                    "成渝中线高铁",
                    "重庆轨道交通",
                    "重庆高速"
                ],
                "site": "cqnews.net"
            },
            {
                "name": "重庆交通局",
                "queries": [
                    "重庆交通建设",
                    "重庆交通规划"
                ],
                "site": "jtj.cq.gov.cn"
            },
            {
                "name": "重庆轨道交通",
                "queries": [
                    "重庆轨道",
                    "重庆地铁"
                ],
                "site": "cqmetro.cn"
            }
        ]
        
        all_results = []
        
        for source in sources:
            print(f"\n📡 搜索 {source['name']}...")
            
            for query in source['queries']:
                print(f"  查询: {query}")
                
                url = "https://api.tavily.com/search"
                headers = {
                    "Content-Type": "application/json"
                }
                
                # 构建搜索查询
                search_query = f"{query}"
                if source['site']:
                    search_query += f" site:{source['site']}"
                
                payload = {
                    "api_key": TAVILY_API_KEY,
                    "query": search_query,
                    "search_depth": "basic",
                    "max_results": 10,
                    "include_raw_content": True,
                    "days": days,
                    "topic": "news"
                }
                
                try:
                    response = requests.post(url, json=payload, headers=headers, timeout=15)
                    response.raise_for_status()
                    data = response.json()
                    
                    if "results" in data:
                        results = data["results"]
                        print(f"    找到 {len(results)} 条结果")
                        
                        # 添加来源标识
                        for result in results:
                            result['_source'] = source['name']
                        
                        all_results.extend(results)
                
                except Exception as e:
                    print(f"    ❌ 搜索失败: {e}")
        
        print(f"\n✅ 总共找到 {len(all_results)} 条结果")
        return all_results
    
    def process_results(self, results):
        """处理搜索结果，去重并格式化"""
        print("\n📝 处理搜索结果...")
        
        processed = []
        duplicate_count = 0
        filtered_count = 0
        
        for i, result in enumerate(results):
            title = result.get("title", "")
            content = result.get("content", "") or result.get("snippet", "")
            url = result.get("url", "")
            published_date = result.get("published_date", "")
            source_name = result.get("_source", "未知来源")
            
            # 过滤：必须包含交通相关关键词
            traffic_keywords = ['交通', '轨道', '地铁', '高铁', '公交', '道路', '高速', '桥梁', '隧道', '建设', '规划', '运营', '开通', '开工']
            if not any(kw in title or kw in content for kw in traffic_keywords):
                filtered_count += 1
                continue
            
            # 检查重复
            if self.is_duplicate(title, content):
                duplicate_count += 1
                print(f"  ⚠️ [{i+1}] 跳过重复: {title[:50]}...")
                continue
            
            # 格式化发布时间
            if not published_date:
                published_date = datetime.now().isoformat()
            
            print(f"  ✅ [{i+1}] 添加: {title[:50]}...")
            
            processed.append({
                "title": title,
                "content": content[:500],
                "url": url,
                "published_date": published_date,
                "source": source_name,
                "hash": self._get_content_hash(title, content)
            })
        
        print(f"\n✅ 处理完成: {len(processed)} 条新新闻 (过滤 {filtered_count} 条, 跳过 {duplicate_count} 条重复)")
        return processed
    
    def generate_markdown(self, news_list):
        """生成飞书文档Markdown"""
        print("\n📄 生成飞书文档...")
        
        # 统计各来源新闻数量
        source_count = {}
        for news in news_list:
            source = news.get("source", "其他")
            source_count[source] = source_count.get(source, 0) + 1
        
        md = f"""# 重庆交通新闻整理

**更新时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**新闻数量：** {len(news_list)} 条
**数据来源：** 最近14天的重庆交通建设、规划、运营相关新闻

---

## 📊 来源统计

"""
        
        for source, count in sorted(source_count.items(), key=lambda x: x[1], reverse=True):
            md += f"- **{source}**：{count} 条\n"
        
        md += "\n---\n\n"
        
        # 按发布时间排序（最新的在前）
        sorted_news = sorted(news_list, key=lambda x: x.get("published_date", ""), reverse=True)
        
        for i, news in enumerate(sorted_news, 1):
            title = news.get("title", "")
            content = news.get("content", "")
            url = news.get("url", "")
            published_date = news.get("published_date", "")
            source = news.get("source", "")
            
            # 格式化时间
            try:
                dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                date_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                date_str = published_date
            
            md += f"""## {i}. {title}

**发布时间：** {date_str}
**来源：** {source}
**原文链接：** {url}

**内容摘要：**
{content}

---

"""
        
        return md
    
    def save_to_cache(self, news_list):
        """保存到缓存文件"""
        print("\n💾 保存到缓存文件...")
        
        # 添加到现有新闻列表
        for news in news_list:
            news_item = {
                "title": news["title"],
                "content": news["content"],
                "source": news["source"],
                "url": news["url"],
                "hash": news["hash"],
                "timestamp": datetime.now().isoformat(),
                "publish_time": news["published_date"],
                "location": {"name": "重庆主城区", "lat": 29.56, "lng": 106.55},
                "display_type": "line",
                "category": self._infer_category(news["title"], news["content"])
            }
            self.existing_news.insert(0, news_item)
        
        # 保存到文件
        data = {
            "news": self.existing_news,
            "last_update": datetime.now().isoformat()
        }
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已保存 {len(news_list)} 条新闻到缓存")
    
    def _infer_category(self, title, content):
        """推断新闻分类"""
        combined = f"{title} {content}".lower()
        
        if any(kw in combined for kw in ["建设", "开工", "竣工", "投用"]):
            return "建设"
        elif any(kw in combined for kw in ["规划", "设计", "方案"]):
            return "规划"
        elif any(kw in combined for kw in ["运营", "开通", "运行", "调整"]):
            return "运营"
        else:
            return "其他"
    
    def run(self, days=14):
        """执行完整流程"""
        print("=" * 60)
        print("重庆交通新闻整理工具（多源综合版）")
        print(f"抓取范围: 最近 {days} 天")
        print("=" * 60)
        
        # 搜索新闻
        results = self.search_multi_sources(days=days)
        
        if not results:
            print("\n⚠️ 没有搜索到新闻")
            return None
        
        # 处理结果
        processed = self.process_results(results)
        
        if not processed:
            print("\n⚠️ 没有符合条件的新新闻")
            return None
        
        # 生成Markdown
        markdown = self.generate_markdown(processed)
        
        # 保存到文件
        output_file = "/tmp/chongqing_traffic_news_comprehensive.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown)
        print(f"✅ Markdown已保存到: {output_file}")
        
        # 保存到缓存
        self.save_to_cache(processed)
        
        print("\n" + "=" * 60)
        print("✅ 完成！")
        print(f"📄 Markdown文件: {output_file}")
        print("=" * 60)
        
        return markdown


def main():
    import sys
    
    days = 14
    for arg in sys.argv[1:]:
        if arg.startswith("--days="):
            days = int(arg.split("=")[1])
    
    processor = NewsProcessor()
    markdown = processor.run(days=days)
    
    if markdown:
        print("\n" + "=" * 60)
        print("内容预览（前1500字）:")
        print("=" * 60)
        print(markdown[:1500] + "...")


if __name__ == "__main__":
    main()
