"""
企业知识库问答系统 - RAG检索引擎
基于LangChain + Chroma + Ollama实现检索增强生成
"""
import os
import json
import logging
import requests
from typing import List, Dict, Optional, Tuple

from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document as LangchainDocument

from config import Config

logger = logging.getLogger(__name__)


def check_ollama_alive() -> Tuple[bool, str]:
    """
    检测Ollama服务是否运行且所需模型已安装

    Returns:
        (是否可用, 状态描述)
    """
    try:
        resp = requests.get(f'{Config.OLLAMA_BASE_URL}/api/tags', timeout=5)
        if resp.status_code == 200:
            installed = [m['name'] for m in resp.json().get('models', [])]
            # 简化模型名比较：qwen3:8b 和 qwen3-embedding:4b
            inst_names = set()
            for m in installed:
                inst_names.add(m)
                if ':' in m:
                    inst_names.add(m.split(':')[0])
            missing = []
            for required in [Config.LLM_MODEL, Config.EMBEDDING_MODEL]:
                if required not in inst_names:
                    missing.append(required)
            if missing:
                return False, f'模型未安装: {", ".join(missing)}，已装: {installed if installed else "无"}'
            return True, f'Ollama就绪，模型: {", ".join(installed)}'
        return False, f'Ollama返回异常: {resp.status_code}'
    except requests.ConnectionError:
        return False, f'无法连接Ollama ({Config.OLLAMA_BASE_URL})，请确认Ollama已启动'
    except Exception as e:
        return False, f'Ollama检测异常: {e}'


