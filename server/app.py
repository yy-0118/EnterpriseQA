"""
企业知识库问答系统 - Flask应用主入口
整合所有模块并启动Web服务
"""
import logging
from flask import Flask
from flask_cors import CORS

from config import Config
from models import db

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)


def _seed_test_data():
    """自动导入测试数据（仅在首次运行时执行）"""
    import hashlib
    from models import User, KnowledgeCategory, Document, QAHistory

    def _md5(pwd):
        return hashlib.md5(pwd.encode('utf-8')).hexdigest()

    pwd = _md5('123456')

    # 用户
    users = [
        User(username='admin', password=pwd, role='admin', email='admin@enterprise.com', status=1),
        User(username='zhangsan', password=pwd, role='user', email='zhangsan@enterprise.com', status=1),
        User(username='lisi', password=pwd, role='user', email='lisi@enterprise.com', status=1),
        User(username='wangwu', password=pwd, role='user', email='wangwu@enterprise.com', status=1),
    ]
    db.session.add_all(users)
    db.session.flush()

    # 知识分类
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

    # 知识文档
    docs = [
        Document(title='员工考勤管理制度',
                 content='第一章 总则\n第一条 为规范公司考勤管理，维护正常工作秩序，特制定本制度。\n第二条 本制度适用于公司全体员工。\n\n第二章 工作时间\n第三条 公司实行标准工时制，工作时间为周一至周五，上午9:00-12:00，下午13:00-18:00。\n第四条 员工应按时上下班，不得无故迟到、早退或旷工。\n\n第三章 请假管理\n第五条 员工请假须提前申请，经部门负责人审批后方可休假。\n第六条 年假天数：工龄1-10年享5天，10-20年享10天，20年以上享15天。\n\n第四章 加班管理\n第七条 公司提倡高效工作，原则上不鼓励加班。\n\n第五章 违纪处理\n第八条 迟到30分钟以内扣款20元，超过30分钟按旷工半天处理。',
                 file_type='txt', category_id=5, chunk_count=5, uploaded_by=1),
        Document(title='费用报销流程指南',
                 content='一、报销范围\n1. 差旅费：交通费、住宿费、餐饮补贴\n2. 办公用品：日常消耗品\n3. 业务招待费：客户接待费用\n\n二、报销流程\n1. 填写《费用报销单》，附原始发票\n2. 部门经理审核（≤1000元直接审批）\n3. 超1000元需分管副总审批\n4. 超5000元需总经理审批\n5. 财务审核\n6. 出纳付款\n\n三、报销标准\n住宿：一线城市400元/晚，二线城市300元/晚\n餐饮补贴：80元/天',
                 file_type='txt', category_id=6, chunk_count=4, uploaded_by=1),
        Document(title='React前端开发规范',
                 content='# React前端开发规范\n\n## 项目结构\n- src/components: 通用组件\n- src/pages: 页面组件\n- src/hooks: 自定义Hooks\n\n## 命名规范\n- 组件文件: PascalCase (UserProfile.tsx)\n- 工具函数: camelCase (formatDate.ts)\n- 常量: UPPER_SNAKE_CASE\n\n## 组件规范\n- 使用函数组件和Hooks\n- 每个文件不超过300行\n- Props用TypeScript接口定义',
                 file_type='md', category_id=7, chunk_count=3, uploaded_by=1),
        Document(title='新员工入职指南',
                 content='欢迎加入公司！\n\n一、入职手续\n1. 携带身份证、学历证书原件及复印件\n2. 签订劳动合同\n3. 办理工牌和门禁卡\n4. 领取办公设备\n5. 开通企业邮箱和系统账号\n\n二、试用期\n1. 试用期一般为3个月\n2. 试用期工资为转正工资的80%\n\n三、薪酬福利\n1. 每月10日发工资\n2. 五险一金\n3. 每年健康体检\n4. 节日福利',
                 file_type='txt', category_id=4, chunk_count=5, uploaded_by=1),
        Document(title='Python代码规范',
                 content='# Python代码规范\n\n## 编码风格\n- 遵循PEP 8\n- 4空格缩进\n- 每行不超过120字符\n\n## 命名约定\n- 模块: lower_with_under.py\n- 类名: CapWords\n- 函数: lower_with_under()\n- 常量: CAPS_WITH_UNDER\n\n## 最佳实践\n- 列表推导式替代简单循环\n- 生成器处理大数据\n- context manager管理资源',
                 file_type='md', category_id=8, chunk_count=3, uploaded_by=1),
    ]
    db.session.add_all(docs)
    db.session.flush()

    # 问答历史
    qa_list = [
        QAHistory(user_id=2, question='公司的考勤制度是什么？',
                  answer='根据《员工考勤管理制度》，公司实行标准工时制，工作时间为周一至周五，上午9:00-12:00，下午13:00-18:00。迟到30分钟以内扣款20元。',
                  sources='[{"title":"员工考勤管理制度","score":0.92}]', feedback=1),
        QAHistory(user_id=2, question='如何报销差旅费？',
                  answer='报销流程：1.填写《费用报销单》附发票；2.部门经理审核；3.分级审批（1000/5000元为节点）；4.财务审核；5.出纳付款。',
                  sources='[{"title":"费用报销流程指南","score":0.95}]', feedback=1),
    ]
    db.session.add_all(qa_list)
    db.session.commit()
    logger.info('  ✓ 4个用户 | 8个分类 | 5个文档 | 2条问答历史')


