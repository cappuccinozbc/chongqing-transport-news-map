# 重庆交通新闻地图

## 🎯 项目简介

一个可视化展示重庆交通相关新闻的交互式地图应用。通过自动抓取、去重、空间定位，将交通新闻以点、线、面、网络等形式在地图上展示。

**核心价值：** 让用户一目了然地在地图上看到重庆的交通发展动态。

## ✨ 主要特性

### 🤖 智能分析
- **自动分类**：建设、规划、运营、其他
- **智能去重**：基于内容哈希，避免重复
- **空间定位**：自动识别新闻涉及的区域/地点
- **展示方式识别**：自动判断用点/线/面/哪种方式展示

### 🗺️ 多种展示方式
- **📍 点状**：单个地点（车站、站点、交叉口）
- **📏 线状**：道路、线路、高速、走廊
- **⬛ 面状**：区域、片区、新城、开发区
- **🔗 网络状**：多线路连接、枢纽、综合交通体系

### 🎨 可视化效果
- **颜色编码**：按分类用不同颜色（建设=橙、规划=蓝、运营=绿）
- **大小映射**：按展示方式调整图元大小
- **时间轴**：按新闻时间排序和筛选
- **交互式**：点击查看详情、高亮关联新闻

## 🚀 快速开始

### 方式1：使用示例数据测试

```bash
cd chongqing-transport-news-map

# 1. 抓取示例新闻
python3 scripts/fetch_news.py

# 2. 生成地图
python3 scripts/generate_map.py

# 3. 启动本地服务
cd output && python3 -m http.server 8000

# 4. 打开浏览器
open http://localhost:8000/index.html
```

### 方式2：从MPText API抓取真实数据

```bash
# 1. 设置API Key
export MPTEXT_API_KEY=your_api_key_here

# 2. 编辑fetch_news.py，在main()函数中添加：
fetcher.fetch_from_mptext(api_key=os.getenv("MPTEXT_API_KEY"), keyword="重庆交通")

# 3. 生成地图
python3 scripts/generate_map.py
```

## 📁 项目结构

```
chongqing-transport-news-map/
├── SKILL.md                      # 技能使用说明
├── README.md                     # 项目文档（本文件）
├── scripts/
│   ├── fetch_news.py            # 新闻抓取和去重工具
│   └── generate_map.py           # GeoJSON和HTML地图生成
├── references/                    # (可选) 配置和参考
├── assets/                       # (可选) 静态资源
└── output/                       # 生成输出
    ├── transport_news.json         # 新闻数据库
    ├── news_data.geojson          # Geo地图数据
    └── index.html               # 交互式地图
```

## 🎨 数据格式

### transport_news.json

```json
{
  "news": [
    {
      "title": "重庆轨道交通24号线一期工程开工",
      "content": "线路全长约45公里，起于鹿栖站，止于广阳北站...",
      "source": "重庆轨道交通集团",
      "hash": "a1b2c3d4...",           # 内容哈希（用于去重）
      "timestamp": "2026-03-09T14:00:00",
      "location": {
        "name": "渝北区",
        "lat": 29.82,
        "lng": 106.51
      },
      "display_type": "line",            # point/line/area/network
      "category": "建设"                  # 建设/规划/运营/其他
    }
  ],
  "last_update": "2026-03-09T14:00:00"
}
```

### news_data.geojson

标准GeoJSON格式，Feature的properties包含新闻信息：

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",              # 或 LineString/Polygon/MultiLineString
        "coordinates": [106.51, 29.82]
      },
      "properties": {
        "title": "新闻标题",
        "content": "新闻内容",
        "source": "来源",
        "category": "建设",
        "timestamp": "2026-03-09T14:00:00",
        "display_type": "point",
        "color": "#FF5722",
        "size": 1.0
      }
    }
  ]
}
```

## 🎨 地图交互功能

### 当前实现
- ✅ **基础地图**：Leaflet + OpenStreetMap底图
- ✅ **多图层**：按展示类型分图层
- ✅ **点击弹窗**：显示新闻详情
- ✅ **新闻列表**：右侧面板显示新闻
- ✅ **联动高亮**：点击列表对应地图图元

### 可扩展功能顶建议

#### 📅 高级筛选
```javascript
// 按分类筛选
filterByCategory('建设');  // 只显示建设类新闻

// 按时间范围筛选
filterByDateRange('2026-03-01', '2026-03-10');

// 按来源筛选
filterBySource('重庆轨道交通集团');

// 搜索关键词
searchNews('轨道');
```

#### 📈 热力图分析
```javascript
// 分析区域间关联
generateHeatmap();

// 显示交通网络分析
showNetworkAnalysis();
```

#### 📊 数据统计
```javascript
// 按分类统计
showCategoryStats();

// 按区域统计
showAreaStats();

// 时间趋势图
showTimeTrendChart();
```

#### 🔄 自动刷新
```javascript
// WebSocket实时更新
const ws = new WebSocket('ws://your-server/updates');
ws.onmessage = (data) => {
    addNewsToMap(data);
};
```

## 🔧 配置选项

### 地图样式

编辑 `scripts/generate_map.py`：

```python
# 修改中心点和缩放层级
DEFAULT_CENTER = [29.56, 106.55]  # 重庆主城区
DEFAULT_ZOOM = 11

