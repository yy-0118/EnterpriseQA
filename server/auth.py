"""
企业知识库问答系统 - 用户认证模块
提供登录、注册、用户信息获取等API
"""
import hashlib
import jwt
import time
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Blueprint, request, jsonify, g

from models import db, User
from config import Config

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def md5_encrypt(password: str) -> str:
    """
    对密码进行MD5加密

    Args:
        password: 原始密码

    Returns:
        MD5加密后的32位十六进制字符串
    """
    md5 = hashlib.md5()
    md5.update(password.encode('utf-8'))
    return md5.hexdigest()


def generate_token(user_id: int, username: str, role: str) -> str:
    """
    生成JWT令牌

    Args:
        user_id: 用户ID
        username: 用户名
        role: 用户角色

    Returns:
        JWT Token字符串
    """
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES),
        'iat': datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')
    return token


def login_required(f):
    """
    登录验证装饰器
    验证请求头中的JWT Token，并将用户信息存入g对象

    Usage:
        @login_required
        def protected_route():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '')
        # 格式: Bearer <token>
        if token.startswith('Bearer '):
            token = token[7:]

        if not token:
            return jsonify({'code': 401, 'message': '请先登录'}), 401

        try:
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            g.user_id = payload['user_id']
            g.username = payload['username']
            g.role = payload['role']
        except jwt.ExpiredSignatureError:
            return jsonify({'code': 401, 'message': '登录已过期，请重新登录'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'code': 401, 'message': '无效的Token'}), 401

        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """
    管理员权限验证装饰器
    在login_required基础上验证用户是否为管理员

    Usage:
        @admin_required
        def admin_route():
            ...
    """
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if g.role != 'admin':
            return jsonify({'code': 403, 'message': '需要管理员权限'}), 403
        return f(*args, **kwargs)

    return decorated


@auth_bp.route('/login', methods=['POST'])
def login():
    import traceback
    from flask import current_app
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请提供登录信息'}), 400

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400

        # 诊断: 打印当前请求使用的数据库连接信息
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', 'N/A')
        print(f"[LOGIN] 当前数据库: {db_uri.split('://')[0]}")

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'code': 401, 'message': '用户名或密码错误'}), 401

        if user.password != md5_encrypt(password):
            return jsonify({'code': 401, 'message': '用户名或密码错误'}), 401

        if user.status != 1:
            return jsonify({'code': 403, 'message': '账号已被禁用，请联系管理员'}), 403

        token = generate_token(user.id, user.username, user.role)

        return jsonify({
            'code': 200,
            'message': '登录成功',
            'data': {
                'token': token,
                'user': user.to_dict(),
            }
        })
    except Exception as e:
        print("="*50)
        print("【登录接口报错】")
        traceback.print_exc()
        print("="*50)
        return jsonify({'code': 500, 'message': f'服务器内部错误: {str(e)}'}), 500


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册接口
    新用户默认角色为普通用户

    Request Body:
        {
            "username": "newuser",
            "password": "123456",
            "email": "user@example.com" (可选)
        }

    Returns:
        {
            "code": 200,
            "message": "注册成功",
            "data": { "user": {...} }
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请提供注册信息'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    email = data.get('email', '').strip()

    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400

    if len(username) < 3 or len(username) > 50:
        return jsonify({'code': 400, 'message': '用户名长度需在3-50个字符之间'}), 400

    if len(password) < 6:
        return jsonify({'code': 400, 'message': '密码长度不能少于6个字符'}), 400

    # 检查用户名是否已存在
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'code': 409, 'message': '用户名已被注册'}), 409

    # 创建新用户
    new_user = User(
        username=username,
        password=md5_encrypt(password),
        role='user',
        email=email if email else None,
        status=1,
    )

    try:
        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '注册成功',
            'data': {
                'user': new_user.to_dict(),
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'注册失败: {str(e)}'}), 500


@auth_bp.route('/userinfo', methods=['GET'])
@login_required
def get_userinfo():
    """
    获取当前登录用户信息

    Returns:
        {
            "code": 200,
            "data": { "user": {...} }
        }
    """
    user = User.query.get(g.user_id)
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404

    return jsonify({
        'code': 200,
        'data': {
            'user': user.to_dict(),
        }
    })
