# 重庆交通新闻地图

一个可视化展示重庆交通相关新闻的交互式地图应用。

## ✨ 特性

- 🤖 **智能分析** - 自动分类、去重、空间定位
- 🗺️ **多种展示方式** - 点/线/面/网络四种形式
- 🎨 **可交互地图** - Leaflet + OpenStreetMap
- 🔄 **自动更新** - 支持定时抓取

## 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/cappuccinozbc/chongqing-transport-news-map.git

# 进入项目
cd chongqing-transport-news-map

# 运行演示（使用示例数据）
python3 demo_fetch.py

# 或使用MPText API抓取真实数据
export MPTEXT_API_KEY=your_key && python3 demo_fetch.py

# 启动本地服务器
cd output && python3 -m http.server 8000

# 打开浏览器访问
open http://localhost:8000/index.html
```

## 📊 项目结构

```
chongqing-transport-news-map/
├── SKILL.md              # OpenClaw技能文档
├── README.md             # 项目说明文档
├── demo_fetch.py         # 主入口脚本
├── transport_news.json     # 新闻数据库
├── scripts/
│   ├── fetch_news.py      # 抓取工具
│   └── generate_map.py    # 地图生成工具
└── output/
    ├── news_data.geojson  # GeoJSON数据
    └── index.html         # 交互式地图
```

## 📖 在线演示

访问在线演示：https://cappuccinozbc.github.io/chongqing-transport-news-map/

## 📝ser Content Policy

本项目仅供学习和参考使用。
数据来源：重庆交通局、重庆轨道集团等官方渠道。

---

**Created with ❤️ by 小龙虾 & OpenClaw**
