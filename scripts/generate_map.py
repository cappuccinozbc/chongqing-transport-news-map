#!/usr/bin/env python3
"""
生成重庆交通新闻地图

功能：
1. 读取新闻数据
2. 生成GeoJSON或HTML地图
3. 根据展示类型渲染不同样式（点/线/面/网络）
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
    
    def load_data(self) -> Dict:
        """加载新闻数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ 无法加载数据: {e}")
            return {"news": []}
    
    def generate_geojson(self, data: Dict) -> Dict:
        """
        生成GeoJSON格式数据
        
        Features类型：
        - Point: 点状（单个地点）
        - LineString: 线状（道路、线路）
        - Polygon: 面状（区域、片区）
        - MultiLineString: 网络（多个连接线）
        """
        features = []
        news_data = data.get("news", [])
        
        for news in news_data:
            location = news.get("location", {})
            display_type = news.get("display_type", "point")
            
            if not location or "lat" not in location or "lng" not in location:
                continue
            
            lat = location["lat"]
            lng = location["lng"]
            
            # 根据展示类型生成不同的Geometry
            props = {
                "title": news.get("title", ""),
                "content": news.get("content", ""),
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
        """生成HTML交互地图（使用Leaflet）"""
        
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>重庆交通新闻地图</title>
    
    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    
    <style>
        body {{ margin: 0; padding: 0; font-family: 'Microsoft YaHei', sans-serif; }}
        #map {{ height: 100vh; width: 100%; }}
        .info-panel {{
            position: fixed;
            top: 20px;
            right: 20px;
            width: 350px;
            max-height: 80vh;
            overflow-y: auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            z-index: 1000;
        }}
        .news-item {{
            padding: 15px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
        }}
        .news-item:hover {{ background: #f5f5f5; }}
        .news-item h4 {{ margin: 0 0 8px 0; color: #333; }}
        .news-item p {{ margin: 0; color: #666; font-size: 14px; }}
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
        }}
        .tag-建设 {{ background: #4CAF50; color: white; }}
        .tag-规划 {{ background: #2196F3; color: white; }}
        .tag-运营 {{ background: #FF9800; color: white; }}
        .tag-其他 {{ background: #9E9E9E; color: white; }}
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div class="info-panel">
        <h3>📍 重庆交通新闻</h3>
        <div id="news-list"></div>
    </div>
    
    <!-- Leaflet JS -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <script>
        // 初始化地图
        var map = L.map('map').setView([29.56, 106.55], 11);
        
        // 添加底图
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);
        
        // 新闻数据
        var newsData = {json.dumps(geojson['features'], ensure_ascii=False)};
        
        // 图层组
        var pointLayer = L.layerGroup().addTo(map);
        var lineLayer = L.layerGroup().addTo(map);
        var areaLayer = L.layerGroup().addTo(map);
        var networkLayer = L.layerGroup().addTo(map);
        
        // 渲染新闻
        newsData.forEach(function(feature, index) {{
            var props = feature.properties;
            var geometry = feature.geometry;
            var layer;
            
            // 根据类型选择样式
            var style = {{
                color: props.color,
                weight: props.size * 2,
                opacity: 0.7,
                fillColor: props.color,
                fillOpacity: 0.3
            }};
            
            // 根据几何类型渲染
            if (geometry.type === 'Point') {{
                layer = L.circleMarker([geometry.coordinates[1], geometry.coordinates[0]], {{
                    radius: props.size * 5000,
                    fillColor: props.color,
                    color: props.color,
                    weight: 2,
                    opacity: 0.8,
                    fillOpacity: 0.4
                }});
            }} else if (geometry.type === 'LineString') {{
                layer = L.polyline(geometry.coordinates.map(function(c) {{ return [c[1], c[0]]; }}), style);
            }} else if (geometry.type === 'Polygon') {{
                layer = L.polygon(geometry.coordinates[0].map(function(c) {{ return [c[1], c[0]]; }}), style);
            }} else if (geometry.type === 'MultiLineString') {{
                layer = L.multiPolyline(geometry.coordinates.map(function(line) {{
                    return line.map(function(c) {{ return [c[1], c[0]]; }});
                }}), style);
            }}
            
            // 添加弹出信息
            layer.bindPopup(
                '<strong>' + props.title + '</strong><br>' +
                '<small>' + props.source + '</small><br><br>' +
                props.content.substring(0, 100) + (props.content.length > 100 ? '...' : '') +
                '<br><br><span class="tag tag-' + props.category + '">' + props.category + '</span>'
            );
            
            // 添加点击事件
            layer.on('click', function() {{
                highlightNews(index);
            }});
            
            // 根据类型添加到对应图层
            if (props.display_type === 'point') {{
                pointLayer.addLayer(layer);
            }} else if (props.display_type === 'line') {{
                lineLayer.addLayer(layer);
            }} else if (props.display_type === 'area') {{
                areaLayer.addLayer(layer);
            }} else if (props.display_type === 'network') {{
                networkLayer.addLayer(layer);
            }}
        }});
        
        // 渲染新闻列表
        var newsList = document.getElementById('news-list');
        newsData.forEach(function(feature, index) {{
            var props = feature.properties;
            var item = document.createElement('div');
            item.className = 'news-item';
            item.innerHTML = 
                '<h4>' + props.title + '</h4>' +
                '<p>' + props.content.substring(0, 80) + '...</p>' +
                '<div class="meta">' +
                    '<span class="tag tag-' + props.category + '">' + props.category + '</span>' +
                    '<span class="tag tag-' + props.display_type + '">' + props.display_type + '</' + 
                    '<br>' + props.source.split(' ')[0] + 
                '</div>';
            
            item.onclick = function() {{
                map.eachLayer(function(layer) {{
                    if (layer._popup && layer._popup.getContent().indexOf(props.title) >= 0) {{
                        layer.openPopup();
                    }}
                }});
                map.setView(feature.geometry.type === 'Point' ? 
                    [feature.geometry.coordinates[1], feature.geometry.coordinates[0]] : 
                    [29.56, 106.55], 12);
            }};
            
            newsList.appendChild(item);
        }});
        
        // 高亮显示新闻
        function highlightNews(index) {{
            // TODO: 实现高亮效果
            console.log('Highlight news:', index);
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
            "其他": "#9E9E9E"       # 灰色
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
