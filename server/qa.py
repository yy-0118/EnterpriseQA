"""
企业知识库问答系统 - 智能问答模块
基于RAG引擎实现知识库检索问答
"""
import json
import logging

from flask import Blueprint, request, jsonify, g

from models import db, QAHistory
from auth import login_required
from rag_engine import get_rag_engine, check_ollama_alive

qa_bp = Blueprint('qa', __name__, url_prefix='/api/qa')

logger = logging.getLogger(__name__)


@qa_bp.route('/ask', methods=['POST'])
@login_required
def ask_question():
    """
    RAG智能问答接口
    无需依赖Ollama也能返回结果（降级为关键词匹配）
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'code': 400, 'message': '请提供问题'}), 400

    question = (data.get('question', '') or '').strip()
    if not question:
        return jsonify({'code': 400, 'message': '问题不能为空'}), 400

    # 获取RAG引擎并执行检索
    try:
        rag = get_rag_engine()
        answer, sources, mode = rag.search(question)
    except Exception as e:
        logger.error(f'RAG引擎异常: {e}')
        import traceback
        traceback.print_exc()
        answer = f'问答引擎异常: {str(e)}'
        sources = []
        mode = '异常'

    # 保存历史
    history_id = None
    try:
        history = QAHistory(
            user_id=g.user_id,
            question=question,
            answer=answer,
            sources=json.dumps(sources, ensure_ascii=False),
        )
        db.session.add(history)
        db.session.commit()
        history_id = history.id
    except Exception as e:
        db.session.rollback()
        logger.error(f'保存历史失败: {e}')

    return jsonify({
        'code': 200,
        'message': 'ok',
        'data': {
            'question': question,
            'answer': answer,
            'sources': sources,
            'history_id': history_id,
            'mode': mode,
        }
    })


@qa_bp.route('/history', methods=['GET'])
@login_required
def get_history():
    """获取当前用户的问答历史"""
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 100)

    query = QAHistory.query.filter_by(user_id=g.user_id).order_by(QAHistory.created_at.desc())
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


@qa_bp.route('/feedback/<int:history_id>', methods=['POST'])
@login_required
def submit_feedback(history_id: int):
    """提交问答反馈（满意/不满意）"""
    data = request.get_json(silent=True)
    if not data or data.get('feedback') not in [0, 1]:
        return jsonify({'code': 400, 'message': '请提供有效反馈(0或1)'}), 400

    history = QAHistory.query.get(history_id)
    if not history:
        return jsonify({'code': 404, 'message': '记录不存在'}), 404
    if history.user_id != g.user_id:
        return jsonify({'code': 403, 'message': '无权操作'}), 403

    try:
        history.feedback = data['feedback']
        db.session.commit()
        return jsonify({'code': 200, 'message': '反馈成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500


@qa_bp.route('/status', methods=['GET'])
def ollama_status():
    """公开接口：检查Ollama运行状态"""
    ok, msg = check_ollama_alive()
    return jsonify({
        'code': 200,
        'data': {
            'ollama_available': ok,
            'message': msg,
        }
    })
