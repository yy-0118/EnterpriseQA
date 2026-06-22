"""
数据库初始化脚本 — 支持 SQLite 和 MySQL 两种模式

用法:
    python init_db.py            # SQLite本地模式（无需安装MySQL）
    python init_db.py --mysql    # MySQL模式（需先手动执行 db.sql 建库）
"""
import sys
import os
import hashlib

# 确保在 server 目录下执行
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, KnowledgeCategory, Document, QAHistory


def md5_encrypt(password: str) -> str:
    """MD5加密"""
    md5 = hashlib.md5()
    md5.update(password.encode('utf-8'))
    return md5.hexdigest()


def _insert_test_data():
    """插入完整的测试数据"""
    pwd = md5_encrypt('123456')

    # ---- 用户 ----
    users = [
        User(username='admin', password=pwd, role='admin', email='admin@enterprise.com', status=1),
        User(username='zhangsan', password=pwd, role='user', email='zhangsan@enterprise.com', status=1),
        User(username='lisi', password=pwd, role='user', email='lisi@enterprise.com', status=1),
        User(username='wangwu', password=pwd, role='user', email='wangwu@enterprise.com', status=1),
    ]
    db.session.add_all(users)
    db.session.flush()

    # ---- 知识分类 ----
    cats = [
        KnowledgeCategory(name='公司制度', description='公司内部管理规章制度', parent_id=0),
        KnowledgeCategory(name='技术文档', description='技术开发相关文档资料', parent_id=0),
        KnowledgeCategory(name='产品手册', description='产品使用和操作手册', parent_id=0),
        KnowledgeCategory(name='培训资料', description='员工培训和学习材料', parent_id=0),
        KnowledgeCategory(name='人事管理', description='人事相关制度', parent_id=1),
        KnowledgeCategory(name='财务管理', description='财务报销等制度', parent_id=1),
        KnowledgeCategory(name='前端开发', description='前端技术栈文档', parent_id=2),
        KnowledgeCategory(name='后端开发', description='后端技术栈文档', parent_id=2),
    ]
    db.session.add_all(cats)
    db.session.flush()

    # ---- 知识文档 ----
    docs = [
        Document(
            title='员工考勤管理制度',
            content='第一章 总则\n第一条 为规范公司考勤管理，维护正常工作秩序，特制定本制度。\n第二条 本制度适用于公司全体员工。\n\n第二章 工作时间\n第三条 公司实行标准工时制，工作时间为周一至周五，上午9:00-12:00，下午13:00-18:00。\n第四条 员工应按时上下班，不得无故迟到、早退或旷工。\n\n第三章 请假管理\n第五条 员工请假须提前申请，经部门负责人审批后方可休假。\n第六条 请假类型包括：年假、事假、病假、婚假、产假、丧假等。\n第七条 年假天数：工龄1-10年享5天，10-20年享10天，20年以上享15天。\n\n第四章 加班管理\n第八条 公司提倡高效工作，原则上不鼓励加班。确需加班的，须提前报部门负责人审批。\n第九条 加班时间可申请调休或按国家规定计算加班费。\n\n第五章 违纪处理\n第十条 迟到30分钟以内扣款20元，超过30分钟按旷工半天处理。\n第十一条 连续旷工3天或年累计旷工7天，公司有权解除劳动合同。',
            file_type='txt', category_id=5, chunk_count=5, uploaded_by=1),
        Document(
            title='费用报销流程指南',
            content='一、报销范围\n1. 差旅费：包括交通费、住宿费、餐饮补贴\n2. 办公用品：日常办公消耗品\n3. 业务招待费：客户接待相关费用\n4. 培训费：经批准的外部培训费用\n\n二、报销流程\n1. 员工填写《费用报销单》，附上原始发票\n2. 部门经理审核签字（金额≤1000元可直接审批）\n3. 金额超过1000元需分管副总审批\n4. 超过5000元需总经理审批\n5. 财务部审核票据合规性\n6. 出纳付款\n\n三、报销标准\n1. 住宿标准：一线城市400元/晚，二线城市300元/晚，其他城市200元/晚\n2. 餐饮补贴：80元/天\n3. 市内交通实报实销，长途交通二等座/经济舱\n\n四、注意事项\n1. 发票须真实有效\n2. 报销须在费用发生后30日内提交\n3. 单次报销金额上限为20000元',
            file_type='txt', category_id=6, chunk_count=4, uploaded_by=1),
        Document(
            title='React前端开发规范',
            content='# React前端开发规范\n\n## 1. 项目结构\n- src/components: 通用组件\n- src/pages: 页面组件\n- src/hooks: 自定义Hooks\n- src/services: API服务层\n\n## 2. 命名规范\n- 组件文件使用PascalCase: UserProfile.tsx\n- 工具函数使用camelCase: formatDate.ts\n- 常量使用UPPER_SNAKE_CASE: API_BASE_URL\n\n## 3. 组件规范\n- 使用函数组件和Hooks，不使用类组件\n- 每个组件文件不超过300行\n- Props使用TypeScript接口定义\n\n## 4. 状态管理\n- 简单状态使用useState\n- 复杂状态使用useReducer\n- 全局状态使用Zustand或Context\n- 服务端数据使用React Query',
            file_type='md', category_id=7, chunk_count=3, uploaded_by=1),
        Document(
            title='Spring Boot后端开发规范',
            content='# Spring Boot后端开发规范\n\n## 1. 项目分层\n- Controller层: 接收请求，参数校验\n- Service层: 业务逻辑处理\n- DAO/Mapper层: 数据访问\n- Entity层: 数据库实体映射\n\n## 2. 命名规范\n- Controller: XxxController\n- Service接口: XxxService, 实现类: XxxServiceImpl\n- Mapper: XxxMapper\n\n## 3. RESTful API设计\n- GET /api/resource - 列表查询\n- GET /api/resource/{id} - 单个查询\n- POST /api/resource - 新增\n- PUT /api/resource/{id} - 更新\n- DELETE /api/resource/{id} - 删除\n\n## 4. 统一返回格式\n{"code": 200, "message": "success", "data": {}}',
            file_type='md', category_id=8, chunk_count=3, uploaded_by=1),
        Document(
            title='新员工入职指南',
            content='欢迎加入公司！\n\n一、入职手续\n1. 携带身份证、学历证书原件及复印件\n2. 签订劳动合同（一式两份）\n3. 办理工牌和门禁卡\n4. 领取办公设备（电脑、文具等）\n5. 开通企业邮箱和内部系统账号\n\n二、试用期管理\n1. 试用期一般为3个月，优秀者可提前转正\n2. 试用期工资为转正工资的80%\n3. 试用期内提前3天可提出离职\n\n三、薪酬福利\n1. 每月10日发放上月工资\n2. 五险一金按国家规定缴纳\n3. 每年一次健康体检\n4. 节日福利：春节、端午、中秋发放礼品\n\n四、办公环境\n1. 公司地址：科技园区A栋15层\n2. 办公时间：9:00-18:00，午休12:00-13:00\n3. 公司提供免费午餐和下午茶',
            file_type='txt', category_id=4, chunk_count=5, uploaded_by=1),
        Document(
            title='Python代码规范与最佳实践',
            content='# Python代码规范\n\n## 1. 编码风格\n- 严格遵循PEP 8规范\n- 使用4个空格缩进\n- 每行不超过120个字符\n\n## 2. 命名约定\n- 模块名: lower_with_under.py\n- 类名: CapWords\n- 函数/方法: lower_with_under()\n- 常量: CAPS_WITH_UNDER\n\n## 3. 类型注解\n- 所有公共函数必须添加类型注解\n- 使用mypy进行静态类型检查\n\n## 4. 最佳实践\n- 使用列表推导式替代简单循环\n- 使用生成器处理大数据集\n- 上下文管理器管理资源\n- 异常处理具体化',
            file_type='md', category_id=8, chunk_count=3, uploaded_by=1),
    ]
    db.session.add_all(docs)
    db.session.flush()

    # ---- 问答历史 ----
    qa_list = [
        QAHistory(
            user_id=2,
            question='公司的考勤制度是什么？',
            answer='根据《员工考勤管理制度》，公司实行标准工时制，工作时间为周一至周五，上午9:00-12:00，下午13:00-18:00。迟到30分钟以内扣款20元，超过30分钟按旷工半天处理。',
            sources='[{"title":"员工考勤管理制度","score":0.92}]',
            feedback=1),
        QAHistory(
            user_id=2,
            question='如何报销差旅费？',
            answer='差旅费报销流程：1.填写《费用报销单》并附上原始发票；2.部门经理审核签字；3.根据金额大小逐级审批；4.财务审核；5.出纳付款。住宿标准：一线城市400元/晚。',
            sources='[{"title":"费用报销流程指南","score":0.95}]',
            feedback=1),
        QAHistory(
            user_id=3,
            question='React组件命名规范是什么？',
            answer='React组件文件使用PascalCase命名，如UserProfile.tsx。组件使用函数组件和Hooks，每个文件不超过300行。Props使用TypeScript接口定义。',
            sources='[{"title":"React前端开发规范","score":0.88}]',
            feedback=1),
    ]
    db.session.add_all(qa_list)
    db.session.commit()

    print('   ✓ 4 个测试用户')
    print('   ✓ 8 个知识分类')
    print('   ✓ 6 个测试文档')
    print('   ✓ 3 条问答历史')


