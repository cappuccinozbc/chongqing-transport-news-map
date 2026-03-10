#!/usr/bin/env python3
"""
生成重庆交通新闻地图

功能：
1. 读取新闻数据
2. 生成GeoJSON或HTML地图
3. 根据展示类型渲染不同样式（点/线/面/网络）
4. 判断宏观新闻，不在地图上显示
"""

import json
from typing import Dict, List
from pathlib import Path

class MapGenerator:
    """地图生成器"""
    
    def __init__(self, data_file: str = "transport_news.json"):
        self.data_file = data_file

        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        # 高德地图API Key
        self.amap_key = "a4097d1dbdf4a439ff4ad1e49a18b3fb"
    
    def load_data(self) -> Dict:
        """加载新闻数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ 无法加载数据: {e}")
            return {"news": []}
    
    def _is_spatial_feature(self, title: str, content: str) -> bool:
        """

        
        判断新闻是否适合空间表达
        
        如果是宏观、总体情况（全市、全路网等），返回False
        """
        text = f"{title} {content}".lower()
        
        # 宏观关键词
        macro_keywords = [
            "全市", "全路网", "轨道线网", "全线",
            "总体情况", "整体", "全网",
            "里程突破", "共开通", "共计",
            "运营线路", "覆盖主城", "日均客运"
        ]
        
        # 如果包含宏观关键词，不适合空间表达
        for keyword in macro_keywords:
            if keyword in text:
                return False
        
        return True
    
    def generate_geojson(self, data: Dict) -> Dict:
        """
        生成GeoJSON格式数据
        
        Features类型：
        - Point: 点状（单个地点）
        - LineString: 线状（道路、线路）
        - Polygon: 面状（区域、片区
        - MultiLineString: 网络（多个连接线）
        - macro: 宏观情况（不在地图显示，只在右侧列表）
        """
        features = []
        news_data = data.get("news", [])
        
        for news in news_data:
            title = news.get("title", "")
            content = news.get("content", "")
            location = news.get("location", {})
            display_type = news.get("display_type", "point")
            
            # 判断是否适合空间表达
            is_spatial = self._is_spatial_feature(title, content)
            
            # 如果不适合空间表达，标记为宏观情况
            if not is_spatial:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [0, 0]
                    },
                    "properties": {
                        "title": title,
                        "content": content,
                        "source": news.get("source", ""),
                        "category": "总体情况",
                        "timestamp": news.get("timestamp", ""),
                        "display_type": "macro",
                        "color": "#607D8B",
                        "size": 0
                    }
                })
                continue
            
            # 空间特征的正常处理
            if not location or "lat" not in location or "lng" not in location:
                continue
            
            lat = location["lat"]
            lng = location["lng"]
            
            # 根据展示类型生成不同的Geometry
            props = {
                "title": title,
                "content": content,
                "source": news.get("source", ""),
                "category": news.get("category", "其他"),
                "timestamp": news.get("timestamp", ""),
                "display_type": display_type,
                "color": self._get_color_by_category(news.get("category", "")),
                "size": self._get_size_by_type(display_type)
            }
            
            if display_type == "point":
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat]
                    },
                    "properties": props
                })
            
            elif display_type == "line":
                # 线状：假设从中心点向两个方向延伸
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [lng - 0.05, lat - 0.05],
                            [lng, lat],
                            [lng + 0.05, lat + 0.05]

                        ]
                    },
                    "properties": props
                })
            
            elif display_type == "area":
                # 面状：以中心点生成矩形
                size = 0.05
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [lng - size, lat - size],
                            [lng + size, lat - size],
                            [lng + size, lat + size],
                            [lng - size, lat + size],
                            [lng - size, lat - size]
                        ]]
                    },
                    "properties": props
                })
            
            elif display_type == "network":
                # 网络：多个连接线
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "MultiLineString",
                        "coordinates": [
                            [[lng - 0.03, lat - 0.03], [lng, lat]],
                            [[lng, lat], [lng + 0.04, lat + 0.01]],
                            [[lng, lat], [lng - 0.02, lat + 0.04]],
                            [[lng, lat], [lng + 0.03, lat - 0.02]]
                        ]
                    },
                    "properties": props
                })
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return geojson
    
    def generate_html_map(self, geojson: Dict) -> str:
        """生成HTML交互地图（使用高德地图官方JS API）"""
        
        # 构建newsData JavaScript代码
        news_data_js = json.dumps(geojson['features'], ensure_ascii=False)
        
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>重庆交通新闻地图</title>
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        html, body, #container {{
            width: 100%;
            height: 100%;
            font-family: 'Microsoft YaHei', sans-serif;
        }}
        #container {{
            position: relative;
        }}
        #map {{
            width: 100%;
            height: 100%;
        }}
        .info-panel {{
            position: absolute;
            top: 20px;
            right: 20px;
            width: 350px;
            max-height: 80vh;
            overflow-y: auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            z-index: 999;
        }}
        .news-item {{
            padding: 15px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
        }}
        .news-item.macro {{
            background: #f5f5f5;
            cursor: default;
        }}
        .news-item:hover {{
            background: #f0f0f0;
        }}
        .news-item.macro:hover {{
            background: #f5f5f5;
        }}
        .news-item h4 {{
            margin: 0 0 8px 0;
            color: #333;
            font-size: 16px;
        }}
        .news-item p {{
            margin: 0 0 8px 0;
            color: #666;
            font-size: 14px;
            line-height: 1.5;
        }}
        .news-item .meta {{
            margin-top: 8px;
            font-size: 12px;
            color: #999;
        }}
        .tag {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 11px;
            margin-right: 5px;
            margin-bottom: 3px;
        }}
        .tag-建设 {{ background: #4CAF50; color: white; }}
        .tag-规划 {{ background: #2196F3; color: white; }}
        .tag-运营 {{ background: #FF9800; color: white; }}
        .tag-其他 {{ background: #9E9E9E; color: white; }}
        .tag-总体情况 {{ background: #607D8B; color: white; }}
    </style>
    
    <script type="text/javascript">
        window._AMapSecurityConfig = {{
            securityJsCode: '{self.amap_key}',
            serviceHost: 'https://restapi.amap.com'
        }};
    </script>
    <script src="https://webapi.amap.com/loader.js?name=amap&amp;v=2.0&amp;key={self.amap_key}"></script>
</head>
<body>
    <div id="container">
        <div id="map"></div>
        
        <div class="info-panel">
            <h3>📍 重庆交通新闻</h3>
            <div id="news-list"></div>
        </div>
    </div>
    
    <script>
        var newsData = {news_data_js};
        var map;
        var overlays = [];
        
        // 等待AMap加载完成
        function checkAMap() {{
            if (typeof AMap !== 'undefined') {{
                initMap();
            }} else {{
                setTimeout(checkAMap, 100);
            }}
        }}
        
        checkAMap();
        
        function initMap() {{
            AMap.plugin(['AMap.Map', 'AMap.Marker', 'AMap.Polyline', 'AMap.Polygon', 'AMap.InfoWindow'], function() {{
            // 初始化地图
            map = new AMap.Map('map', {{
                zoom: 11,
                center: [106.55, 29.56],
                viewMode: '2D',
                lang: 'zh_cn'
            }});
            
            // 添加控件
            map.addControl(new AMap.Scale());
            
            // 渲染空间特征
            renderMapFeatures();
            
            // 渲染新闻列表
            renderNewsList();
            }}); // AMap.plugin结束
        }} // initMap结束
        
        function renderMapFeatures() {{
            newsData.forEach(function(feature) {{
                var props = feature.properties;
                
                // 宏观情况不在地图上渲染
                if (props.display_type === 'macro') {{
                    return;
                }}
                
                var geometry = feature.geometry;
                var style = {{
                    strokeColor: props.color,
                    strokeOpacity: 0.8,
                    strokeWeight: props.size * 3,
                    fillColor: props.color,
                    fillOpacity: 0.3
                }};
                
                var overlay;
                
                if (geometry.type === 'Point') {{
                    var marker = new AMap.Marker(new AMap.LngLat(geometry.coordinates[0], geometry.coordinates[1]), {{
                        title: props.title
                    }});
                    
                    // 添加信息窗
                    var infoWindow = new AMap.InfoWindow({{
                        content: '<div style="padding:10px;"><strong>' + props.title + '</strong><br>' +
                                 '<small>' + props.source + '</small><br><br>' +
                                 props.content + '<br><br>' +
                                 '<span class="tag tag-' + props.category + '">' + props.category + '</span></div>',
                        offset: new AMap.Pixel(0, -30)
                    }});
                    
                    marker.on('click', function() {{
                        infoWindow.open(map, marker.getPosition());
                    }});
                    
                    overlay = marker;
                }} else if (geometry.type === 'LineString') {{
                    var path = geometry.coordinates.map(function(c) {{
                        return new AMap.LngLat(c[0], c[1]);
                    }});
                    
                    overlay = new AMap.Polyline(path, style);
                }} else if (geometry.type === 'Polygon') {{
                    var path = geometry.coordinates[0].map(function(c) {{
                        return new AMap.LngLat(c[0], c[1]);
                    }});
                    
                    overlay = new AMap.Polygon(path, style);
                }} else if (geometry.type === 'MultiLineString') {{
                    // MultiLineString创建多条线
                    var group = [];
                    geometry.coordinates.forEach(function(line) {{
                        var path = line.map(function(c) {{
                            return new AMap.LngLat(c[0], c[1]);
                        }});
                        group.push(new AMap.Polyline(path, style));
                    }});
                    overlay = group;
                }}
                
                if (overlay) {{
                    if (Array.isArray(overlay)) {{
                        overlay.forEach(function(o) {{
                            map.add(o);
                            overlays.push(o);
                        }});
                    }} else {{
                        map.add(overlay);
                        overlays.push(overlay);
                    }}
                }}
            }});
        }}
        
        function renderNewsList() {{
            var newsList = document.getElementById('news-list');
            newsData.forEach(function(feature) {{
                var props = feature.properties;
                var item = document.createElement('div');
                item.className = 'news-item' + (props.display_type === 'macro' ? ' macro' : '');
                
                item.innerHTML = 
                    '<h4>' + props.title + '</h4>' +
                    '<p>' + props.content + '</p>' +
                    '<div class="meta">' +
                        '<span class="tag tag-' + props.category + '">' + props.category + '</span>' +
                        '<span class="tag tag-' + props.display_type + '">' + props.display_type + '</span>' +
                        '<br><br>' + props.source.split(' ')[0] + 
                        '<br>' + props.timestamp + 
                    '</div>';
                
                // 非宏观新闻可点击定位
                if (props.display_type !== 'macro') {{
                    item.onclick = function() {{
                        var geometry = feature.geometry.geometry;
                        if (geometry.type === 'Point') {{
                            map.setCenter(new AMap.LngLat(geometry.coordinates[0], geometry.coordinates[1]));
                            map.setZoom(14);
                        }} else {{
                            map.setCenter(new AMap.LngLat(106.55, 29.56));
                            map.setZoom(12);
                        }}
                    }};
                }}
                
                newsList.appendChild(item);
            }});
        }}
    </script>
</body>
</html>"""
        
        return html_template
    
    def _get_color_by_category(self, category: str) -> str:
        """根据分类获取颜色"""
        colors = {
            "建设": "#FF5722",      # 橙色
            "规划": "#2196F3",      # 蓝色
            "运营": "#4CAF50",      # 绿色
            "其他": "#9E9E9E",      # 灰色
            "总体情况": "#607D8B"   # 蓝灰色
        }
        return colors.get(category, "#666666")
    
    def _get_size_by_type(self, display_type: str) -> float:
        """根据展示类型获取大小"""
        sizes = {
            "point": 1.0,
            "line": 2.0,
            "area": 2.5,
            "network": 3.0
        }
        return sizes.get(display_type, 1.0)
    
    def generate(self):
        """生成所有输出文件"""
        print("\n🗺️ 生成地图文件...")
        
        # 加载数据
        data = self.load_data()
        if not data.get("news"):
            print("❌ 没有新闻数据")
            return
        
        print(f"📊 共有 {len(data['news'])} 条新闻")
        
        # 生成GeoJSON
        geojson = self.generate_geojson(data)
        
        # 统计宏观和空间新闻
        spatial_count = sum(1 for f in geojson['features'] if f['properties']['display_type'] != 'macro')
        macro_count = sum(1 for f in geojson['features'] if f['properties']['display_type'] == 'macro')
        
        print(f"📍 空间特征: {spatial_count} 条")
        print(f"📋 宏观情况: {macro_count} 条")
        
        geojson_file = self.output_dir / "news_data.geojson"
        with open(geojson_file, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        print(f"✅ GeoJSON已生成: {geojson_file}")
        
        # 生成HTML地图
        html = self.generate_html_map(geojson)
        html_file = self.output_dir / "index.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ HTML地图已生成: {html_file}")
        
        print(f"\n💾 所有文件已生成到: {self.output_dir.absolute()}")
        print(f"🌐 打开地图: file://{html_file.absolute()}")


def main():
    """主函数"""
    print("=" * 60)
    print("重庆交通新闻地图生成器")
    print("=" * 60)
    
    generator = MapGenerator()
    generator.generate()


if __name__ == "__main__":
    main()
