"""
企业知识库问答系统 - 数据库模型定义
使用SQLAlchemy ORM映射MySQL表结构
"""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

# 全局数据库实例
db = SQLAlchemy()


class User(db.Model):
    """用户模型 - 对应users表"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='用户ID')
    username = db.Column(db.String(50), unique=True, nullable=False, comment='用户名')
    password = db.Column(db.String(128), nullable=False, comment='MD5加密后的密码')
    role = db.Column(db.String(20), nullable=False, default='user', comment='角色: admin管理员, user普通用户')
    email = db.Column(db.String(100), nullable=True, comment='邮箱')
    avatar = db.Column(db.String(255), nullable=True, comment='头像URL')
    status = db.Column(db.SmallInteger, nullable=False, default=1, comment='状态: 1启用, 0禁用')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.now,
        onupdate=datetime.now, comment='更新时间'
    )

    def to_dict(self):
        """转换为字典，不包含密码字段"""
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'email': self.email,
            'avatar': self.avatar,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
        }


class KnowledgeCategory(db.Model):
    """知识分类模型 - 对应knowledge_categories表"""
    __tablename__ = 'knowledge_categories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='分类ID')
    name = db.Column(db.String(100), nullable=False, comment='分类名称')
    description = db.Column(db.String(500), nullable=True, comment='分类描述')
    parent_id = db.Column(db.Integer, nullable=False, default=0, comment='父分类ID')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }


class Document(db.Model):
    """知识文档模型 - 对应documents表"""
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='文档ID')
    title = db.Column(db.String(200), nullable=False, comment='文档标题')
    content = db.Column(db.Text, nullable=False, comment='文档内容')
    file_type = db.Column(db.String(20), nullable=False, default='txt', comment='文件类型')
    category_id = db.Column(db.Integer, nullable=True, comment='所属分类ID')
    chunk_count = db.Column(db.Integer, nullable=False, default=0, comment='文档分块数量')
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='上传者')
    status = db.Column(db.SmallInteger, nullable=False, default=1, comment='状态: 1正常, 0已删除')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.now,
        onupdate=datetime.now, comment='更新时间'
    )

    # 关联关系
    uploader = db.relationship('User', backref='documents', lazy='joined')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content[:200] + '...' if len(self.content) > 200 else self.content,
            'file_type': self.file_type,
            'category_id': self.category_id,
            'chunk_count': self.chunk_count,
            'uploaded_by': self.uploaded_by,
            'uploader_name': self.uploader.username if self.uploader else None,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
        }


class QAHistory(db.Model):
    """问答历史模型 - 对应qa_history表"""
    __tablename__ = 'qa_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='记录ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='提问用户')
    question = db.Column(db.Text, nullable=False, comment='用户问题')
    answer = db.Column(db.Text, nullable=False, comment='系统回答')
    sources = db.Column(db.Text, nullable=True, comment='参考来源(JSON)')
    feedback = db.Column(db.SmallInteger, nullable=True, comment='反馈: 1满意, 0不满意')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='提问时间')

    # 关联关系
    user = db.relationship('User', backref='qa_histories', lazy='joined')

    def to_dict(self):
        """转换为字典"""
        import json
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'question': self.question,
            'answer': self.answer,
            'sources': json.loads(self.sources) if self.sources else [],
            'feedback': self.feedback,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }
