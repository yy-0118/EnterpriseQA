-- ============================================
-- 企业知识库问答系统 - 数据库初始化脚本
-- 数据库名: db_enterprise_qa
-- MySQL版本: 8.0
-- 端口: 3308
-- ============================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS db_enterprise_qa
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE db_enterprise_qa;

-- ============================================
-- 1. 用户表 (users)
-- 角色: admin=管理员, user=普通用户
-- 密码使用MD5加密存储
-- ============================================
DROP TABLE IF EXISTS `qa_history`;
DROP TABLE IF EXISTS `documents`;
DROP TABLE IF EXISTS `knowledge_categories`;
DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    `username` VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    `password` VARCHAR(128) NOT NULL COMMENT 'MD5加密后的密码',
    `role` ENUM('admin', 'user') NOT NULL DEFAULT 'user' COMMENT '角色: admin管理员, user普通用户',
    `email` VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
    `avatar` VARCHAR(255) DEFAULT NULL COMMENT '头像URL',
    `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 1启用, 0禁用',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_role` (`role`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================
-- 2. 知识分类表 (knowledge_categories)
-- ============================================
CREATE TABLE `knowledge_categories` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '分类ID',
    `name` VARCHAR(100) NOT NULL COMMENT '分类名称',
    `description` VARCHAR(500) DEFAULT NULL COMMENT '分类描述',
    `parent_id` INT DEFAULT 0 COMMENT '父分类ID, 0表示顶级分类',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX `idx_parent` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识分类表';

-- ============================================
-- 3. 文档表 (documents)
-- 记录上传到知识库的文档元信息
-- ============================================
CREATE TABLE `documents` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '文档ID',
    `title` VARCHAR(200) NOT NULL COMMENT '文档标题',
    `content` LONGTEXT NOT NULL COMMENT '文档内容',
    `file_type` VARCHAR(20) DEFAULT 'txt' COMMENT '文件类型: txt, pdf, docx, md',
    `category_id` INT DEFAULT NULL COMMENT '所属分类ID',
    `chunk_count` INT DEFAULT 0 COMMENT '文档分块数量',
    `uploaded_by` INT NOT NULL COMMENT '上传者用户ID',
    `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 1正常, 0已删除',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_category` (`category_id`),
    INDEX `idx_uploader` (`uploaded_by`),
    INDEX `idx_status` (`status`),
    FOREIGN KEY (`uploaded_by`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识文档表';

-- ============================================
-- 4. 问答历史表 (qa_history)
-- 记录用户的每次问答
-- ============================================
CREATE TABLE `qa_history` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    `user_id` INT NOT NULL COMMENT '提问用户ID',
    `question` TEXT NOT NULL COMMENT '用户问题',
    `answer` LONGTEXT NOT NULL COMMENT '系统回答',
    `sources` TEXT DEFAULT NULL COMMENT '参考来源文档(JSON格式)',
    `feedback` TINYINT DEFAULT NULL COMMENT '用户反馈: 1满意, 0不满意',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '提问时间',
    INDEX `idx_user` (`user_id`),
    INDEX `idx_created` (`created_at`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问答历史表';

-- ============================================
-- 测试数据
-- 密码: 123456 的MD5值 = e10adc3949ba59abbe56e057f20f883e
-- ============================================

-- 插入测试用户
INSERT INTO `users` (`username`, `password`, `role`, `email`, `status`) VALUES
('admin', 'e10adc3949ba59abbe56e057f20f883e', 'admin', 'admin@enterprise.com', 1),
('zhangsan', 'e10adc3949ba59abbe56e057f20f883e', 'user', 'zhangsan@enterprise.com', 1),
('lisi', 'e10adc3949ba59abbe56e057f20f883e', 'user', 'lisi@enterprise.com', 1),
('wangwu', 'e10adc3949ba59abbe56e057f20f883e', 'user', 'wangwu@enterprise.com', 1);

-- 插入知识分类
INSERT INTO `knowledge_categories` (`name`, `description`, `parent_id`) VALUES
('公司制度', '公司内部管理规章制度', 0),
('技术文档', '技术开发相关文档资料', 0),
('产品手册', '产品使用和操作手册', 0),
('培训资料', '员工培训和学习材料', 0),
('人事管理', '人事相关制度', 1),
('财务管理', '财务报销等制度', 1),
('前端开发', '前端技术栈文档', 2),
('后端开发', '后端技术栈文档', 2);

-- 插入测试文档
INSERT INTO `documents` (`title`, `content`, `file_type`, `category_id`, `chunk_count`, `uploaded_by`) VALUES
('员工考勤管理制度', '第一章 总则\n第一条 为规范公司考勤管理，维护正常工作秩序，根据国家相关法律法规，结合公司实际情况，特制定本制度。\n第二条 本制度适用于公司全体员工。\n\n第二章 工作时间\n第三条 公司实行标准工时制，工作时间为周一至周五，上午9:00-12:00，下午13:00-18:00。\n第四条 员工应按时上下班，不得无故迟到、早退或旷工。\n\n第三章 请假管理\n第五条 员工请假须提前申请，经部门负责人审批后方可休假。\n第六条 请假类型包括：年假、事假、病假、婚假、产假、丧假等。\n第七条 年假天数根据员工工龄确定：工龄1-10年享5天，10-20年享10天，20年以上享15天。\n\n第四章 加班管理\n第八条 公司提倡高效工作，原则上不鼓励加班。确需加班的，须提前报部门负责人审批。\n第九条 加班时间可申请调休或按国家规定计算加班费。\n\n第五章 违纪处理\n第十条 迟到30分钟以内扣款20元，超过30分钟按旷工半天处理。\n第十一条 连续旷工3天或年累计旷工7天，公司有权解除劳动合同。', 'txt', 5, 5, 1),
('费用报销流程指南', '一、报销范围\n1. 差旅费：包括交通费、住宿费、餐饮补贴\n2. 办公用品：日常办公消耗品\n3. 业务招待费：客户接待相关费用\n4. 培训费：经批准的外部培训费用\n\n二、报销流程\n1. 员工填写《费用报销单》，附上原始发票\n2. 部门经理审核签字（金额≤1000元可直接审批）\n3. 金额超过1000元需分管副总审批\n4. 超过5000元需总经理审批\n5. 财务部审核票据合规性\n6. 出纳付款\n\n三、报销标准\n1. 国内出差住宿标准：一线城市400元/晚，二线城市300元/晚，其他城市200元/晚\n2. 餐饮补贴：80元/天\n3. 交通：市内交通实报实销，长途交通二等座/经济舱\n\n四、注意事项\n1. 发票须真实有效，不得使用虚假发票\n2. 报销须在费用发生后30日内提交\n3. 单次报销金额上限为20000元\n4. 电子发票需打印后粘贴在报销单上', 'txt', 6, 4, 1),
('React前端开发规范', '# React前端开发规范\n\n## 1. 项目结构\n- src/components: 通用组件\n- src/pages: 页面组件\n- src/hooks: 自定义Hooks\n- src/services: API服务层\n- src/utils: 工具函数\n- src/store: 状态管理\n\n## 2. 命名规范\n- 组件文件使用PascalCase: UserProfile.tsx\n- 工具函数使用camelCase: formatDate.ts\n- 常量使用UPPER_SNAKE_CASE: API_BASE_URL\n- CSS模块使用kebab-case: user-profile.module.css\n\n## 3. 组件规范\n- 使用函数组件和Hooks，不使用类组件\n- 每个组件文件不超过300行\n- Props使用TypeScript接口定义\n- 组件导出使用默认导出\n\n## 4. 状态管理\n- 简单状态使用useState\n- 复杂状态使用useReducer\n- 全局状态使用Zustand或Context\n- 服务端数据使用React Query\n\n## 5. 代码质量\n- 使用ESLint + Prettier统一代码风格\n- 提交前运行单元测试\n- 组件至少包含基础渲染测试\n- 使用Husky管理Git Hooks', 'md', 7, 3, 1),
('Spring Boot后端开发规范', '# Spring Boot后端开发规范\n\n## 1. 项目分层\n- Controller层: 接收请求，参数校验\n- Service层: 业务逻辑处理\n- DAO/Mapper层: 数据访问\n- Entity层: 数据库实体映射\n- DTO层: 数据传输对象\n- Config层: 配置类\n\n## 2. 命名规范\n- Controller: XxxController\n- Service接口: XxxService, 实现类: XxxServiceImpl\n- Mapper: XxxMapper\n- Entity: 与数据库表名对应\n\n## 3. RESTful API设计\n- GET /api/resource - 列表查询\n- GET /api/resource/{id} - 单个查询\n- POST /api/resource - 新增\n- PUT /api/resource/{id} - 更新\n- DELETE /api/resource/{id} - 删除\n\n## 4. 统一返回格式\n{\n  "code": 200,\n  "message": "success",\n  "data": {}\n}\n\n## 5. 异常处理\n- 使用@RestControllerAdvice全局异常处理\n- 业务异常继承RuntimeException\n- 区分业务异常和系统异常\n\n## 6. 数据库规范\n- 使用MyBatis-Plus作为ORM框架\n- 所有表必须有id、created_at、updated_at字段\n- 软删除使用is_deleted标记\n- 金额使用BigDecimal类型', 'md', 8, 3, 1),
('新员工入职指南', '欢迎加入公司！以下是新员工入职需要了解的重要信息。\n\n一、入职手续\n1. 携带身份证、学历证书原件及复印件\n2. 签订劳动合同（一式两份）\n3. 办理工牌和门禁卡\n4. 领取办公设备（电脑、文具等）\n5. 开通企业邮箱和内部系统账号\n\n二、试用期管理\n1. 试用期一般为3个月，优秀者可提前转正\n2. 试用期工资为转正工资的80%\n3. 试用期内提前3天可提出离职\n4. 转正需通过转正答辩\n\n三、薪酬福利\n1. 每月10日发放上月工资\n2. 五险一金按国家规定缴纳\n3. 每年一次健康体检\n4. 节日福利：春节、端午、中秋发放礼品\n5. 团建活动：每季度一次部门团建\n\n四、办公环境\n1. 公司地址：科技园区A栋15层\n2. 办公时间：9:00-18:00，午休12:00-13:00\n3. 公司提供免费午餐和下午茶\n4. 地下停车场可免费使用\n\n五、常用系统\n1. OA系统：http://oa.company.com\n2. 企业邮箱：https://mail.company.com\n3. 代码仓库：http://gitlab.company.com\n4. 项目管理：http://jira.company.com\n5. 内部知识库：http://wiki.company.com', 'txt', 4, 5, 1),
('Python代码规范与最佳实践', '# Python代码规范\n\n## 1. 编码风格\n- 严格遵循PEP 8规范\n- 使用4个空格缩进\n- 每行不超过120个字符\n- 函数间空两行，方法间空一行\n\n## 2. 命名约定\n- 模块名: lower_with_under.py\n- 类名: CapWords\n- 函数/方法: lower_with_under()\n- 常量: CAPS_WITH_UNDER\n- 私有属性: _leading_underscore\n\n## 3. 类型注解\n- 所有公共函数必须添加类型注解\n- 使用mypy进行静态类型检查\n- 复杂类型使用TypeAlias\n\n## 4. 文档字符串\n- 使用Google风格或NumPy风格的docstring\n- 每个公共模块、类、方法都要有文档\n- 包含参数说明、返回值、异常\n\n## 5. 最佳实践\n- 使用列表推导式替代简单循环\n- 使用生成器处理大数据集\n- 上下文管理器管理资源\n- 使用dataclass替代简单数据容器\n- 异常处理具体化，不使用裸露的except', 'md', 8, 3, 1);

-- 插入测试问答历史
INSERT INTO `qa_history` (`user_id`, `question`, `answer`, `sources`, `feedback`) VALUES
(2, '公司的考勤制度是什么？', '根据《员工考勤管理制度》，公司实行标准工时制，工作时间为周一至周五，上午9:00-12:00，下午13:00-18:00。迟到30分钟以内扣款20元，超过30分钟按旷工半天处理。', '[{"title":"员工考勤管理制度","score":0.92}]', 1),
(2, '如何报销差旅费？', '差旅费报销流程：1.填写《费用报销单》并附上原始发票；2.部门经理审核签字；3.根据金额大小逐级审批；4.财务审核；5.出纳付款。住宿标准：一线城市400元/晚，二线城市300元/晚。', '[{"title":"费用报销流程指南","score":0.95}]', 1),
(3, 'React组件命名规范是什么？', 'React组件文件使用PascalCase命名，如UserProfile.tsx。组件使用函数组件和Hooks，每个文件不超过300行。Props使用TypeScript接口定义。', '[{"title":"React前端开发规范","score":0.88}]', 1),
(2, '新员工试用期多久？', '根据《新员工入职指南》，试用期一般为3个月，表现优秀者可提前转正。试用期工资为转正工资的80%，试用期内提前3天可提出离职。', '[{"title":"新员工入职指南","score":0.91}]', 1),
(3, 'Python项目如何命名文件？', 'Python模块文件使用小写字母加下划线命名（lower_with_under.py），类名使用CapWords风格，函数和方法使用lower_with_under()风格。私有属性以单下划线开头。', '[{"title":"Python代码规范与最佳实践","score":0.89}]', 1);