def _print_accounts():
    print('\n📋 测试账号 (密码均为 123456):')
    print('  管理员:  admin    / 123456')
    print('  普通用户: zhangsan / 123456')
    print('  普通用户: lisi     / 123456')
    print('  普通用户: wangwu   / 123456')


def init_sqlite():
    """SQLite 本地模式（无需 MySQL）"""
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///enterprise_qa.db'
    with app.app_context():
        db.create_all()
        print('✅ SQLite 表结构创建成功')

        if User.query.first():
            print('⚠️  已有数据，跳过测试数据导入')
        else:
            _insert_test_data()
            print('\n✅ 测试数据导入成功！')
        _print_accounts()


def init_mysql():
    """MySQL 模式（需先执行 db.sql）"""
    with app.app_context():
        try:
            count = User.query.count()
            print(f'✅ MySQL 连接成功，当前用户数: {count}')
            if count == 0:
                print('⚠️  数据库无数据，请先执行: mysql -uroot -p123456 -P3308 < db.sql')
                print('   或改用 SQLite 模式: python init_db.py')
            else:
                _print_accounts()
        except Exception as e:
            print(f'❌ MySQL 连接失败: {e}')
            print('   改用 SQLite 本地模式: python init_db.py')


if __name__ == '__main__':
    if '--mysql' in sys.argv:
        print('🔗 MySQL 模式...')
        init_mysql()
    else:
        print('🔗 SQLite 本地模式（无需 MySQL）...')
        print('   (需要 MySQL 请执行: python init_db.py --mysql)')
        init_sqlite()
