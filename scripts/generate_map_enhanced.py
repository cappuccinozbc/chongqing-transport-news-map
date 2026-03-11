#!/usr/bin/env python3
"""
生成重庆交通新闻地图（增强版）

功能：
1. 读取新闻数据
2. 生成GeoJSON或HTML地图
3. 根据展示类型渲染不同样式（点/线/面/网络）
4. 判断宏观新闻，不在地图上显示
5. 显示发布时间和来源URL
"""

import json
from typing import Dict, List
from pathlib import Path
from datetime import datetime

class MapGenerator:
    """地图生成器"""
    
    def __init__(self, data_file: str = "transport_news.json"):
        self.data_file = data_file
        self.output_dir = Path("docs")  # 改为docs目录，用于GitHub Pages
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
    
    def _format_publish_time(self, time_str: str) -> str:
        """格式化发布时间显示"""
        if not time_str:
            return "未知时间"
        
        try:
            dt = datetime.fromisoformat(time_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return time_str
    
    def generate_geojson(self, data: Dict) -> Dict:
        """
        生成GeoJSON格式数据
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
            
            # 格式化发布时间
            publish_time = news.get("publish_time", "")
            formatted_time = self._format_publish_time(publish_time)
            
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
                        "url": news.get("url", ""),
                        "category": "总体情况",
                        "timestamp": news.get("timestamp", ""),
                        "publish_time": publish_time,
                        "formatted_time": formatted_time,
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
                "url": news.get("url", ""),
                "category": news.get("category", "其他"),
                "timestamp": news.get("timestamp", ""),
                "publish_time": publish_time,
                "formatted_time": formatted_time,
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
            width: 380px;
            max-height: 80vh;
            overflow-y: auto;
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            z-index: 1000;
        }}
        .info-panel h3 {{
            margin: 0 0 20px 0;
            color: #333;
            font-size: 18px;
        }}
        .news-item {{
            padding: 15px;
            border-bottom: 1px solid #f0f0f0;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .news-item.macro {{
            background: #f8f9fa;
            cursor: default;
        }}
        .news-item:hover {{
            background: #f5f5f5;
        }}
        .news-item.macro:hover {{
            background: #f8f9fa;
        }}
        .news-item h4 {{
            margin: 0 0 8px 0;
            color: #333;
            font-size: 15px;
            line-height: 1.4;
        }}
        .news-item p {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 13px;
            line-height: 1.6;
        }}
        .news-item .meta {{
            margin-top: 8px;
            font-size: 11px;
            color: #999;
        }}
        .news-item .url {{
            margin-top: 6px;
            font-size: 11px;
        }}
        .news-item .url a {{
            color: #2196F3;
            text-decoration: none;
            word-break: break-all;
        }}
        .news-item .url a:hover {{
            text-decoration: underline;
        }}
        .tag {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            margin-right: 6px;
            margin-bottom: 4px;
            font-weight: 500;
        }}
        .tag-建设 {{ background: #4CAF50; color: white; }}
        .tag-规划 {{ background: #2196F3; color: white; }}
        .tag-运营 {{ background: #FF9800; color: white; }}
        .tag-其他 {{ background: #9E9E9E; color: white; }}
        .tag-总体情况 {{ background: #607D8B; color: white; }}
        .tag-point {{ background: #9C27B0; color: white; }}
        .tag-line {{ background: #E91E63; color: white; }}
        .tag-area {{ background: #00BCD4; color: white; }}
        .tag-network {{ background: #FF9800; color: white; }}
        .loading {{
            text-align: center;
            padding: 40px 20px;
            color: #999;
            font-size: 14px;
        }}
        .error-message {{
            text-align: center;
            padding: 20px;
            color: #d32f2f;
            font-size: 14px;
            background: #ffebee;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .map-toolbar {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: white;
            padding: 10px 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
        }}
        .map-toolbar button {{
            margin: 0 5px;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            background: #2196F3;
            color: white;
            cursor: pointer;
            font-size: 12px;
        }}
        .map-toolbar button:hover {{
            background: #1976D2;
        }}
    </style>
</head>
<body>
    <div id="container">
        <div id="map"></div>
        
        <div class="map-toolbar">
            <button onclick="resetView()">重置视图</button>
            <button onclick="toggleLayer()">切换图层</button>
        </div>
        
        <div class="info-panel">
            <h3>📍 重庆交通新闻</h3>
            <div id="news-list">
                <div class="loading">正在加载地图和新闻...</div>
            </div>
            <div id="stats" style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #f0f0f0; font-size: 12px; color: #999;"></div>
        </div>
    </div>
    
    <script type="text/javascript">
        window._AMapSecurityConfig = {{
            securityJsCode: '{self.amap_key}',
            serviceHost: 'https://restapi.amap.com'
        }};
    </script>
    <script type="text/javascript" src="https://webapi.amap.com/maps?v=2.0&key={self.amap_key}"></script>
    
    <script>
        var newsData = {news_data_js};
        var map;
        var overlays = [];
        var currentLayer = 0;
        
        function renderMapFeatures() {{
            if (!map) return;
            
            console.log('开始渲染地图特征，共', newsData.length, '条');
            
            var spatialCount = 0;
            
            newsData.forEach(function(feature) {{
                var props = feature.properties;
                
                if (props.display_type === 'macro') {{
                    return;
                }}
                
                spatialCount++;
                
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
                    
                    var infoWindow = new AMap.InfoWindow({{
                        content: '<div style="padding:12px; min-width:250px;"><strong style="color:#333; font-size:16px; margin-bottom:8px; display:block;">' + props.title + '</strong><small style="color:#666; font-size:12px; display:block; margin-bottom:10px;">' + props.source + '</small><p style="color:#666; font-size:14px; line-height:1.6; margin:0 0 10px 0;">' + props.content + '</p><span class="tag tag-' + props.category + '">' + props.category + '</span></div>',
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
            
            console.log('地图特征渲染完成，空间特征:', spatialCount, '条');
        }}
        
        function renderNewsList() {{
            var newsList = document.getElementById('news-list');
            var statsDiv = document.getElementById('stats');
            newsList.innerHTML = '';
            
            var macroCount = 0;
            var spatialCount = 0;
            
            newsData.forEach(function(feature) {{
                var props = feature.properties;
                
                if (props.display_type === 'macro') {{
                    macroCount++;
                }} else {{
                    spatialCount++;
                }}
                
                var item = document.createElement('div');
                item.className = 'news-item' + (props.display_type === 'macro' ? ' macro' : '');
                
                var categoryTagClass = 'tag-' + props.category;
                var typeTagClass = 'tag-' + props.display_type;
                
                // 构建URL链接
                var urlHtml = '暂无链接';
                if (props.url && props.url.length > 0) {{
                    urlHtml = '<a href="' + props.url + '" target="_blank">📎 查看原文</a>';
                }}
                
                item.innerHTML = 
                    '<h4>' + props.title + '</h4>' +
                    '<p>' + props.content + '</p>' +
                    '<div class="meta">' +
                        '<span class="tag ' + categoryTagClass + '">' + props.category + '</span>' +
                        '<span class="tag ' + typeTagClass + '">' + props.display_type + '</span>' +
                        '<br><br>' +
                        '<strong>📅 发布时间：</strong>' + (props.formatted_time || '未知时间') +
                        '<br><strong>🏢 来源：</strong>' + props.source.split(' ')[0] +
                    '</div>' +
                    '<div class="url">' + urlHtml + '</div>';
                
                if (props.display_type !== 'macro') {{
                    item.onclick = (function(feature) {{
                        return function() {{
                            var geometry = feature.geometry;
                            if (geometry.type === 'Point') {{
                                map.setCenter(new AMap.LngLat(geometry.coordinates[0], geometry.coordinates[1]));
                                map.setZoom(14);
                            }} else {{
                                map.setCenter(new AMap.LngLat(106.55, 29.56));
                                map.setZoom(12);
                            }}
                        }};
                    })(feature);
                }}
                
                newsList.appendChild(item);
            }});
            
            statsDiv.innerHTML = 
                '<strong>统计信息：</strong><br>' +
                '总计: ' + newsData.length + ' 条 | ' +
                '空间特征: ' + spatialCount + ' 条 | ' +
                '宏观情况: ' + macroCount + ' 条';
            
            console.log('新闻列表渲染完成');
        }}
        
        function resetView() {{
            if (map) {{
                map.setCenter(new AMap.LngLat(106.55, 29.56));
                map.setZoom(11);
            }}
        }}
        
        function toggleLayer() {{
            currentLayer = (currentLayer + 1) % 2;
            
            overlays.forEach(function(overlay) {{
                if (Array.isArray(overlay)) {{
                    overlay.forEach(function(o) {{
                        if (currentLayer === 0) {{
                            map.add(o);
                        }} else {{
                            map.remove(o);
                        }}
                    }});
                }} else {{
                    if (currentLayer === 0) {{
                        map.add(overlay);
                    }} else {{
                        map.remove(overlay);
                    }}
                }}
            }});
        }}
        
        function initMap() {{
            try {{
                map = new AMap.Map('map', {{
                    zoom: 11,
                    center: [106.55, 29.56],
                    viewMode: '2D',
                    lang: 'zh_cn'
                }});
                
                // 添加比例尺控件（v2.0中使用插件方式）
                AMap.plugin(['AMap.Scale'], function() {{
                    map.addControl(new AMap.Scale());
                }});
                
                console.log('地图初始化成功');
        
                renderMapFeatures();
                
                renderNewsList();
            }} catch (error) {{
                console.error('地图初始化失败:', error);
                var newsList = document.getElementById('news-list');
                newsList.innerHTML = '<div class="error-message">地图加载失败，请刷新页面重试。<br>错误信息: ' + error.message + '</div>';
            }}
        }}
        
        // 页面加载完成后等待AMap
        window.addEventListener('load', function() {{
            console.log('页面加载完成');
            
            // 等待AMap加载完成
            var checkCount = 0;
            var maxCheck = 50; // 最多等待5秒
            
            function checkAMap() {{
                if (typeof AMap !== 'undefined') {{
                    console.log('AMap已加载，初始化地图');
                    initMap();
                }} else {{
                    checkCount++;
                    if (checkCount < maxCheck) {{
                        console.log('等待AMap加载...', checkCount);
                        setTimeout(checkAMap, 100);
                    }} else {{
                        console.error('AMap加载超时');
                        var newsList = document.getElementById('news-list');
                        newsList.innerHTML = '<div class="error-message">地图API加载超时，请检查网络连接或刷新页面重试。</div>';
                    }}
                }}
            }}
            
            // 开始检查AMap
            checkAMap();
        }});
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
    print("重庆交通新闻地图生成器（增强版）")
    print("=" * 60)
    
    generator = MapGenerator()
    generator.generate()


if __name__ == "__main__":
    main()
