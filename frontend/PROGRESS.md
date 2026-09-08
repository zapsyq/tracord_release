# Tracord 开发进度

## 2026-05-24

### 已完成
- 主页框架：标题栏 + 底部 4 Tab 导航（地图/记录/规划/我的）
- 新粗野主义导航样式：选中态白底黑边框 + 偏移阴影
- 地图页占位：对角线斜线纹理 + 长按弹出"点亮/规划"菜单
- 定位标记：地图底部定位 pin
- 代码精简：仅 dio + provider 两个依赖

### 当前项目结构
```
lib/
├── main.dart
├── app.dart
├── core/
│   ├── theme/app_theme.dart
│   ├── network/api_config.dart
│   ├── network/api_client.dart
│   └── storage/token_storage.dart
└── features/
    ├── auth/                       ← ✅ 注册登录完成
    ├── map/                        ← 🚧 地图框架就绪，待接高德 SDK
    │   ├── pages/map_page.dart
    │   └── widgets/city_popup.dart
    ├── home/pages/home_page.dart    ← ✅ 主页框架就绪
    ├── records/pages/              ← 占位
    ├── planning/pages/             ← 占位
    └── profile/pages/              ← 占位
```

### 待完成
- 接入高德 SDK（Android 模拟器）
- 记录/规划/我的页面
- 智能体模块

### 关键信息
- 后端地址：http://127.0.0.1:8000
- 项目位置：d:\VSCode\tracord\frontend