class RAGEngine:
    """
    RAG检索引擎类
    负责文档向量化、存储、检索和生成回答
    如果Ollama不可用，自动降级为关键词匹配模式
    """

    def __init__(self):
        """初始化RAG引擎"""
        # 检测Ollama可用性
        self.ollama_ok, self.ollama_status = check_ollama_alive()

        if self.ollama_ok:
            try:
                self.embeddings = OllamaEmbeddings(
                    model=Config.EMBEDDING_MODEL,
                    base_url=Config.OLLAMA_BASE_URL,
                )
                self.llm = ChatOllama(
                    model=Config.LLM_MODEL,
                    base_url=Config.OLLAMA_BASE_URL,
                    temperature=0.3,
                )
            except Exception as e:
                self.ollama_ok = False
                self.ollama_status = f'模型初始化失败: {e}'
        else:
            self.embeddings = None
            self.llm = None

        # 文本分割器（不依赖Ollama）
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            separators=['\n\n', '\n', '。', '！', '？', '；', '.', '!', '?', ' ', ''],
            length_function=len,
        )

        # 初始化Chroma向量数据库
        if self.ollama_ok:
            try:
                self.vector_store = Chroma(
                    collection_name=Config.CHROMA_COLLECTION_NAME,
                    embedding_function=self.embeddings,
                    persist_directory=Config.CHROMA_PERSIST_DIR,
                )
                self.rag_chain = self._build_rag_chain()
            except Exception as e:
                logger.error(f'Chroma初始化失败: {e}')
                self.ollama_ok = False
                self.ollama_status = f'Chroma初始化失败: {e}'
                self.vector_store = None
                self.rag_chain = None
        else:
            self.vector_store = None
            self.rag_chain = None

        if self.ollama_ok:
            logger.info(f'RAG引擎就绪 - LLM: {Config.LLM_MODEL}, Embedding: {Config.EMBEDDING_MODEL}')
        else:
            logger.warning(f'RAG引擎降级为关键词匹配模式 - {self.ollama_status}')

    def _build_rag_chain(self):
        """构建RAG处理链"""
        prompt_template = """你是一个专业的企业知识库问答助手。请根据以下已知的企业内部知识来回答用户的问题。

## 已知知识:
{context}

## 对话规则:
1. 如果可以根据已知知识回答，请给出详细、准确的回答
2. 如果已知知识不足以回答问题，请明确说明"根据现有知识库，我无法回答这个问题"
3. 回答时请引用相关的文档来源
4. 保持专业、友好的语气

## 用户问题:
{question}

## 回答:"""

        prompt = ChatPromptTemplate.from_template(prompt_template)
        retriever = self.vector_store.as_retriever(
            search_kwargs={'k': Config.RETRIEVAL_TOP_K}
        )

        def format_docs(docs: List[LangchainDocument]) -> str:
            formatted = []
            for i, doc in enumerate(docs, 1):
                source = doc.metadata.get('title', '未知来源')
                formatted.append(f'[文档{i}] 来源: {source}\n{doc.page_content}\n')
            return '\n---\n'.join(formatted)

        return (
            {'context': retriever | format_docs, 'question': RunnablePassthrough()}
            | prompt | self.llm | StrOutputParser()
        )

    def add_documents(self, documents: List[Dict[str, str]], doc_id_prefix: str = '') -> int:
        """将文档添加到向量数据库，Ollama离线时跳过向量化仅记录日志"""
        self._try_restore()  # 热恢复
        if not self.ollama_ok:
            logger.warning(f'Ollama不可用({self.ollama_status})，文档已存入MySQL，未向量化')
            return 0

        all_splits = []
        for doc in documents:
            splits = self.text_splitter.split_text(doc['content'])
            for i, split in enumerate(splits):
                all_splits.append(LangchainDocument(
                    page_content=split,
                    metadata={'title': doc['title'], 'chunk_index': i, 'doc_id': doc.get('id', '')}
                ))

        if not all_splits:
            return 0

        ids = [f'{doc_id_prefix}_{doc.metadata["title"]}_chunk_{doc.metadata["chunk_index"]}' for doc in all_splits]

        try:
            self.vector_store.add_documents(all_splits, ids=ids)
            logger.info(f'已添加 {len(all_splits)} 个向量块')
            return len(all_splits)
        except Exception as e:
            logger.warning(f'向量化失败({e})，文档已存入MySQL，启用Ollama后自动生效')
            # 标记引擎需重建
            self.ollama_ok = False
            self.ollama_status = f'向量化失败: {e}'
            return 0

    def delete_documents(self, title: str) -> bool:
        """从向量数据库删除文档"""
        try:
            if self.vector_store:
                collection = self.vector_store._collection
                results = collection.get(where={'title': title})
                if results and results['ids']:
                    collection.delete(ids=results['ids'])
                    return True
            return False
        except Exception as e:
            logger.error(f'删除文档失败: {e}')
            return False

    def _try_restore(self) -> bool:
        """如果Ollama从离线变为在线，重新初始化引擎组件"""
        if self.ollama_ok:
            return True  # 已经在线
        ok, msg = check_ollama_alive()
        if not ok:
            self.ollama_status = msg
            return False
        # Ollama已就绪，重新初始化
        logger.info(f'检测到Ollama已就绪，正在初始化RAG引擎... ({msg})')
        try:
            self.embeddings = OllamaEmbeddings(model=Config.EMBEDDING_MODEL, base_url=Config.OLLAMA_BASE_URL)
            self.llm = ChatOllama(model=Config.LLM_MODEL, base_url=Config.OLLAMA_BASE_URL, temperature=0.3)
            self.vector_store = Chroma(
                collection_name=Config.CHROMA_COLLECTION_NAME,
                embedding_function=self.embeddings,
                persist_directory=Config.CHROMA_PERSIST_DIR,
            )
            self.rag_chain = self._build_rag_chain()
            self.ollama_ok = True
            self.ollama_status = msg
            logger.info('RAG引擎初始化成功')
            return True
        except Exception as e:
            self.ollama_status = f'初始化失败: {e}'
            logger.warning(f'RAG引擎初始化失败: {e}')
            return False

    def search(self, query: str, top_k: Optional[int] = None) -> Tuple[str, List[Dict], str]:
        """
        搜索并生成回答
        Returns: (答案, 来源列表, 模式说明)
        """
        # 每次查询前尝试恢复 Ollama 连接（支持热恢复）
        self._try_restore()

        if top_k is None:
            top_k = Config.RETRIEVAL_TOP_K

        # 模式1: Ollama不可用 → 关键词匹配
        if not self.ollama_ok:
            return self._keyword_fallback(query)

        # 模式2: 向量库为空 → 提示用户
        if self.is_empty():
            return (
                '知识库中还没有文档数据。请先在管理后台上传知识文档，系统会自动进行向量化处理。\n\n'
                '管理员操作步骤：\n1. 进入"知识库管理"\n2. 点击"上传文档"\n3. 填写标题和内容后提交\n\n'
                f'⚠️ 当前Ollama状态: {self.ollama_status}',
                [],
                '知识库为空'
            )

        # 模式3: 正常RAG检索
        try:
            docs_with_scores = self.vector_store.similarity_search_with_score(query, k=top_k)
        except Exception as e:
            logger.error(f'向量检索失败: {e}')
            return self._keyword_fallback(query)

        sources = []
        for doc, score in docs_with_scores:
            sources.append({
                'title': doc.metadata.get('title', '未知来源'),
                'score': round(float(score), 4),
                'content_snippet': doc.page_content[:150],
            })

        try:
            answer = self.rag_chain.invoke(query)
        except Exception as e:
            logger.error(f'LLM生成失败: {e}')
            # 降级：直接返回检索到的文档片段
            snippets = '\n\n---\n\n'.join([
                f'【{s["title"]}】(相关度: {s["score"]:.0%})\n{s["content_snippet"]}'
                for s in sources
            ])
            answer = (
                f'⚠️ AI生成回答失败（{self.ollama_status}），以下是从知识库中直接检索到的相关内容：\n\n'
                f'{snippets}\n\n'
                f'💡 请确认Ollama已启动且模型已安装：\n'
                f'   ollama pull {Config.LLM_MODEL}\n'
                f'   ollama pull {Config.EMBEDDING_MODEL}'
            )

        return answer, sources, 'RAG模式'

    def _keyword_fallback(self, query: str) -> Tuple[str, List[Dict], str]:
        """Ollama不可用时的关键词匹配降级方案"""
        from models import db, Document

        docs = Document.query.filter_by(status=1).all()
        if not docs:
            return (
                '知识库中暂无文档。请先在管理后台上传知识文档。\n\n'
                f'⚠️ 当前Ollama状态: {self.ollama_status}\n\n'
                '💡 启动Ollama并安装模型后可启用AI智能问答：\n'
                '   1. 下载安装Ollama: https://ollama.com\n'
                '   2. ollama pull qwen3:4b\n'
                '   3. ollama pull qwen3-embedding:4b\n'
                '   4. 重启本服务',
                [],
                '离线模式-无文档'
            )

        # 关键词提取：空格分词 + 中文字符二元组（bigram）
        import re
        query_lower = query.lower()
        # 提取中文连续片段
        chinese_chars = re.findall(r'[一-鿿]+', query_lower)
        keywords = set(query_lower.split())  # 空格分词
        for seg in chinese_chars:
            # 二元组：如 "考勤制度" → {"考勤", "勤制", "制度"}
            for i in range(len(seg) - 1):
                keywords.add(seg[i:i + 2])
            # 也加入单字
            keywords.update(seg)

        scored = []
        for doc in docs:
            content_lower = doc.content.lower()
            title_lower = doc.title.lower()
            # 标题匹配权重更高
            score = sum(3 for kw in keywords if kw in title_lower)
            score += sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)

        if not scored:
            return (
                f'未找到与「{query}」相关的知识文档。请尝试换个问法，或联系管理员补充相关知识。\n\n'
                f'⚠️ Ollama未运行: {self.ollama_status}\n'
                f'📚 当前知识库共有 {len(docs)} 篇文档',
                [],
                '离线模式-无匹配'
            )

        sources = []
        snippets = []
        for score, doc in scored[:3]:
            sources.append({'title': doc.title, 'score': score / max(1, len(keywords)), 'content_snippet': doc.content[:150]})
            snippets.append(f'【{doc.title}】\n{doc.content[:500]}')

        answer = (
            f'🔍 离线模式 - 关键词匹配结果：\n\n'
            f'{chr(10).join(snippets)}\n\n'
            f'---\n'
            f'⚠️ 当前为离线关键词匹配模式，回答不够智能。\n'
            f'{self.ollama_status}\n\n'
            f'💡 启用AI智能问答的步骤：\n'
            f'   1. 安装Ollama: https://ollama.com\n'
            f'   2. 打开终端执行:\n'
            f'      ollama pull {Config.LLM_MODEL}\n'
            f'      ollama pull {Config.EMBEDDING_MODEL}\n'
            f'   3. 重启本服务'
        )
        return answer, sources, '离线模式-关键词匹配'

    def is_empty(self) -> bool:
        """检查向量数据库是否为空"""
        try:
            if self.vector_store:
                return self.vector_store._collection.count() == 0
            return True
        except Exception:
            return True

    def get_collection_stats(self) -> Dict:
        """获取向量数据库统计信息"""
        try:
            if self.vector_store:
                return {
                    'total_chunks': self.vector_store._collection.count(),
                    'collection_name': Config.CHROMA_COLLECTION_NAME,
                    'ollama_status': self.ollama_status,
                }
        except Exception:
            pass
        return {
            'total_chunks': 0,
            'collection_name': Config.CHROMA_COLLECTION_NAME,
            'ollama_status': self.ollama_status,
        }


# 全局单例
_rag_engine_instance = None


def get_rag_engine() -> RAGEngine:
    """获取RAG引擎单例"""
    global _rag_engine_instance
    if _rag_engine_instance is None:
        _rag_engine_instance = RAGEngine()
    return _rag_engine_instance
