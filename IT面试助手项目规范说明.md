# IT面试助手项目规范说明

## 项目概述
构建一个基于AI的IT技术面试训练平台，通过Gemini API提供英语面试模拟和代码讲解服务，帮助新人准备IT行业技术面试。

## 技术栈选择
### 核心技术
- 后端框架：FastAPI（比直接使用Gradio更灵活，便于后续扩展）
- 前端界面：Gradio（用于快速构建交互界面）
- AI服务：
  - Gemini API（主要对话模型）
  - Hugging Face Transformers（用于代码分析和补充）
- 数据库：SQLite（存储面试记录和用户反馈）
- 开发工具：Cursor

### 补充技术
- python-dotenv（环境变量管理）
- langchain（用于构建复杂的对话链）
- pandas（数据处理）
- pytest（单元测试）
- black（代码格式化）
- pre-commit（代码提交前检查）

## 项目结构
```
it-interview-assistant/
├── .env
├── .gitignore
├── README.md
├── requirements.txt
├── setup.py
├── tests/
├── data/
│   ├── interview_questions.json
│   └── code_samples/
└── src/
    ├── main.py
    ├── config.py
    ├── api/
    │   ├── __init__.py
    │   ├── routes.py
    │   └── models.py
    ├── core/
    │   ├── __init__.py
    │   ├── interview_engine.py
    │   ├── code_analyzer.py
    │   └── feedback_manager.py
    ├── database/
    │   ├── __init__.py
    │   └── models.py
    └── ui/
        ├── __init__.py
        └── gradio_app.py
```

## 核心功能模块

### 1. 面试官模拟器（Interview Simulator）
```python
# 功能说明
- 多种面试场景支持（初级、中级、高级）
- 根据简历和岗位动态调整问题难度
- 自然对话流和跟进性提问
- 实时反馈和建议
```

### 2. 代码分析器（Code Analyzer）
```python
# 功能说明
- 实时代码评审
- 性能优化建议
- 最佳实践推荐
- 常见错误检测
```

### 3. 技术点讲解器（Tech Explainer）
```python
# 功能说明
- 深入解释技术概念
- 提供实际应用案例
- 相关知识点联系
- 学习路径建议
```

### 4. 反馈系统（Feedback System）
```python
# 功能说明
- 面试表现评分
- 改进建议生成
- 进度追踪
- 学习计划制定
```

## API设计

### 1. 面试会话管理
```python
@app.post("/interview/start")
@app.post("/interview/question")
@app.post("/interview/feedback")
@app.post("/interview/end")
```

### 2. 代码分析服务
```python
@app.post("/code/analyze")
@app.post("/code/optimize")
@app.post("/code/explain")
```

### 3. 学习追踪
```python
@app.post("/progress/track")
@app.get("/progress/report")
```

## Gemini API提示词模板

### 1. 面试官角色设定
```text
You are an experienced IT technical interviewer. Conduct the interview in English.
Focus on {position_level} level {technology} position.
Evaluate candidate's responses and provide follow-up questions based on their answers.
```

### 2. 代码分析提示
```text
Analyze the following code snippets for:
1. Time and space complexity
2. Best practices compliance
3. Potential improvements
4. Security considerations
Provide explanations in English with clear examples.
```

## Gradio界面设计

### 1. 主界面组件
```python
- 面试模式选择（下拉菜单）
- 技术栈选择（多选框）
- 经验水平选择（单选框）
- 对话历史显示区
- 代码输入框（支持语法高亮）
- 反馈展示区
```

### 2. 可视化组件
```python
- 面试进度条
- 表现评分雷达图
- 知识点掌握热力图
- 学习进度追踪图表
```

## 数据库模型

### 1. 用户会话
```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    position_level TEXT,
    technologies TEXT,
    performance_score FLOAT
);
```

### 2. 面试记录
```sql
CREATE TABLE interview_records (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    question TEXT,
    answer TEXT,
    feedback TEXT,
    timestamp TIMESTAMP
);
```

## 部署配置

### 1. 环境变量
```env
GEMINI_API_KEY=your_api_key
HF_API_KEY=your_huggingface_key
DEBUG_MODE=True
DATABASE_URL=sqlite:///./interview_assistant.db
```

### 2. 依赖管理
```txt
fastapi>=0.68.0
gradio>=3.50.2
google-generativeai>=0.3.0
transformers>=4.30.0
langchain>=0.1.0
python-dotenv>=0.19.0
sqlalchemy>=1.4.23
pandas>=1.3.0
pytest>=6.2.5
```

## 测试规范

### 1. 单元测试
```python
- 面试引擎测试
- 代码分析器测试
- API端点测试
- 数据库操作测试
```

### 2. 集成测试
```python
- 完整面试流程测试
- API链路测试
- 界面交互测试
```

## 扩展建议

### 1. 后续功能
- 多语言支持
- 面试录音/录像
- AI驱动的简历优化
- 模拟项目面试
- 技术博客写作辅导

### 2. 性能优化
- 响应缓存
- 批量处理
- 异步操作
- 模型量化

## 开发流程

1. 环境搭建
2. 核心功能实现
3. API开发
4. 界面构建
5. 测试编写
6. 部署配置
7. 文档完善

请按照此规范使用Cursor进行开发，建议按照以下顺序：

1. 首先搭建基础项目结构
2. 实现核心的面试引擎
3. 开发API层
4. 构建Gradio界面
5. 添加数据持久化
6. 补充辅助功能
7. 完善测试用例
