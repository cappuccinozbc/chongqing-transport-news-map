#!/usr/bin/env python3
"""
演示：从MPText API抓取重庆交通相关文章
"""

import sys
import os

# 添加技能目录到Python路径
skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, skill_dir)

from scripts.fetch_news import TransportNewsFetcher


def main():
    print("=" * 60)
    print("重庆交通新闻地图 - 演示脚本")
    print("=" * 60)
    
    # 获取API Key
    api_key = os.getenv("MPTEXT_API_KEY")
    
    if not api_key:
        print("\n⚠️  未设置 MPTEXT_API_KEY 环境变量")
        print("\n请设置API Key后重新运行：")
        print("export MPTEXT_API_KEY=your_api_key")
        print("python3 demo_fetch.py")
        
        print("\n将使用示例数据演示...")
        demo_with_sample_data()
        return
    
    print(f"\n🔑 API Key: {api_key[:10]}...")
    
    # 创建抓取器
    fetcher = TransportNewsFetcher()
    
    # 从MPText API抓取
    print("\n📡 从MPText API抓取重庆交通相关文章...")
    articles = fetcher.fetch_from_mptext(api_key, "重庆交通")
    
    if not articles:
        print("\n❌ 未获取到文章")
        print("\n尝试使用示例数据演示...")
        demo_with_sample_data()
        return
    
    print(f"\n✅ 成功获取到 {len(articles)} 条文章")
    
    # 处理文章数据
    print("\n📝 处理文章数据...")
    for i, article in enumerate(articles[:5], 1):  # 只处理前5条作为演示
        # 提取文章信息（MPText API返回的结构可能不同，这里做适配）
        # 假设返回格式：{title, content, account_name} 或类似结构
        
        # 适配不同可能的API响应格式
        if isinstance(article, dict):
            title = article.get("title") or article.get("name") or "未知标题"
            content = article.get("content") or article.get("description") or article.get("introduction") or ""
            source = article.get("account_name") or article.get("account") or "MPText"
        else:
            title = str(article)[:50]
            content = ""
            source = "MPText"
        
        print(f"\n[{i}] {title}")
        print(f"    来源: {source}")
        
        # 添加到数据库
        fetcher.add_news(
            title=title,
            content=content,
            source=source
        )
    
    # 统计
    print(f"\n📊 数据库中共有 {len(fetcher.news_cache['news'])} 条新闻")
    
    # 生成地图
    print("\n🗺️ 生成地图...")
    from scripts.generate_map import MapGenerator
    
    generator = MapGenerator()
    generator.generate()
    
    print("\n" + "=" * 60)
    print("✅ 完成！")
    print("=" * 60)
    print(f"\n💾 数据文件: transport_news.json")
    print(f"🌐 地图文件: output/index.html")
    print(f"\n打开地图访问: file://{os.path.abspath('output/index.html')}")


def demo_with_sample_data():
    """使用示例数据演示"""
    from scripts.fetch_news import TransportNewsFetcher
    
    fetcher = TransportNewsFetcher()
    
    # 添加示例新闻
    sample_news = [
        {
            "title": "重庆轨道交通24号线一期工程正式开工",
            "content": "重庆轨道交通24号线一期工程正式开工建设，线路全长约45公里，起于鹿栖站，"
                       "止于广阳北站，共设车站15座。该线路将有效连接重庆西部科学城与主城区。",
            "source": "重庆轨道交通集团"
        },
        {
            "title": "渝遂高速重庆段顺利通车",
            "content": "渝遂高速重庆段正式通车，线路全长约120公里，设计时速100公里，"
                       "大大缩短了重庆至遂宁的通行时间，进一步完善了川东地区高速路网。",
            "source": "重庆交通开投集团"
        },
        {
            "title": "重庆东站正式投用运营",
            "content": "重庆东站正式投用运营，站房面积约12万平方米，"
                       "设置有12个站台，最高可同时容纳约3万名旅客。该站将成为成渝地区重要的铁路枢纽。",
            "source": "中国铁路成都局"
        },
        {
            "title": "两江新区龙洲湾大桥工程建设中",
            "content": "两江新区龙洲湾大桥建设正在积极推进中，桥梁全长约1.5公里，"
                       "设计时速80公里。该桥建成后将有效改善龙洲湾片区的交通条件。",
            "source": "两江新区管委会"
        },
        {
            "title": "重庆轨道全网运营里程突破575公里",
            "content": "截至目前，重庆轨道交通已开通运营线路14条，运营里程达575公里，"
                       "覆盖主城都市区主要区域。日均客运量约430万人次。",
            "source": "重庆轨道交通集团"
        }
    ]
    
    for news in sample_news:
        fetcher.add_news(
            title=news["title"],
            content=news["content"],
            source=news["source"]
        )
    
    print(f"✅ 已添加 {len(sample_news)} 条示例新闻")
    
    # 生成地图
    from scripts.generate_map import MapGenerator
    generator = MapGenerator()
    generator.generate()
    
    print("\n" + "=" * 60)
    print("✅ 演示完成！")
    print("=" * 60)
    print(f"\n💾 数据文件: transport_news.json")
    print(f"🌐 地图文件: output/index.html")
    print(f"\n打开地图访问: file://{os.path.abspath('output/index.html')}")


if __name__ == "__main__":
    main()
