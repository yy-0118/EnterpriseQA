"""
企业知识库问答系统 - 知识库管理模块
提供文档的上传、查询、删除等功能（支持手工输入和本地文件上传）
同时维护MySQL元数据和Chroma向量数据库
"""
import os
import logging

from flask import Blueprint, request, jsonify, g
from werkzeug.utils import secure_filename

from models import db, Document, KnowledgeCategory
from auth import login_required, admin_required
from rag_engine import get_rag_engine

# 创建知识库蓝图
kb_bp = Blueprint('kb', __name__, url_prefix='/api/kb')

logger = logging.getLogger(__name__)

# 允许上传的文件扩展名
ALLOWED_EXTENSIONS = {'txt', 'md', 'markdown'}
# 上传文件存放临时目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')


def _allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _read_file_content(filepath: str, filename: str) -> str:
    """
    读取上传文件内容，自动检测编码

    Args:
        filepath: 文件完整路径
        filename: 原始文件名

    Returns:
        文件文本内容
    """
    # 尝试常见编码依次读取
    for encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    # 最后兜底
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


@kb_bp.route('/documents', methods=['GET'])
@login_required
def list_documents():
    """
    获取知识库文档列表
    支持按分类筛选和分页

    Query Params:
        category_id: 分类ID(可选)
        page: 页码(默认1)
        page_size: 每页数量(默认20)
        keyword: 搜索关键词(可选)

    Returns:
        {
            "code": 200,
            "data": {
                "list": [...],
                "total": 50,
                "page": 1,
                "page_size": 20
            }
        }
    """
    category_id = request.args.get('category_id', type=int)
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '').strip()

    if page_size > 100:
        page_size = 100

    # 构建查询条件
    query = Document.query.filter_by(status=1)

    if category_id:
        query = query.filter_by(category_id=category_id)

    if keyword:
        query = query.filter(
            db.or_(
                Document.title.like(f'%{keyword}%'),
                Document.content.like(f'%{keyword}%'),
            )
        )

    # 按时间倒序排列
    query = query.order_by(Document.created_at.desc())

    total = query.count()
    documents = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        'code': 200,
        'data': {
            'list': [d.to_dict() for d in documents],
            'total': total,
            'page': page,
            'page_size': page_size,
        }
    })


@kb_bp.route('/documents/<int:doc_id>', methods=['GET'])
@login_required
def get_document(doc_id: int):
    """
    获取单个文档的完整内容

    Args:
        doc_id: 文档ID

    Returns:
        {"code": 200, "data": {"document": {...}}}
    """
    doc = Document.query.filter_by(id=doc_id, status=1).first()
    if not doc:
        return jsonify({'code': 404, 'message': '文档不存在'}), 404

    return jsonify({
        'code': 200,
        'data': {
            'document': doc.to_dict()
        }
    })


