"""
企业知识库问答系统 - 管理员后台模块
提供数据统计、用户管理、系统概览等管理功能
"""
import logging
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, g
from sqlalchemy import func, extract

from models import db, User, Document, QAHistory
from auth import admin_required
from rag_engine import get_rag_engine

# 创建管理员蓝图
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

logger = logging.getLogger(__name__)


@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def dashboard():
    """
    管理员首页仪表盘数据
    返回系统核心统计指标

    Returns:
        {
            "code": 200,
            "data": {
                "user_count": 50,
                "doc_count": 120,
                "qa_count": 500,
                "vector_chunks": 2000,
                ...
            }
        }
    """
    # 用户总数
    user_count = User.query.filter_by(status=1).count()

    # 文档总数
    doc_count = Document.query.filter_by(status=1).count()

    # 问答总数
    qa_count = QAHistory.query.count()

    # 今日问答数
    today = datetime.now().date()
    today_qa_count = QAHistory.query.filter(
        func.date(QAHistory.created_at) == today
    ).count()

    # 知识库向量块总数
    rag = get_rag_engine()
    vector_stats = rag.get_collection_stats()

    # === 近7天问答趋势数据(用于折线图) ===
    trend_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        count = QAHistory.query.filter(
            func.date(QAHistory.created_at) == date
        ).count()
        trend_data.append({
            'date': date.strftime('%m-%d'),
            'count': count,
        })

    # === 文档分类分布数据(用于饼图) ===
    category_stats = db.session.query(
        Document.category_id,
        func.count(Document.id).label('count')
    ).filter(
        Document.status == 1,
        Document.category_id.isnot(None)
    ).group_by(Document.category_id).all()

    from models import KnowledgeCategory
    category_data = []
    for cat_id, count in category_stats:
        cat = KnowledgeCategory.query.get(cat_id)
        category_data.append({
            'name': cat.name if cat else '未分类',
            'value': count,
        })

    # === 用户活跃度排行(TOP10) ===
    user_activity = db.session.query(
        QAHistory.user_id,
        User.username,
        func.count(QAHistory.id).label('qa_count')
    ).join(User, QAHistory.user_id == User.id).group_by(
        QAHistory.user_id, User.username
    ).order_by(func.count(QAHistory.id).desc()).limit(10).all()

    user_activity_data = [
        {'username': username, 'count': count}
        for _, username, count in user_activity
    ]

    # === 近12个月问答趋势(用于柱状图) ===
    monthly_trend = []
    for i in range(11, -1, -1):
        date = today.replace(day=1) - timedelta(days=1)
        date = (date.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        year, month = date.year, date.month
        count = QAHistory.query.filter(
            extract('year', QAHistory.created_at) == year,
            extract('month', QAHistory.created_at) == month,
        ).count()
        monthly_trend.append({
            'month': f'{year}-{month:02d}',
            'count': count,
        })

    return jsonify({
        'code': 200,
        'data': {
            'user_count': user_count,
            'doc_count': doc_count,
            'qa_count': qa_count,
            'today_qa_count': today_qa_count,
            'vector_chunks': vector_stats.get('total_chunks', 0),
            'trend_data': trend_data,  # 近7天趋势
            'category_data': category_data,  # 分类分布
            'user_activity': user_activity_data,  # 用户活跃度
            'monthly_trend': monthly_trend,  # 月度趋势
        }
    })


@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """
    用户管理列表
    支持分页和搜索

    Query Params:
        page: 页码
        page_size: 每页数量
        keyword: 搜索关键词

    Returns:
        {"code": 200, "data": {"list": [...], "total": 50}}
    """
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '').strip()

    if page_size > 100:
        page_size = 100

    query = User.query.filter_by(status=1)

    if keyword:
        query = query.filter(
            db.or_(
                User.username.like(f'%{keyword}%'),
                User.email.like(f'%{keyword}%'),
            )
        )

    query = query.order_by(User.created_at.desc())
    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()

    # 为每个用户统计问答次数
    user_list = []
    for u in users:
        u_dict = u.to_dict()
        u_dict['qa_count'] = QAHistory.query.filter_by(user_id=u.id).count()
        u_dict['doc_count'] = Document.query.filter_by(uploaded_by=u.id, status=1).count()
        user_list.append(u_dict)

    return jsonify({
        'code': 200,
        'data': {
            'list': user_list,
            'total': total,
            'page': page,
            'page_size': page_size,
        }
    })


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id: int):
    """
    更新用户信息（角色、状态等）

    Request Body:
        {
            "role": "admin",
            "status": 1,
            "email": "..."
        }

    Returns:
        {"code": 200, "message": "更新成功"}
    """
    user = User.query.filter_by(id=user_id, status=1).first()
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请提供更新信息'}), 400

    try:
        if 'role' in data and data['role'] in ['admin', 'user']:
            user.role = data['role']
        if 'status' in data:
            user.status = data['status']
        if 'email' in data:
            user.email = data['email']

        db.session.commit()
        return jsonify({'code': 200, 'message': '更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'更新失败: {str(e)}'}), 500


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id: int):
    """
    删除用户（软删除，设置status=0）

    Args:
        user_id: 用户ID

    Returns:
        {"code": 200, "message": "删除成功"}
    """
    user = User.query.filter_by(id=user_id, status=1).first()
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404

    # 不允许删除自己
    if user.id == g.user_id:
        return jsonify({'code': 400, 'message': '不能删除自己的账号'}), 400

    try:
        user.status = 0
        db.session.commit()
        return jsonify({'code': 200, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'删除失败: {str(e)}'}), 500


@admin_bp.route('/qa/history', methods=['GET'])
@admin_required
def list_all_qa_history():
    """
    查看所有用户的问答历史（管理员视角）
    支持分页和筛选

    Query Params:
        page: 页码
        page_size: 每页数量
        keyword: 搜索关键词
        user_id: 按用户筛选

    Returns:
        {"code": 200, "data": {"list": [...], "total": 100}}
    """
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    filter_user_id = request.args.get('user_id', type=int)

    if page_size > 100:
        page_size = 100

    query = QAHistory.query

    if keyword:
        query = query.filter(
            db.or_(
                QAHistory.question.like(f'%{keyword}%'),
                QAHistory.answer.like(f'%{keyword}%'),
            )
        )
    if filter_user_id:
        query = query.filter_by(user_id=filter_user_id)

    query = query.order_by(QAHistory.created_at.desc())
    total = query.count()
    histories = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        'code': 200,
        'data': {
            'list': [h.to_dict() for h in histories],
            'total': total,
            'page': page,
            'page_size': page_size,
        }
    })