def create_app() -> Flask:
    """
    创建并配置Flask应用
    注册所有蓝图、数据库、CORS等

    Returns:
        配置完成的Flask应用实例
    """
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(Config)

    # 配置CORS跨域支持（允许前端Vue3开发服务器访问）
    CORS(app, resources={
        r'/api/*': {
            'origins': '*',
            'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            'allow_headers': ['Content-Type', 'Authorization'],
        }
    })

    # 初始化数据库
    db.init_app(app)
    with app.app_context():
        # 检查数据库连接并自动初始化（SQLite模式）
        try:
            db.engine.connect()
            # 检查是否需要创建表（SQLite自动建表 + 导入测试数据）
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            if not tables or 'users' not in tables:
                logger.info('检测到数据库未初始化，正在自动创建表结构...')
                db.create_all()
                logger.info('表结构创建成功')

                # 自动导入测试数据
                from models import User, KnowledgeCategory, Document, QAHistory
                if not User.query.first():
                    logger.info('正在导入测试数据...')
                    _seed_test_data()
                    logger.info('测试数据导入成功')
            logger.info(f'数据库连接成功 [{app.config["SQLALCHEMY_DATABASE_URI"].split("://")[0]}]')
        except Exception as e:
            logger.warning(f'数据库连接失败: {e}')

    # 注册认证蓝图
    from auth import auth_bp
    app.register_blueprint(auth_bp)
    logger.info('已注册: 认证模块 (/api/auth)')

    # 注册问答蓝图
    from qa import qa_bp
    app.register_blueprint(qa_bp)
    logger.info('已注册: 智能问答模块 (/api/qa)')

    # 注册知识库蓝图
    from kb import kb_bp
    app.register_blueprint(kb_bp)
    logger.info('已注册: 知识库管理模块 (/api/kb)')

    # 注册管理员蓝图
    from admin import admin_bp
    app.register_blueprint(admin_bp)
    logger.info('已注册: 管理员后台模块 (/api/admin)')

    # 健康检查接口
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """健康检查接口"""
        return {'code': 200, 'message': '服务运行正常', 'data': {'status': 'ok'}}

    # ==================== 托管前端静态文件（生产模式） ====================
    # 构建前端后，静态文件在 server/static/ 目录
    import os as _os
    _static_dir = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'static')
    if _os.path.isdir(_static_dir):
        from flask import send_from_directory

        # API 404 处理器（必须在蓝图之前注册，但不能用 catch-all）
        # 前端页面 fallback 用 404 handler 处理

        def _safe_send(path):
            """安全发送静态文件，不存在返回 None"""
            try:
                return send_from_directory(_static_dir, path)
            except Exception:
                return None

        # 单独注册每个静态资源路由，避免拦截 API
        @app.route('/')
        def serve_index():
            return send_from_directory(_static_dir, 'index.html')

        @app.route('/favicon.svg')
        def serve_favicon():
            return _safe_send('favicon.svg')

        @app.route('/assets/<path:filename>')
        def serve_assets(filename):
            return send_from_directory(_os.path.join(_static_dir, 'assets'), filename)

        logger.info('已启用前端静态文件托管 (server/static/)')

    # 全局异常处理器
    @app.errorhandler(404)
    def not_found(error):
        """处理404: API返回JSON，前端页面返回index.html（SPA路由兜底）"""
        from flask import request as _req
        if _req.path.startswith('/api/'):
            return {'code': 404, 'message': '接口不存在'}, 404
        # SPA 前端页面，返回 index.html（如果静态目录存在）
        if _os.path.isdir(_static_dir):
            from flask import send_from_directory
            return send_from_directory(_static_dir, 'index.html')
        return {'code': 404, 'message': '接口不存在'}, 404

    @app.errorhandler(500)
    def server_error(error):
        """处理500错误，打印详细堆栈"""
        import traceback
        logger.error(f'服务器内部错误: {error}')
        traceback.print_exc()  # 强制打印完整错误堆栈到终端
        return {'code': 500, 'message': '服务器内部错误'}, 500

    return app


# 创建应用实例
app = create_app()

if __name__ == '__main__':
    import sys
    # 生产模式：使用 Waitress 多线程服务器（所有人可通过 IP 访问）
    if '--prod' in sys.argv:
        try:
            from waitress import serve
            logger.info('========================================')
            logger.info('  生产模式启动 (Waitress)')
            logger.info('  访问地址: http://0.0.0.0:5000')
            logger.info('  局域网内其他设备可通过你的IP访问')
            logger.info('========================================')
            serve(app, host='0.0.0.0', port=5000, threads=4)
        except ImportError:
            logger.warning('Waitress未安装，回退到开发服务器')
            logger.warning('安装命令: pip install waitress')
            app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        # 开发模式
        logger.info('开发模式启动: http://127.0.0.1:5000')
        logger.info('生产模式启动: python app.py --prod')
        app.run(host='0.0.0.0', port=5000, debug=False)
