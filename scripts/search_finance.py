#!/usr/bin/env python3
"""
使用Tavily搜索华龙网重庆金融新闻
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
DATA_FILE = "/root/.openclaw/workspace/skills/chongqing-transport-news-map/finance_news.json"

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
    
    def search_tavily_site(self, site, days=14, max_results=20):
        """使用Tavily搜索指定网站"""
        print(f"🔍 使用Tavily搜索 {site} 的重庆金融新闻...")
        
        if not TAVILY_API_KEY:
            print("❌ TAVILY_API_KEY未设置")
            return []
        
        # 搜索关键词
        queries = [
            "重庆金融",
            "重庆银行",
            "重庆投资",
            "重庆上市",
            "重庆经济",
            "成渝双城经济圈 金融",
            "西部金融中心"
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
                "query": f"{query} site:{site}",
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
        filtered_count = 0
        
        for i, result in enumerate(results):
            title = result.get("title", "")
            content = result.get("content", "") or result.get("snippet", "")
            url = result.get("url", "")
            published_date = result.get("published_date", "")
            
            # 过滤：必须包含金融相关关键词
            finance_keywords = ['金融', '银行', '投资', '上市', '基金', '证券', '保险', '信托', '理财', '经济', '股市', '债券']
            if not any(kw in title or kw in content for kw in finance_keywords):
                filtered_count += 1
                continue
            
            # (可选）过滤掉其他地区的新闻
            china_keywords = ['中国', '全国', '北京', '上海', '深圳', '广州', '香港', '台湾']
            # 注意：这里我们保留重庆相关的，但也可以保留其他地区的重要金融新闻
            
            # 检查重复
            is_dup = self.is_duplicate(title, content)
            if is_dup:
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
                "hash": self._get_content_hash(title, content)
            })
        
        print(f"\n✅ 处理完成: {len(processed)} 条新新闻 (过滤 {filtered_count} 条, 跳过 {duplicate_count} 条重复)")
        return processed
    
    def generate_markdown(self, news_list, site_name):
        """生成飞书文档Markdown"""
        print("\n📄 生成飞书文档...")
        
        md = f"""# 重庆金融新闻整理（{site_name}）

**更新时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**新闻数量：** {len(news_list)} 条
**数据来源：** {site_name} 最近14天的重庆金融相关新闻

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
                "source": "华龙网",
                "url": news["url"],
                "hash": news["hash"],
                "timestamp": datetime.now().isoformat(),
                "publish_time": news["published_date"],
                "category": "金融"
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
    
    def send_to_feishu(self, content):
        """保存到文件供手动发送"""
        output_file = "/tmp/chongqing_finance_news_hualong.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 内容已保存到: {output_file}")
        print("💡 请查看文件内容")
        
        return output_file
    
    def run(self, site="news.cqnews.net", days=14):
        """执行完整流程"""
        print("=" * 60)
        print("重庆金融新闻整理工具（华龙网版）")
        print(f"搜索站点: {site}")
        print(f"抓取范围: 最近 {days} 天")
        print("=" * 60)
        
        # 搜索新闻
        results = self.search_tavily_site(site, days=days)
        
        if not results:
            print("\n⚠️ 没有搜索到新闻")
            return
        
        # 处理结果
        processed = self.process_results(results)
        
        if not processed:
            print("\n⚠️ 没有符合条件的新闻")
            return
        
        # 生成Markdown
        markdown = self.generate_markdown(processed, site)
        
        # 保存到文件
        output_file = self.send_to_feishu(markdown)
        
        # 保存到缓存
        self.save_to_cache(processed)
        
        print("\n" + "=" * 60)
        print("✅ 完成！")
        print(f"📄 Markdown文件: {output_file}")
        print("=" * 60)
        
        return markdown


def main():
    import sys
    
    site = "news.cqnews.net"  # 华龙网
    days = 14
    
    for arg in sys.argv[1:]:
        if arg.startswith("--site="):
            site = arg.split("=")[1]
        elif arg.startswith("--days="):
            days = int(arg.split("=")[1])
    
    processor = NewsProcessor()
    markdown = processor.run(site=site, days=days)
    
    if markdown:
        print("\n" + "=" * 60)
        print("内容预览（前1500字）:")
        print("=" * 60)
        print(markdown[:1500] + "...")


if __name__ == "__main__":
    main()
