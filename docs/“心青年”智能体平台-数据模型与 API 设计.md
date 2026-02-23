# 数据模型与 API 设计文档

## 1. 核心数据模型设计 (Data Models)

本部分定义核心实体及其属性，采用类 SQL/NoSQL 混合描述。

### 1.1 用户与角色体系

#### `User` (基础用户表)
系统所有用户的基表。
- `id`: BigInteger (PK)
- `username`: String (Unique)
- `email`: String (Unique)
- `gender`: String ['male', 'female', 'hidden']
- `password_hash`: String
- `nickname`: String
- `avatar`: String (URL)
- `roles`: JSON (Array<String>) ['family', 'volunteer', 'expert', 'admin', 'maintainer']  
	（JSON 数组，如 ['user', 'admin']，原生 JSON 存储）
- `status`: String ['active', 'banned', 'pending_review']
- `is_active`: Boolean
- `is_superuser`: Boolean
- `created_at`: DateTime
- `updated_at`: DateTime

#### `VolunteerProfile` (志愿者扩展表)
- `user_id`: BigInteger (FK -> User.id)
- `full_name`: String (真实姓名, 仅管理员可见)
- `phone`: String (手机号, 仅管理员可见)
- `public_email`: String (公开邮箱, 可选) 
- `is_public_visible`: Boolean (是否在志愿者墙展示)
- `service_hours`: String (累计服务时长)
- `skills`: String (擅长领域，JSON 字符串数组)
- `status`: String ['pending', 'approved', 'rejected'] (注册审核状态)
- `work_status`: String ['online', 'busy', 'offline'] (服务状态)

#### `ExpertProfile` (专家扩展表)
- `user_id`: BigInteger (FK -> User.id)
- `full_name`: String
- `phone`: String (仅管理员可见)
- `public_email`: String
- `title`: String (职称)
- `org`: String (所属机构)
- `skills`: String (擅长领域标签，JSON 字符串数组)
- `status`: String ['pending', 'approved', 'rejected']


#### `Session`（会话表）
用于持久化多端会话信息，支持统一身份校验与多端登录。

| 字段名        | 类型      | 说明               |
|--------------|----------|--------------------|
| session_id   | String   | 会话唯一标识 (PK)  |
| user_id      | BigInteger| 关联用户ID         |
| created_at   | DateTime | 会话创建时间       |
| expired_at   | DateTime | 会话过期时间       |
| user_agent   | String   | 客户端信息         |
| ip           | String   | 登录 IP 地址       |

---

### 1.2 知识库体系 (RAG Core)

#### `KnowledgeItem` (知识条目)
- `id`: Integer (PK)
- `title`: String
- `summary`: String (摘要)
- `content`: Text (Markdown 原始内容)
- `tags`: JSON
- `category`: String (如: "情绪干预", "生活自理")
- `risk_level`: String ['high', 'medium', 'low'] (风险等级)
- `document_type`: String (文档类型/证据等级)
- `target_audience`: JSON (适用人群)
- `applicable_age`: JSON (适用年龄)
- `author_id`: BigInteger (FK -> User.id, 贡献者)
- `status`: String ['draft', 'pending_review', 'published', 'rejected', 'archived']
- `review_comments`: Text (审核意见)
- `reviewed_by`: BigInteger (FK -> User.id, 审核专家)
- `reviewed_at`: DateTime
- `is_deleted`: Boolean (软删除标记)
- `created_at`: DateTime
- `updated_at`: DateTime

#### `KnowledgeChunk` (知识切片 - 向量化单元)
- `id`: Integer (PK)
- `item_id`: Integer (FK -> KnowledgeItem.id)
- `parent_id`: Integer (FK -> KnowledgeChunk.id, 父切片ID)
- `chunk_type`: String ['parent', 'child', 'independent'] (切片类型)
- `content_chunk`: Text (被切分的文本段)
- `chunk_metadata`: JSON (切片专属元数据)
- `vector_id`: String (向量数据库中的 ID)
- `sequence`: Integer (在原文中的顺序)

### 1.3 咨询与工单体系

#### `ConsultationSession` (RAG 智能对话会话)
- `id`: BigInteger (PK)
- `user_id`: BigInteger (FK -> User.id)
- `topic`: String (自动生成的会话摘要)
- `created_at`: DateTime
- `is_archived`: Boolean

