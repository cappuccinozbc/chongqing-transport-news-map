#!/usr/bin/env python3
"""
使用Tavily搜索华龙网最新交通新闻（改进版）
"""

import json
import requests
from datetime import datetime, timedelta

# Tavily API配置
TAVILY_API_KEY = "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"

def search_hualong_latest():
    """搜索华龙网最新新闻（不使用site语法）"""
    print("🔍 使用Tavily搜索华龙网最新交通新闻...")
    
    queries = [
        "成渝中线高铁井口嘉陵江特大桥 site:cqnews.net",
        "重庆交通 高铁 轨道 site:cqnews.net",
        "重庆轨道 轨道交通 site:cqnews.net",
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
            "include_raw_content": True,
            "days": 3,  # 最近3天
            "topic": "news"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if "results" in data:
                results = data["results"]
                print(f"    找到 {len(results)} 条结果")
                
                for result in results:
                    print(f"      - {result.get('title', '')[:60]}")
                    print(f"        时间: {result.get('published_date', '')}")
                    print(f"        URL: {result.get('url', '')}")
                
                all_results.extend(results)
        
        except Exception as e:
            print(f"    ❌ 搜索失败: {e}")
    
    print(f"\n✅ 总共找到 {len(all_results)} 条结果")
    
    # 去重
    seen_urls = set()
    unique_results = []
    for result in all_results:
        url = result.get('url', '')
        if url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(result)
    
    print(f"✅ 去重后: {len(unique_results)} 条")
    return unique_results

def main():
    results = search_hualong_latest()
    
    if results:
        print("\n" + "=" * 60)
        print("详细结果：")
        print("=" * 60)
        
        for i, result in enumerate(results, 1):
            print(f"\n[{i}] {result.get('title', '')}")
            print(f"发布时间: {result.get('published_date', '')}")
            print(f"URL: {result.get('url', '')}")
            print(f"内容: {result.get('content', '')[:200]}...")

if __name__ == "__main__":
    main()