@kb_bp.route('/documents', methods=['POST'])
@login_required
def add_document():
    """
    上传新文档到知识库
    会将文档内容向量化并存储到Chroma

    Request Body:
        {
            "title": "公司考勤制度",
            "content": "文档完整内容...",
            "category_id": 1 (可选),
            "file_type": "txt" (可选，默认txt)
        }

    Returns:
        {"code": 200, "message": "上传成功", "data": {"document": {...}}}
    """
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请提供文档信息'}), 400

    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    category_id = data.get('category_id')
    file_type = data.get('file_type', 'txt')

    if not title:
        return jsonify({'code': 400, 'message': '文档标题不能为空'}), 400
    if not content:
        return jsonify({'code': 400, 'message': '文档内容不能为空'}), 400

    # 检查标题是否已存在
    existing = Document.query.filter_by(title=title, status=1).first()
    if existing:
        return jsonify({'code': 409, 'message': '文档标题已存在'}), 409

    # 创建文档记录
    doc = Document(
        title=title,
        content=content,
        file_type=file_type,
        category_id=category_id,
        uploaded_by=g.user_id,
        chunk_count=0,
    )

    try:
        db.session.add(doc)
        db.session.flush()  # 获取doc.id但不提交事务

        # 向量化并添加到Chroma
        rag = get_rag_engine()
        chunk_count = rag.add_documents(
            [{'id': doc.id, 'title': title, 'content': content}],
            doc_id_prefix=f'doc_{doc.id}'
        )
        doc.chunk_count = chunk_count

        db.session.commit()

        return jsonify({
            'code': 200,
            'message': f'文档上传成功，共生成 {chunk_count} 个向量块',
            'data': {
                'document': doc.to_dict(),
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'上传文档失败: {e}')
        return jsonify({'code': 500, 'message': f'上传失败: {str(e)}'}), 500


@kb_bp.route('/documents/upload', methods=['POST'])
@login_required
def upload_file():
    """
    上传本地文件到知识库（支持 .txt / .md）
    读取文件内容后自动创建文档并向量化

    Form Data:
        file: 上传的文件
        category_id: 知识分类ID（可选）

    Returns:
        {"code": 200, "message": "...", "data": {"document": {...}}}
    """
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '请选择要上传的文件'}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename:
        return jsonify({'code': 400, 'message': '请选择文件'}), 400

    if not _allowed_file(file.filename):
        return jsonify({
            'code': 400,
            'message': f'不支持的文件类型，目前只支持: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400

    # 确保上传目录存在
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 安全处理文件名并保存
    original_name = file.filename
    safe_name = secure_filename(original_name)
    filepath = os.path.join(UPLOAD_DIR, safe_name)
    file.save(filepath)

    # 读取文件内容
    try:
        content = _read_file_content(filepath, original_name)
    except Exception as e:
        logger.error(f'读取文件失败: {e}')
        return jsonify({'code': 500, 'message': f'读取文件内容失败: {str(e)}'}), 500

    if not content.strip():
        return jsonify({'code': 400, 'message': '文件内容为空'}), 400

    # 去掉扩展名作为文档标题
    title_parts = original_name.rsplit('.', 1)
    title = title_parts[0]
    file_type = title_parts[1].lower() if len(title_parts) > 1 else 'txt'
    if file_type == 'markdown':
        file_type = 'md'

    # 获取可选分类
    category_id = request.form.get('category_id', type=int)

    # 检查标题是否重复
    existing = Document.query.filter_by(title=title, status=1).first()
    if existing:
        return jsonify({'code': 409, 'message': f'文档「{title}」已存在，请先删除或改名后再上传'}), 409

    # 创建文档记录
    doc = Document(
        title=title,
        content=content,
        file_type=file_type,
        category_id=category_id,
        uploaded_by=g.user_id,
        chunk_count=0,
    )

    try:
        db.session.add(doc)
        db.session.flush()

        # 向量化
        rag = get_rag_engine()
        chunk_count = rag.add_documents(
            [{'id': doc.id, 'title': title, 'content': content}],
            doc_id_prefix=f'doc_{doc.id}'
        )
        doc.chunk_count = chunk_count
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': f'文件「{original_name}」上传成功，共生成 {chunk_count} 个向量块',
            'data': {'document': doc.to_dict()}
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'文件上传失败: {e}')
        return jsonify({'code': 500, 'message': f'上传失败: {str(e)}'}), 500
    finally:
        # 删除临时文件
        try:
            os.remove(filepath)
        except OSError:
            pass


@kb_bp.route('/documents/<int:doc_id>', methods=['DELETE'])
@admin_required
def delete_document(doc_id: int):
    """
    删除文档(软删除)
    同时从Chroma向量数据库中移除

    Args:
        doc_id: 文档ID

    Returns:
        {"code": 200, "message": "删除成功"}
    """
    doc = Document.query.get(doc_id)
    if not doc:
        return jsonify({'code': 404, 'message': '文档不存在'}), 404

    try:
        # 从向量数据库删除
        rag = get_rag_engine()
        rag.delete_documents(doc.title)

        # 从MySQL软删除
        doc.status = 0
        db.session.commit()

        return jsonify({'code': 200, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除文档失败: {e}')
        return jsonify({'code': 500, 'message': f'删除失败: {str(e)}'}), 500


@kb_bp.route('/documents/<int:doc_id>', methods=['PUT'])
@admin_required
def update_document(doc_id: int):
    """
    更新文档内容和元信息

    Args:
        doc_id: 文档ID

    Request Body:
        {
            "title": "新标题",
            "content": "新内容",
            "category_id": 2
        }

    Returns:
        {"code": 200, "message": "更新成功"}
    """
    doc = Document.query.filter_by(id=doc_id, status=1).first()
    if not doc:
        return jsonify({'code': 404, 'message': '文档不存在'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请提供更新信息'}), 400

    try:
        # 更新文档内容
        content_changed = False
        if 'title' in data:
            doc.title = data['title'].strip()
        if 'content' in data:
            doc.content = data['content'].strip()
            content_changed = True
        if 'category_id' in data:
            doc.category_id = data['category_id']

        # 如果内容变更，重新向量化
        if content_changed:
            rag = get_rag_engine()
            # 删除旧的向量
            rag.delete_documents(doc.title)
            # 添加新的向量
            chunk_count = rag.add_documents(
                [{'id': doc.id, 'title': doc.title, 'content': doc.content}],
                doc_id_prefix=f'doc_{doc.id}'
            )
            doc.chunk_count = chunk_count

        db.session.commit()
        return jsonify({'code': 200, 'message': '更新成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新文档失败: {e}')
        return jsonify({'code': 500, 'message': f'更新失败: {str(e)}'}), 500


@kb_bp.route('/categories', methods=['GET'])
@login_required
def list_categories():
    """
    获取知识分类列表

    Returns:
        {"code": 200, "data": {"categories": [...]}}
    """
    categories = KnowledgeCategory.query.order_by(
        KnowledgeCategory.parent_id,
        KnowledgeCategory.id
    ).all()

    # 构建分类树结构
    category_map = {}
    tree = []
    for cat in categories:
        cat_dict = cat.to_dict()
        cat_dict['children'] = []
        category_map[cat.id] = cat_dict

        if cat.parent_id == 0 or cat.parent_id is None:
            tree.append(cat_dict)
        elif cat.parent_id in category_map:
            category_map[cat.parent_id]['children'].append(cat_dict)

    return jsonify({
        'code': 200,
        'data': {
            'categories': tree,
        }
    })


@kb_bp.route('/categories', methods=['POST'])
@admin_required
def add_category():
    """
    添加知识分类

    Request Body:
        {
            "name": "新分类",
            "description": "分类描述",
            "parent_id": 0
        }

    Returns:
        {"code": 200, "message": "添加成功"}
    """
    data = request.get_json()
    if not data or not data.get('name', '').strip():
        return jsonify({'code': 400, 'message': '分类名称不能为空'}), 400

    try:
        cat = KnowledgeCategory(
            name=data['name'].strip(),
            description=data.get('description', '').strip() or None,
            parent_id=data.get('parent_id', 0),
        )
        db.session.add(cat)
        db.session.commit()
        return jsonify({'code': 200, 'message': '添加成功', 'data': {'category': cat.to_dict()}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'添加失败: {str(e)}'}), 500
