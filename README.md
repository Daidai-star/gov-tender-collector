# 政府招标文件收集系统

FastAPI + Vue 的前后端一体化招标信息收集系统，支持定时抓取、公告检索、附件管理、AI 一键分析。

## 目录

- `/Users/yangqingyu/Documents/New project/backend`: 后端 API + 抓取引擎 + Worker
- `/Users/yangqingyu/Documents/New project/frontend`: 前端管理台与阅览界面
- `/Users/yangqingyu/Documents/New project/deploy`: Docker Compose 与 Nginx 配置

## 功能清单

- 每日三次定时抓取（09:00/14:00/21:00，可配置）
- 手动触发抓取任务
- 站点适配器机制（内置 `generic_html` + 河南三站预置适配器）
- 公告与附件存储，去重与版本记录
- 公告检索与详情阅览（支持收藏、仅收藏/仅AI已分析筛选）
- DeepSeek AI 一键分析
- RBAC：管理员/普通用户
- 用户管理（管理员新增用户/查看用户）

## 本地开发

### 1) 启动基础服务

```bash
cd /Users/yangqingyu/Documents/New\ project/deploy
docker compose up -d postgres redis
```

### 2) 启动后端 API 与 Worker

```bash
cd /Users/yangqingyu/Documents/New\ project/backend
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

另开终端：

```bash
cd /Users/yangqingyu/Documents/New\ project/backend
source .venv/bin/activate
python worker.py
```

### 3) 启动前端

```bash
cd /Users/yangqingyu/Documents/New\ project/frontend
npm install
npm run dev
```

## Ubuntu 一体化部署

```bash
cd /Users/yangqingyu/Documents/New\ project/backend
cp .env.example .env
# 编辑 .env 填写 SECRET_KEY 与 DEEPSEEK_API_KEY

cd /Users/yangqingyu/Documents/New\ project/deploy
docker compose up -d --build
```

访问：
- 前端: `http://<server-ip>/`
- API 健康检查: `http://<server-ip>/healthz`

默认管理员（首次自动种子）：
- 用户名: `admin`
- 密码: `admin123456`

## 关键 API

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/auth/users`
- `POST /api/v1/auth/users`
- `GET /api/v1/sites`
- `POST /api/v1/sites`
- `PUT /api/v1/sites/{site_id}`
- `POST /api/v1/sites/bootstrap/henan`
- `POST /api/v1/crawl/run`
- `GET /api/v1/notices`
- `GET /api/v1/notices/{id}`
- `POST /api/v1/notices/{id}/analyze`
- `POST /api/v1/notices/{id}/favorite`
- `DELETE /api/v1/notices/{id}/favorite`
- `GET /api/v1/tasks`
- `GET /api/v1/tasks/stats`

## 首批站点接入说明

### 一键导入（已预置河南三站）

站点管理页点击“导入河南三站”，或调用：

```bash
curl -X POST http://<server-ip>/api/v1/sites/bootstrap/henan \
  -H "Authorization: Bearer <token>"
```

预置站点：
- 河南省公共资源交易中心 `https://hnsggzyjy.henan.gov.cn/`
- 新乡市政府采购网 `https://xinxiang.zfcg.henan.gov.cn/`
- 郑州市公共资源交易中心 `https://zzggzy.zhengzhou.gov.cn/`

导入后可直接手动触发抓取；若某站点页面结构有差异，可按下方方式调整 `parser_rules`。

按招标类型触发抓取示例：

```bash
curl -X POST http://<server-ip>/api/v1/crawl/run \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"tender_types":["公开招标","竞争性磋商"]}'
```

示例 `parser_rules`：

```json
{
  "use_browser": false,
  "list_link_selector": ".article-list a",
  "detail_content_selector": ".article-content",
  "attachment_selector": ".article-content a",
  "publish_time_selector": ".pub-time",
  "tender_type_keywords": {
    "公开招标": ["公开招标", "招标公告"],
    "竞争性磋商": ["竞争性磋商"],
    "竞争性谈判": ["竞争性谈判"],
    "单一来源": ["单一来源"]
  }
}
```
