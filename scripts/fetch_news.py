#!/usr/bin/env python3
"""
重庆交通新闻抓取工具

功能：
1. 从多个来源抓取重庆交通相关新闻
2. (预留) 从MPText API抓取公众号文章
3. 去重处理
4. 空间定位（地址转坐标）
5. 判断展示方式（点/线/面）
"""

import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
import requests

class TransportNewsFetcher:
    """重庆交通新闻抓取器"""
    
    def __init__(self, storage_file: str = "transport_news.json"):
        self.storage_file = storage_file
        self.news_cache = self._load_cache()
        
    def _load_cache(self) -> Dict:
        """加载已存储的新闻"""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"news": [], "last_update": None}
    
    def _save_cache(self):
        """保存新闻到缓存"""
        self.news_cache["last_update"] = datetime.now().isoformat()
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(self.news_cache, f, ensure_ascii=False, indent=2)
    
    def _get_content_hash(self, title: str, content: str) -> str:
        """生成内容哈希用于去重"""
        combined = f"{title}_{content}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()
    
    def is_duplicate(self, title: str, content: str) -> bool:
        """检查是否重复"""
        content_hash = self._get_content_hash(title, content)
        existing_hashes = [n.get("hash") for n in self.news_cache.get("news", [])]
        return content_hash in existing_hashes
    
    def add_news(self, title: str, content: str, source: str, 
                location: Optional[Dict] = None, display_type: Optional[str] = None):
        """添加新闻，自动去重"""
        
        # 检查重复
        if self.is_duplicate(title, content):
            print(f"⚠️  跳过重复新闻: {title[:50]}...")
            return False
        
        # 判断展示方式（如果未指定）
        if not display_type:
            display_type = self._infer_display_type(content)
        
        # 判断空间位置（如果未指定）
        if not location:
            location = self._infer_location(title, content)
        
        news_item = {
            "title": title,
            "content": content,
            "source": source,
            "hash": self._get_content_hash(title, content),
            "timestamp": datetime.now().isoformat(),
            "location": location,
            "display_type": display_type,
            "category": self._infer_category(title, content)
        }
        
        self.news_cache["news"].insert(0, news_item)
        self._save_cache()
        print(f"✅ 添加新闻: {title}")
        return True
    
    def _infer_display_type(self, content: str) -> str:
        """
        推断展示方式
        
        返回值：
        - "point": 点状（单个地点）
        - "line": 线状（道路、线路）
        - "area": 面状（区域、片区）
        - "network": 网络（多个关联地点）
        """
        content_lower = content.lower()
        
        # 线状关键词
        line_keywords = ["道路", "高速", "轨道", "线路", "公路", "桥梁", "隧道", 
                      "通道", "走廊", "道路改扩建", "连通", "延伸"]
        if any(kw in content_lower for kw in line_keywords):
            return "line"
        
        # 面状关键词
        area_keywords = ["区域", "片区", "区域", "新城", "开发区", "片区规划", 
                     "整体", "片区建设", "覆盖范围"]
        if any(kw in content_lower for kw in area_keywords):
            return "area"
        
        # 网络关键词
        network_keywords = ["网络", "枢纽", "体系", "综合", "多站点", 
                       "多线路", "串联", "多区域连接"]
        if any(kw in content_lower for kw in network_keywords):
            return "network"
        
        # 默认为点状
        return "point"
    
    def _infer_location(self, title: str, content: str) -> Optional[Dict]:
        """
        推断位置信息
        
        尝试从标题和内容中提取地址信息
        """
        combined = f"{title} {content}"
        
        # 常见重庆地点关键词
        locations = {
            "渝中": {"name": "渝中区", "lat": 29.55, "lng": 106.56},
            "渝北": {"name": "渝北区", "lat": 29.82, "lng": 106.51},
            "渝南": {"name": "渝南区", "lat": 29.52, "lng": 106.58},
            "巴南": {"name": "巴南区", "lat": 29.43, "lng": 106.52},
            "南岸": {"name": "南岸区", "lat": 29.53, "lng": 106.57},
            "江北": {"name": "江北区", "lat": 29.79, "lng": 106.56},
            "沙坪坝": {"name": "沙坪坝区", "lat": 29.56, "lng": 106.45},
            "九龙坡": {"name": "九龙坡区", "lat": 29.51, "lng": 106.52},
            "大渡口": {"name": "大渡口区", "lat": 29.49, "lng": 106.48},
            "两江新区": {"name": "两江新区", "lat": 29.68, "lng": 106.63},
            "西部科学城": {"name": "西部科学城", "lat": 29.70, "lng": 106.20},
            "高新区": {"name": "高新区", "lat": 29.62, "lng": 106.47},
            "茶园": {"name": "茶园", "lat": 29.57, "lng": 106.62},
            "龙洲湾": {"name": "龙洲湾", "lat": 29.61, "lng": 106.58},
            "礼嘉": {"name": "礼嘉", "lat": 29.68, "lng": 106.55},
            "解放碑": {"name": "解放碑", "lat": 29.56, "lng": 106.58},
            "观音桥": {"name": "观音桥", "lat": 29.52, "lng": 106.54},
        }
        
        for keyword, loc_info in locations.items():
            if keyword in combined:
                return loc_info
        
        # 未找到具体位置
        return {"name": "重庆主城区", "lat": 29.56, "lng": 106.55}
    
    def _infer_category(self, title: str, content: str) -> str:
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
    
    def fetch_from_mptext(self, api_key: str, keyword: str = "重庆交通") -> List[Dict]:
        """
        从MPText API抓取公众号文章
        
        注意：需要有效的API Key
        """
        print(f"\n📡 从MPText API搜索: {keyword}")
        
        url = "https://down.mptext.top/api/public/v1/account"
        params = {
            "keyword": keyword,
            "api_key": api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.text.strip().startswith('<!DOCTYPE'):
                print("⚠️  返回HTML，可能认证失败或被保护")
                return []
            
            data = response.json()
            
            # 检查响应结构
            if "data" in data and isinstance(data["data"], list):
                print(f"✅ 找到 {len(data['data'])} 个公众号")
                return data["data"]
            elif "base_resp" in data:
                error_msg = data["base_resp"].get("err_msg", "未知错误")
                print(f"❌ API错误: {error_msg}")
                return []
            else:
                print(f"❌ 未知响应格式: {data}")
                return []
                
        except Exception as e:
            print(f"❌ 抓取失败: {e}")
            return []
    
    def fetch_from_web(self, urls: List[str]) -> List[Dict]:
        """
        从网页抓取新闻（预留功能）
        """
        print(f"\n📡 从网页抓取 {len(urls)} 个来源")
        news_list = []
        
        for url in urls:
            try:
                print(f"  抓取: {url}")
                response = requests.get(url, timeout=10)
                # TODO: 实现具体的网页解析逻辑
            except Exception as e:
                print(f"  ❌ 失败: {e}")
        
        return news_list


def main():
    """主函数 - 演示用法"""
    print("=" * 50)
    print("重庆交通新闻抓取工具")
    print("=" * 50)
    
    fetcher = TransportNewsFetcher()
    
    # 示例：手动添加新闻
    example_news = [
        {
            "title": "重庆轨道交通24号线一期工程开工",
            "content": "重庆轨道交通24号线一期工程正式开工建设，线路全长约45公里，"
                       "起于鹿栖站，止于广阳北站，共设车站15座。",
            "source": "重庆轨道交通集团"
        },
        {
            "title": "渝遂高速重庆段通车",
            "content": "渝遂高速重庆段正式通车，线路全长约120公里，"
                       "大大缩短了重庆至遂宁的通行时间。",
            "source": "重庆交通开投集团"
        }
    ]
    
    print("\n📝 示例：添加新闻\n")
    for news in example_news:
        fetcher.add_news(
            title=news["title"],
            content=news["content"],
            source=news["source"]
        )
    
    print(f"\n📊 当前共有 {len(fetcher.news_cache['news'])} 条新闻")
    print(f"💾 数据已保存到: {fetcher.storage_file}")


if __name__ == "__main__":
    main()
