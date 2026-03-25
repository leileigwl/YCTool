# YCTool - 报价单管理系统

一个支持多公司使用的报价单管理系统，支持中英文双语 PDF 导出。

## 功能特性

- **多公司支持**：可配置多个公司信息，灵活切换
- **客户管理**：管理客户信息和联系方式
- **产品管理**：支持产品批量导入、图片上传
- **报价单生成**：一键生成中/英文报价单 PDF
- **数据导出**：支持 PDF 和 Excel 格式导出

## 技术栈

- **后端**：Python Flask
- **数据库**：SQLite
- **PDF 生成**：ReportLab
- **部署**：Docker

## 快速开始

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python database.py

# 启动服务
python app.py
```

访问 http://localhost:5002

### Docker 部署

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f
```

## 项目结构

```
YCTool/
├── app.py              # Flask 应用入口
├── models.py           # 数据模型
├── routes.py           # 路由定义
├── database.py         # 数据库初始化
├── utils/
│   └── pdf_generator.py # PDF 生成器
├── templates/          # HTML 模板
├── static/
│   ├── fonts/          # 中文字体
│   └── uploads/        # 上传文件
├── Dockerfile
└── docker-compose.yml
```

## 配置

首次运行后，在系统中配置公司信息：
- 公司名称（中/英文）
- 银行账户信息
- 联系方式

## License

MIT
