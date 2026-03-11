#!/usr/bin/env python3
"""
重庆交通新闻抓取工具（增强版）

功能：
1. 从多个来源抓取重庆交通相关新闻
2. 支持MPText API（微信公众号）
3. 支持政府官网抓取
4. 去重处理
5. 空间定位（地址转坐标）
6. 判断展示方式（点/线/面）
7. 按发布时间排序
"""

import json
import hashlib
import re
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

class TransportNewsFetcher:
    """重庆交通新闻抓取器"""
    
    def __init__(self, storage_file: str = "transport_news.json"):
        self.storage_file = storage_file
        self.news_cache = self._load_cache()
        
        # 政府官网新闻源配置
        self.news_sources = [
            {
                "name": "重庆市交通局",
                "url": "https://jtj.cq.gov.cn/sy_240/tt/index_21.html",
                "base_url": "https://jtj.cq.gov.cn",
                "type": "gov"
            },
            {
                "name": "重庆轨道交通集团",
                "url": "https://www.cqmetro.cn/news/",
                "base_url": "https://www.cqmetro.cn",
                "type": "gov"
            }
        ]
        
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
        # 按发布时间排序（最新的在前）
        self.news_cache["news"] = sorted(
            self.news_cache["news"],
            key=lambda x: x.get("publish_time", ""),
            reverse=True
        )
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
                url: Optional[str] = None,
                publish_time: Optional[str] = None,
                location: Optional[Dict] = None,
                display_type: Optional[str] = None):
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
        
        # 默认发布时间为当前时间
        if not publish_time:
            publish_time = datetime.now().isoformat()
        
        news_item = {
            "title": title,
            "content": content,
            "source": source,
            "url": url,
            "hash": self._get_content_hash(title, content),
            "timestamp": datetime.now().isoformat(),
            "publish_time": publish_time,
            "location": location,
            "display_type": display_type,
            "category": self._infer_category(title, content)
        }
        
        self.news_cache["news"].append(news_item)
        self._save_cache()
        print(f"✅ 添加新闻: {title}")
        return True
    
    def _parse_publish_time(self, time_str: str, base_date: Optional[datetime] = None) -> Optional[str]:
        """
        解析发布时间
        
        支持格式：
        - "2026-03-10"
        - "2026-03-10 14:30"
        - "今天 14:30"
        - "昨天"
        - "3天前"
        """
        if not time_str:
            return None
        
        # 标准格式
        standard_formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M",
            "%Y/%m/%d",
            "%Y/%m/%d %H:%M",
            "%Y年%m月%d日",
        ]
        
        for fmt in standard_formats:
            try:
                dt = datetime.strptime(time_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        # 相对时间
        now = datetime.now()
        if "今天" in time_str:
            return now.date().isoformat()
        elif "昨天" in time_str:
            return (now - timedelta(days=1)).date().isoformat()
        elif "天前" in time_str:
            match = re.search(r'(\d+)天前', time_str)
            if match:
                days = int(match.group(1))
                return (now - timedelta(days=days)).date().isoformat()
        
        # 尝试dateutil解析
        try:
            dt = date_parser.parse(time_str, fuzzy=True)
            return dt.isoformat()
        except:
            return None
    
    def fetch_from_gov_website(self, source_config: Dict, days_back: int = 14) -> List[Dict]:
        """
        从政府官网抓取新闻
        
        Args:
            source_config: 新闻源配置
            days_back: 抓取最近多少天的新闻
        """
        print(f"\n📡 从 {source_config['name']} 抓取新闻...")
        
        url = source_config['url']
        base_url = source_config['base_url']
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_list = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # 通用解析逻辑：查找新闻列表
            # 尝试多种常见的选择器
            selectors = [
                'a[href*="/"]',  # 所有链接
                '.news-list a',
                '.article-list a',
                'li a',
            ]
            
            links = []
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    links = elements[:30]  # 最多30条
                    break
            
            print(f"  找到 {len(links)} 个潜在新闻链接")
            
            for link in links:
                try:
                    title = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    # 过滤：必须有标题且长度合适
                    if not title or len(title) < 10 or len(title) > 100:
                        continue
                    
                    # 过滤：排除导航、页脚等
                    exclude_keywords = ['首页', '导航', '更多', '返回', '登录', '注册']
                    if any(kw in title for kw in exclude_keywords):
                        continue
                    
                    # 构建完整URL
                    if href.startswith('/'):
                        full_url = base_url + href
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue
                    
                    # 过滤：只保留交通相关关键词
                    traffic_keywords = [
                        '交通', '轨道', '地铁', '高铁', '公交',
                        '道路', '高速', '桥梁', '隧道', '建设',
                        '规划', '开通', '运营', '开工', '竣工'
                    ]
                    if not any(kw in title for kw in traffic_keywords):
                        continue
                    
                    print(f"  - {title}")
                    print(f"    URL: {full_url}")
                    
                    # 获取详情页内容
                    detail_data = self._fetch_detail_page(full_url, headers)
                    
                    if detail_data:
                        publish_time = detail_data.get('publish_time')
                        content = detail_data.get('content', title)
                        
                        # 检查发布时间是否在范围内
                        if publish_time:
                            try:
                                pub_dt = datetime.fromisoformat(publish_time)
                                if pub_dt < cutoff_date:
                                    print(f"    ⏭️ 超出时间范围，跳过")
                                    continue
                            except:
                                pass
                        
                        news_list.append({
                            "title": title,
                            "content": content,
                            "source": source_config['name'],
                            "url": full_url,
                            "publish_time": publish_time
                        })
                        
                        # 最多10条
                        if len(news_list) >= 10:
                            break
                    
                except Exception as e:
                    print(f"    ❌ 处理失败: {e}")
                    continue
            
            print(f"✅ 成功抓取 {len(news_list)} 条新闻")
            return news_list
            
        except Exception as e:
            print(f"❌ 抓取失败: {e}")
            return []
    
    def _fetch_detail_page(self, url: str, headers: Dict) -> Optional[Dict]:
        """获取新闻详情页"""
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取正文
            content_selectors = [
                '.article-content',
                '.content',
                '#content',
                '.main-content',
                'article',
            ]
            
            content = None
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(strip=True)[:500]  # 前500字
                    break
            
            # 提取发布时间
            time_selectors = [
                '.publish-time',
                '.time',
                '.date',
                '[class*="time"]',
            ]
            
            publish_time = None
            for selector in time_selectors:
                element = soup.select_one(selector)
                if element:
                    time_str = element.get_text(strip=True)
                    publish_time = self._parse_publish_time(time_str)
                    if publish_time:
                        break
            
            return {
                "content": content,
                "publish_time": publish_time
            }
            
        except Exception as e:
            print(f"    ❌ 详情获取失败: {e}")
            return None
    
    def fetch_from_mptext(self, api_key: str, keyword: str = "重庆交通", days_back: int = 14) -> List[Dict]:
        """
        从MPText API抓取公众号文章
        
        Args:
            api_key: MPText API Key
            keyword: 搜索关键词
            days_back: 抓取最近多少天的文章
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
            
            if "data" in data and isinstance(data["data"], list):
                accounts = data["data"]
                print(f"✅ 找到 {len(accounts)} 个公众号")
                
                news_list = []
                cutoff_date = datetime.now() - timedelta(days=days_back)
                
                for account in accounts:
                    try:
                        account_name = account.get("name", "")
                        account_id = account.get("id", "")
                        
                        print(f"  - {account_name}")
                        
                        # 获取文章列表
                        articles_url = "https://down.mptext.top/api/public/v1/account/messages"
                        articles_params = {
                            "account_id": account_id,
                            "api_key": api_key,
                            "limit": 20
                        }
                        
                        articles_resp = requests.get(articles_url, params=articles_params, timeout=10)
                        articles_data = articles_resp.json()
                        
                        if "data" in articles_data:
                            articles = articles_data["data"]
                            print(f"    找到 {len(articles)} 篇文章")
                            
                            for article in articles:
                                try:
                                    title = article.get("title", "")
                                    content = article.get("content", "")
                                    article_url = article.get("url", "")
                                    pub_time = article.get("publish_time")
                                    
                                    # 检查发布时间
                                    if pub_time:
                                        try:
                                            pub_dt = datetime.fromisoformat(pub_time.replace('Z', '+00:00'))
                                            if pub_dt < cutoff_date:
                                                continue
                                        except:
                                            pass
                                    
                                    news_list.append({
                                        "title": title,
                                        "content": content[:300],
                                        "source": account_name,
                                        "url": article_url,
                                        "publish_time": pub_time
                                    })
                                    
                                except Exception as e:
                                    print(f"      ❌ 文章处理失败: {e}")
                                    continue
                                
                                # 最多10条
                                if len(news_list) >= 10:
                                    break
                            
                            if len(news_list) >= 10:
                                break
                    
                    except Exception as e:
                        print(f"  ❌ 公众号处理失败: {e}")
                        continue
                
                print(f"✅ 总共抓取 {len(news_list)} 条文章")
                return news_list
                
            else:
                print(f"❌ 未知响应格式")
                return []
                
        except Exception as e:
            print(f"❌ 抓取失败: {e}")
            return []
    
    def _infer_display_type(self, content: str) -> str:
        """
        推断展示方式
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
        
        return "point"
    
    def _infer_location(self, title: str, content: str) -> Optional[Dict]:
        """推断位置信息"""
        combined = f"{title} {content}"
        
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
            "观音桥": {"name": "观音桥", "pos": 29.52, "lng": 106.54},
        }
        
        for keyword, loc_info in locations.items():
            if keyword in combined:
                return loc_info
        
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
    
    def fetch_all(self, days_back: int = 14, use_mptext: bool = False):
        """
        从所有来源抓取新闻
        
        Args:
            days_back: 抓取最近多少天的新闻
            use_mptext: 是否使用MPText API
        """
        print("=" * 60)
        print("重庆交通新闻抓取（增强版）")
        print(f"抓时间范围: 最近 {days_back} 天")
        print("=" * 60)
        
        total_count = 0
        
        # 从政府官网抓取
        for source_config in self.news_sources:
            news_list = self.fetch_from_gov_website(source_config, days_back)
            
            for news in news_list:
                self.add_news(
                    title=news["title"],
                    content=news["content"],
                    source=news["source"],
                    url=news["url"],
                    publish_time=news["publish_time"]
                )
            
            total_count += len(news_list)
        
        # 从MPText抓取（如果启用）
        if use_mptext:
            api_key = os.getenv("MPTEXT_API_KEY")
            if api_key:
                news_list = self.fetch_from_mptext(api_key, "重庆交通", days_back)
                
                for news in news_list:
                    self.add_news(
                        title=news["title"],
                        content=news["content"],
                        source=news["source"],
                        url=news["url"],
                        publish_time=news["publish_time"]
                    )
                
                total_count += len(news_list)
            else:
                print("⚠️  MPTEXT_API_KEY 未设置，跳过MPText抓取")
        
        print("\n" + "=" * 60)
        print(f"📊 总共抓取 {total_count} 条新闻")
        print(f"📁 当前共有 {len(self.news_cache['news'])} 条新闻（含历史）")
        print(f"💾 数据已保存到: {self.storage_file}")
        print("=" * 60)


def main():
    """主函数"""
    import sys
    
    days_back = 14
    use_mptext = False
    
    # 解析参数
    for arg in sys.argv[1:]:
        if arg.startswith("--days="):
            days_back = int(arg.split("=")[1])
        elif arg == "--mptext":
            use_mptext = True
    
    fetcher = TransportNewsFetcher()
    fetcher.fetch_all(days_back=days_back, use_mptext=use_mptext)


if __name__ == "__main__":
    main()