#### `ConsultationMessage` (对话消息)
- `id`: BigInteger (PK)
- `session_id`: BigInteger (FK -> ConsultationSession.id)
- `role`: String ['user', 'ai']
- `content`: Text (markdown 格式)
- `sources`: Text (RAG 引用来源: [{title, id, score}])
- `created_at`: DateTime


#### `Ticket` (人工咨询工单)
- `id`: Integer (PK)
- `title`: String
- `description`: Text
- `category`: String
- `priority`: String ['low', 'medium', 'high']
- `status`: String ['open', 'claimed', 'processing', 'resolved', 'closed']
- `created_by`: Integer (FK -> User.id, 家属)
- `assigned_to`: Integer (FK -> User.id, 志愿者/专家)
- `assigned_by`: Integer (FK -> User.id, 管理员指派，可选)
- `created_at`: DateTime
- `resolved_at`: DateTime

#### `TicketComment` (工单回复记录)
- `id`: Integer (PK)
- `ticket_id`: Integer (FK -> Ticket.id)
- `user_id`: Integer
- `content`: Text
- `is_internal`: Boolean (是否仅内部可见)
- `created_at`: DateTime

### 1.4 志愿者活动体系

#### `Shift` (线下排班)
- `id`: Integer (PK)
- `title`: String
- `description`: String
- `location`: String
- `start_time`: DateTime
- `end_time`: DateTime
- `max_participants`: Integer
- `current_participants`: Integer
- `status`: String ['open', 'full', 'cancelled', 'completed']
- `created_by`: Integer (FK -> User.id, 管理员)

#### `ShiftApplication` (排班申请)
- `id`: Integer (PK)
- `shift_id`: Integer (FK -> Shift.id)
- `volunteer_id`: Integer (FK -> User.id)
- `status`: String ['pending', 'approved', 'rejected', 'cancelled']
- `attendance_status`: String ['pending', 'present', 'absent', 'late'] (考勤状态)
- `applied_at`: DateTime

---

## 2. API 接口定义 (RESTful)

### 2.1 认证与基础 (Auth)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| POST | `/api/auth/login` | 用户登录 | No |
| POST | `/api/auth/logout` | 用户登出 | Yes |
| POST | `/api/auth/register` | 用户注册（支持多角色与 profile 创建） | No |
| GET | `/api/auth/me` | 获取当前登录用户信息 (含 Roles & Profile概要) | Yes |
| PUT | `/api/auth/me` | 更新当前登录用户信息 | Yes |
| DELETE | `/api/auth/me` | 注销当前登录用户 | Yes |

### 2.2 用户管理 (Users & Profiles)

| Method | Endpoint | Description | Roles |
|---|---|---|---|
| GET | `/api/users/profile` | 获取当前用户详细档案 | Any |
| PUT | `/api/users/profile` | 更新当前用户详细档案 (含 Volunteer/Expert 字段) | Any |
| POST | `/api/users/apply-role` | 申请成为志愿者或专家 (上传资质) | Family |
| GET | `/api/admin/users` | (Admin) 用户列表，支持筛选 | Admin |
| POST | `/api/admin/users/:id/verify` | (Admin) 审核用户注册/角色申请 | Admin |
| GET | `/api/public/experts` | 获取公开专家列表 (专家墙) | Any |
| GET | `/api/public/volunteers` | 获取公开志愿者列表 (志愿者墙) | Any |

#### 用户注册（多角色与 profile 支持）

**请求参数示例：**
```json
{
	"username": "testuser",
	"password": "testpass123",
	"email": "testuser@example.com",
	"gender": "male",
	"nickname": "昵称",
	"roles": ["family", "volunteer", "expert"],
	"volunteer_info": {
		"full_name": "志愿者张三",
		"phone": "13800000000",
		"skills": ["陪伴", "心理疏导"],
		"is_public_visible": true
	},
	"expert_info": {
		"full_name": "专家李四",
		"title": "心理咨询师",
		"organization": "XX医院",
		"qualifications": ["cert1.pdf"],
		"specialties": ["孤独症干预"],
		"is_public_visible": false
	}
}
```

**参数说明：**
- `roles`：数组，支持 ["family", "volunteer", "expert"] 多角色注册。`admin`/`maintainer` 仅后台可创建。
- `volunteer_info`/`expert_info`：如注册对应角色，需传 profile 字段，详见数据模型。