# 修改颜色方案
COLOR_SCHEME = {
    "建设": "#FF5722",      # 橙色
    "规划": "#2196F3",      # 蓝色
    "运营": "#4CAF50",      # 绿色
    "其他": "#9E9E9E"       # 灰色
}
```

### 数据源配置

编辑 `scripts/fetch_news.py`：

```python
# 添加更多新闻源
NEWS_SOURCES = [
    "https://jtj.cq.gov.cn",           # 重庆交通局
    "https://www.cqmetro.cn",             # 重庆轨道集团
    "https://mp.weixin.qq.com/...",
]
```

## 📝 工作流程

```
1. 数据抓取阶段
   ├─ 从MPText API获取公众号文章
   ├─ 从政府网站抓取官方新闻
   └─ 从媒体网站抓取相关报道
   
2. 数据处理阶段
   ├─ 内容哈希去重
   ├─ 空间位置识别
   ├─ 分类自动标注
   └─ 展示方式判断

3. 数据存储阶段
   ├─ 保存JSON格式数据库
   ├─ 生成GeoJSON格式
   └─ 更新时间戳

4. 地图生成阶段
   ├─ 构建GeoJSON FeatureCollection
   ├─ 生成HTML交互地图
   └─ 添加样式和脚本

5. 部署和展示
   ├─ 本地HTTP服务器
   ├─ 或部署到Web服务器
   └─ 或嵌入静态网站
```

## 🌐 部署方案

### 本地开发
```bash
# Python简单服务器
cd output && python3 -m http.server 8000

# 或使用Node
npx http-server -p 8000 output
```

### 生产部署

#### Nginx
```nginx
server {
    listen 80;
    server_name newsmap.yourdomain.com;
    root /path/to/output;
    
    location / {
        try_files $uri $uri/ =404;
    }
}
```

#### Vercel
```bash
# 1. 创建vercel.json
cd output && echo '{"version": 2}' > vercel.json

# 2. 部署
vercel deploy --prod
```

#### GitHub Pages
```bash
# 1. 推送到gh-pages分支
git subtree push --prefix output origin gh-pages

# 2. 访问
open https://yourname.github.io/chongqing-transport-news-map/
```

## 🔮 自动化

### Cron定时任务

```bash
# 每天凌晨2点执行更新
openclaw cron add --json '{
  "name": "transport-news-updater",
  "schedule": {
    "kind": "cron",
    "expr": "0 2 * * *",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "agentTurn",
    "message": "抓取重庆交通新闻并更新地图"
  },
  "sessionTarget": "main",
  "enabled": true
}'
```

## 📖 后续优化方向

### 短期（1-2周）
- [ ] **添加搜索框**：在地图上搜索新闻
- [ ] **时间筛选器**：按日期范围筛选
- [ ] **分类图例**：显示颜色含义
- [ ] **分享功能**：生成分享链接/二维码
- [ ] **响应式设计**：移动端优化

### 中期（1-2月）
- [ ] **更多数据源**：政府网站、媒体RSS
- [ ] **详细页面**：点击新闻跳转详情页
- [ ] **评论系统**：允许用户讨论
- [ ] **收藏功能**：用户可收藏感兴趣新闻
- [ ] **通知功能**：新新闻推送提醒

### 长期（3-6月）
- [ ] **热力图**：显示交通热点区域
- [ ] **网络分析**：计算交通连通性
- [ ] **历史回溯**：查看历史变化趋势
- [ ] **数据API**：提供外部调用接口
- [ ] **后台管理**：数据审核和管理界面

## 🐛 故障排查

### 问题：地图不显示
**检查：**
1. Leaflet库是否加载（打开浏览器开发者工具检查Network）
2. GeoJSON数据格式是否正确
3. 坐标是否为0或NaN

**解决：**
```javascript
// 在浏览器控制台运行
console.log(map);  // 检查地图对象
console.log(newsData);  // 检查数据
```

### 问题：新闻去重失效
**检查：**
1. `hash`字段是否正确生成
2. JSON文件是否有重复内容

**解决：**
```python
# 清空缓存重新开始
rm transport_news.json && python3 scripts/fetch_news.py
```

### 问题：空间定位不准确
**解决：**
1. 编辑 `fetch_news.py` 的 `locations` 字典
2. 使用高德/百度地图API获取精确坐标
3. 或手动标注位置信息

## 📞 技术栈

- **后端**：Python 3.x
  - requests：HTTP请求
  - json：数据存储
  - hashlib：去重算法
  
- **前端**：纯HTML + JavaScript
  - Leaflet 1.9.4：地图库
  - OpenStreetMap：底图数据
  - 无框架依赖：轻量级

## 📄 许可证

本项目仅供学习和参考使用。
数据来源：重庆交通局、重庆轨道集团、重庆交通开投集团等官方渠道。

---

**开始使用：** 运行 `python3 scripts/fetch_news.py && python3 scripts/generate_map.py`
