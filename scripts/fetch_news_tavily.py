#!/usr/bin/env python3
"""
使用Tavily搜索重庆交通新闻并整理到飞书文档（调试版）
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
    
    def search_tavily_news(self, days=14, max_results=20):
        """使用Tavily搜索新闻"""
        print("🔍 使用Tavily搜索重庆交通新闻...")
        
        if not TAVILY_API_KEY:
            print("❌ TAVILY_API_KEY未设置")
            return []
        
        # 搜索关键词
        queries = [
            "重庆交通建设",
            "重庆轨道交通",
            "重庆高速道路",
            "重庆交通规划"
        ]
        
        all_results = []
        
        for query in queries:
            print(f"  搜索: {query}")
            
            url = "https://api.tavily.com/search"
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",
                "max_results": 10,
                "include_raw_content": False,
                "topic": "news"
            }
            
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                print(f"    响应keys: {list(data.keys())}")
                
                if "results" in data:
                    results = data["results"]
                    print(f"    找到 {len(results)} 条结果")
                    
                    # 显示第一条的内容作为调试
                    if results:
                        print(f"    第一条: {results[0].get('title', '')[:60]}...")
                    
                    all_results.extend(results)
                
            except Exception as e:
                print(f"    ❌ 搜索失败: {e}")
        
        print(f"✅ 总共找到 {len(all_results)} 条结果")
        return all_results
    
    def process_results(self, results):
        """处理搜索结果，去重并格式化"""
        print("\n📝 处理搜索结果...")
        
        processed = []
        duplicate_count = 0
        
        for i, result in enumerate(results):
            title = result.get("title", "")
            content = result.get("content", "") or result.get("snippet", "")
            url = result.get("url", "")
            published_date = result.get("published_date", "")
            
            print(f"\n[{i+1}] 处理结果:")
            print(f"  标题: {title[:60]}...")
            print(f"  内容: {content[:60]}...")
            print(f"  URL: {url[:60]}...")
            print(f"  时间: {published_date}")
            
            # 过滤：必须包含交通相关关键词
            traffic_keywords = ['交通', '轨道', '地铁', '高铁', '公交', '道路', '高速', '桥梁', '隧道']
            has_traffic_keyword = any(kw in title or kw in content for kw in traffic_keywords)
            print(f"  交通关键词: {'✅' if has_traffic_keyword else '❌'}")
            
            if not has_traffic_keyword:
                print(f"  ⏭️ 跳过：不包含交通关键词")
                continue
            
            # 检查重复
            is_dup = self.is_duplicate(title, content)
            if is_dup:
                duplicate_count += 1
                print(f"  ⚠️ 跳过重复")
            else:
                print(f"  ✅ 添加")
            
            # 格式化发布时间
            if not published_date:
                published_date = datetime.now().isoformat()
            
            processed.append({
                "title": title,
                "content": content[:500],
                "url": url,
                "published_date": published_date,
                "hash": self._get_content_hash(title, content)
            })
        
        print(f"\n✅ 处理完成: {len(processed)} 条新新闻 (跳过 {duplicate_count} 条重复)")
        return processed
    
    def generate_markdown(self, news_list):
        """生成飞书文档Markdown"""
        print("\n📄 生成飞书文档...")
        
        md = f"""# 重庆交通新闻整理

**更新时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**新闻数量：** {len(news_list)} 条

---

"""
        
        # 按发布时间排序（最新的在前）
        sorted_news = sorted(news_list, key=lambda x: x.get("published_date", ""), reverse=True)
        
        for i, news in enumerate(sorted_news, 1):
            title = news.get("title", "")
            content = news.get("content", "")
            url = news.get("url", "")
            published_date = news.get("published_date", "")
            
            # 格式化时间
            try:
                dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                date_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                date_str = published_date
            
            md += f"""## {i}. {title}

**发布时间：** {date_str}
  
**来源链接：** {url}

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
                "source": "Tavily搜索",
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
    
    def send_to_feishu(self, content):
        """保存到文件供手动发送"""
        output_file = "/tmp/chongqing_traffic_news_tavily.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 内容已保存到: {output_file}")
        print("💡 请查看文件内容，或让我发送到飞书文档")
        
        return output_file
    
    def run(self, days=14):
        """执行完整流程"""
        print("=" * 60)
        print("重庆交通新闻整理工具（Tavily版）")
        print(f"抓取范围: 最近 {days} 天")
        print("=" * 60)
        
        # 搜索新闻
        results = self.search_tavily_news(days=days)
        
        if not results:
            print("\n⚠️ 没有搜索到新闻")
            return
        
        # 处理结果
        processed = self.process_results(results)
        
        if not processed:
            print("\n⚠️ 没有符合条件的新闻")
            return
        
        # 生成Markdown
        markdown = self.generate_markdown(processed)
        
        # 保存到文件
        output_file = self.send_to_feishu(markdown)
        
        # 保存到缓存
        self.save_to_cache(processed)
        
        print("\n" + "=" * 60)
        print("✅ 完成！")
        print(f"📄 Markdown文件: {output_file}")
        print("=" * 60)


def main():
    processor = NewsProcessor()
    processor.run(days=14)


if __name__ == "__main__":
    main()