**返回结构示例：**
```json
{
	"id": 1,
	"username": "testuser",
	"roles": ["family", "volunteer", "expert"],
	"status": "active",
	"volunteer_profile": {
		"status": "pending",
		"full_name": "志愿者张三",
		...
	},
	"expert_profile": {
		"status": "pending",
		"full_name": "专家李四",
		...
	}
}
```

**校验规则：**
- 注册志愿者/专家时，profile 字段必填，缺失时报 400/422。
- 注册 admin/maintainer 角色将被拒绝（400/403）。

**安全说明：**
- profile 敏感字段（如手机号、真实姓名）仅本人和管理员可见，普通接口返回时自动脱敏。


### 2.3 知识库 (Knowledge)

| Method | Endpoint | Description | Roles |
|---|---|---|---|
| GET | `/api/knowledge/items` | 搜索/列出已发布知识条目 | Any |
| GET | `/api/knowledge/items/:id` | 获取详情 | Any |
| POST | `/api/knowledge/items` | 提交知识条目 (草稿/待审核) | Volunteer, Expert, Admin |
| PUT | `/api/knowledge/items/:id` | 编辑条目 | Author, Expert, Admin |
| DELETE | `/api/knowledge/items/:id` | 删除条目 | Author, Expert, Admin |
| GET | `/api/knowledge/audit-list` | 获取待审核列表 | Expert, Admin |
| POST | `/api/knowledge/:id/audit` | 审核条目 (Pass/Reject + Comment) | Expert, Admin |
| POST | `/api/knowledge/upload` | 上传文件进行自动切片 | Volunteer, Expert, Admin |

### 2.4 智能咨询 (RAG Consultation)

| Method | Endpoint | Description | Roles |
|---|---|---|---|
| POST | `/api/consult/chat` | 发送消息并获取 AI 回复 (Stream) | Any |
| POST | `/api/consult/sessions` | 创建新会话 | Any |
| GET | `/api/consult/sessions` | 获取历史会话列表 | Any |
| GET | `/api/consult/sessions/:id` | 获取会话消息详情 | Any |
| DELETE | `/api/consult/sessions/:id` | 删除会话 | Any |

### 2.5 工单系统 (Tickets)

| Method | Endpoint | Description | Roles |
|---|---|---|---|
| POST | `/api/tickets` | 创建咨询工单 | Family |
| GET | `/api/tickets` | 获取工单列表 (Family看自己的, Volunteer/Expert看池子) | Any |
| GET | `/api/tickets/:id` | 工单详情 | Any |
| POST | `/api/tickets/:id/claim` | 认领工单 | Volunteer, Expert |
| POST | `/api/tickets/:id/reply` | 回复工单 | Volunteer, Expert |
| PATCH | `/api/tickets/:id/status` | 变更状态 (Close/Resolve) | Volunteer, Expert, Admin |

### 2.6 志愿者活动 (Shifts)

| Method | Endpoint | Description | Roles |
|---|---|---|---|
| GET | `/api/shifts` | 获取排班列表 | Volunteer, Admin |
| GET | `/api/shifts/:id` | 排班详情 | Volunteer, Admin |
| POST | `/api/shifts` | 创建排班 | Admin |
| POST | `/api/shifts/:id/apply` | 报名排班 | Volunteer |
| PATCH | `/api/shifts/applications/:id` | 审核报名/记录考勤 | Admin |

---


## 3. 设计原则与注意事项

1.  **鉴权机制**：所有非 `/public` 和 `/auth/login|register` 接口均需验证 JWT Token (Cookie 或 Header)。
2.  **Mock 策略**：前端开发期间，建议使用 `Mock.js` 或拦截器模拟上述 API 响应，确保字段名与本设计一致。
3.  **分页标准**：列表接口统一支持 query params: `page=1&limit=20`，返回结构 `{ items: [], total: 100 }`。
4.  **错误处理**：HTTP 状态码优先（200 OK, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 500 Server Error）。
5.  **时间格式**：所有时间字段推荐使用 ISO 8601 格式 (`YYYY-MM-DDTHH:mm:ssZ`)。
6.  **安全性**：敏感字段（这是 `phone`, `real_name`）在非 Admin 接口中必须脱敏或剔除。

