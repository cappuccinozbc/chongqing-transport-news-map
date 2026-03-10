---
name: chongqing-transport-news-map
description: 重庆交通新闻地图项目。定期抓取重庆交通相关新闻（建设、规划、运营），自动去重、空间定位，生成可视化地图（支持点/线/面/网络多种展示方式）。
---

# 重庆交通新闻地图

创建一个动态更新的重庆交通新闻地图网站，展示重庆交通建设规划、运行、运营相关的新闻。

## 🎯 核心功能

1. **自动抓取新闻** - 支持多来源（MPText API、网页抓取）
2. **智能去重** - 基于内容哈希，避免重复新闻
3. **空间定位** - 从标题和内容推经纬度坐标
4. **展示方式判断** - 自动识别并标记：
   - 📍 **点状**（Point）：单个地点（车站、站点）
   - 📏 **线状**（Line）：道路、线路、高速
   - ⬛ **面状**（Area）：区域、片区、新城
   - 🔗 **网络**（Network）：多线路连接、枢纽网络
5. **分类识别** - 自动判断：
   - 🏗 **建设**：开工、竣工、投用
   - 📋 **规划**：规划、设计、方案
   - 🚇 **运营**：开通、运行、调整

## 📂 项目结构

```
chongqing-transport-news-map/
├── SKILL.md                    # 使用说明
├── scripts/
│   ├── fetch_news.py         # 新闻抓取工具
│   └── generate_map.py      # 地图生成工具
├── references/                # (可选) 配置和参考文档
└── output/                   # 生成输出
    ├── transport_news.json    # 新闻数据（含去重）
    ├── news_data.geojson    # Geo地图数据
    └── index.html           # 可交互式地图
```

## 🚀 快速开始

### 1. 抓取新闻

```bash
# 方式1：手动添加示例新闻（测试）
python3 {baseDir}/scripts/fetch_news.py

# 方式2：从MPText API抓取（需要API Key）
export MPTEXT_API_KEY=your_api_key
python3 {baseDir}/scripts/fetch_news.py --mptext "重庆交通"
```

**输出文件：** `transport_news.json`

**数据结构：**
```json
{
  "news": [
    {
      "title": "新闻标题",
      "content": "新闻内容",
      "source": "来源",
      "hash": "内容哈希（去重用）",
      "timestamp": "时间戳",
      "location": {
        "name": "地点名称",
        "lat": 纬度,
        "lng": 经度
      },
      "display_type": "展示方式（point/line/area/network）",
      "category": "分类（建设/规划/运营/其他）"
    }
  ],
  "last_update": "最后更新时间"
}
```

### 2. 生成地图

```bash
python3 {baseDir}/scripts/generate_map.py
```

**输出文件：**
- `output/news_data.geojson` - GeoJSON格式（GIS工具可用）
- `output/index/index.html` - 交互式地图（浏览器打开）

## 🧠️ 空间定位规则

脚本内置重庆常见地点坐标库：

| 地点 | 纬度 | 经度 |
|------|--------|--------|
| 渝中区 | 29.55 | 106.56 |
| 渝北区 | 29.82 | 106.51 |
| 渝南区 | 29.52 | 106.58 |
| 江北区 | 29.79 | 106.56 |
| 沙坪坝 | 29.56 | 106.45 |
| 两江新区 | 29.68 | 106.63 |
| 解放碑 | 29.56 | 106.58 |
| 观音桥 | 29.52 | 106.54 |
| ... | ... | ... |

**未识别地点**：默认定位到 `重庆主城区 (29.56, 106.55)`

如需添加更多地点，编辑 `scripts/fetch_news.py` 的 `_infer_location()` 方法。

## 🎨 展示方式判断规则

基于新闻内容关键词自动判断：

### 线状（LineString）
**关键词：** 道路、高速、轨道、线路、公路、走廊、通道、连通

**展示：** 以中心点为基准，向四周延伸的线段

### 面状（Polygon）
**关键词：** 区域、片区、新城、开发区、覆盖范围

**展示：** 以中心点为基准的矩形区域

### 网络（MultiLineString）
**关键词：** 网络、枢纽、体系、综合、多站点、多线路、串联

**展示：** 多条连接线，形成网络结构

### 点状（Point）- 默认
**展示：** 圆形标记，大小根据类型调整

## 🔄 自动化工作流

设置定期任务（使用cron）实现每天自动更新：

```bash
# 每天凌晨2点抓取新闻
0 2 * * * openclaw cron add --json '{
  "name": "transport-news-fetcher",
  "schedule": {"kind": "cron", "expr": "0 2 * * *", "tz": "Asia/Shanghai"},
  "payload": {
    "kind": "agentTurn",
    "message": "抓取重庆交通新闻并更新地图"
  },
  "sessionTarget": "isolated",
  "enabled": true
}'
```

## 📝 扩展功能

### 集成MPText API

获取 `MPTEXT_API_KEY` 后，可从"重庆交通"公众号抓取最新文章：

```python
# 编辑fetch_news.py添加：
api_key = os.getenv("MPTEXT_API_KEY")
if api_key:
    articles = fetcher.fetch_from_mptext(api_key, "重庆交通")
    for article in articles:
        fetcher.add_news(
            title=article["title"],
            content=article["content"],
            source=article["account_name"]
        )
```

### 添加数据源

在 `fetch_news.py` 的 `fetch_from_web()` 方法中添加更多新闻源：

```python
urls = [
    "https://jtj.cq.gov.cn/sy_240/tt/index_21.html",  # 重庆交通局
    "https://www.cqmetro.cn/",                      # 重庆轨道集团
    # 添加更多...
]
```

### Web应用部署

将 `output/index.html` 部署到Web服务器：

```bash
# 使用Python简单服务器
cd output && python3 -m http.server 8000

# 访问
open http://localhost:8000
```

或使用nginx、Nginx、Vercel等部署。

## 🔧 故障排查

1. **未找到新闻**：检查 `transport_news.json` 是否存在
2. **坐标不准确**：在 `fetch_news.py` 的 `locations` 字典中添加
3. **展示方式错误**：调整 `_infer_display_type()` 中的关键词列表
4. **地图不显示**：检查 `output/index.html` 的Leaflet库引用

## 📖 参考资料

- **GeoJSON规范**：https://geojson.org/
- **Leaflet地图库**：https://leafletjs.com/
- **重庆行政区划坐标**：可从开放数据平台获取

## 💡 最佳实践

1. **定期备份**：`transport_news.json` 每次更新前备份
2. **手动审核**：自动分类可能不准确，定期review数据质量
3. **添加元数据**：在新闻中添加URL、作者、标签等
4. **性能优化**：新闻超过100条时，可只保留最近30天
