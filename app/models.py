"""数据模型：法规 / 条款 / 段落 / 术语 / 引用关系 / AI 解读缓存 / 背诵记录。"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .database import Base


class Law(Base):
    __tablename__ = "laws"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    doc_number: Mapped[str] = mapped_column(String(100), default="")      # 文号
    authority: Mapped[str] = mapped_column(String(100), default="")       # 发布机关
    level: Mapped[str] = mapped_column(String(50), default="")            # 效力层级：法律/行政法规/部门规章/规范性文件
    effective_date: Mapped[str] = mapped_column(String(20), default="")   # 施行日期
    source_path: Mapped[str] = mapped_column(String(500))                 # 导入源文件
    source_format: Mapped[str] = mapped_column(String(10))                # html / md
    content_hash: Mapped[str] = mapped_column(String(64), unique=True)    # 正文哈希，防重复导入
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    articles: Mapped[list["Article"]] = relationship(back_populates="law", cascade="all, delete-orphan", order_by="Article.order_no")
    terms: Mapped[list["Term"]] = relationship(back_populates="law", cascade="all, delete-orphan")


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    law_id: Mapped[int] = mapped_column(ForeignKey("laws.id"))
    order_no: Mapped[int] = mapped_column(Integer)                        # 条号序号 1..N
    label: Mapped[str] = mapped_column(String(20))                        # 第一条/第二条…

    law: Mapped[Law] = relationship(back_populates="articles")
    paragraphs: Mapped[list["Paragraph"]] = relationship(back_populates="article", cascade="all, delete-orphan", order_by="Paragraph.order_no")


class Paragraph(Base):
    __tablename__ = "paragraphs"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"))
    order_no: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)                               # 原文段落，一字不差
    tokens: Mapped[list] = mapped_column(JSON, default=list)              # 分词缓存 [{t, term_id?}]

    article: Mapped[Article] = relationship(back_populates="paragraphs")


class Term(Base):
    __tablename__ = "terms"

    id: Mapped[int] = mapped_column(primary_key=True)
    law_id: Mapped[int] = mapped_column(ForeignKey("laws.id"))
    name: Mapped[str] = mapped_column(String(100), index=True)            # 术语/简称/缩写
    term_type: Mapped[str] = mapped_column(String(20))                    # definition/short_name/abbreviation
    full_name: Mapped[str] = mapped_column(String(200), default="")       # 简称/缩写对应全称
    definition: Mapped[str] = mapped_column(Text, default="")             # 定义文本
    article_id: Mapped[int | None] = mapped_column(ForeignKey("articles.id"))  # 来源条款

    law: Mapped[Law] = relationship(back_populates="terms")


class Relation(Base):
    """法规间引用关系：from_law 的某条款 引用/依据 to_law_name（未入库时 to_law_id 为空）。"""

    __tablename__ = "relations"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_law_id: Mapped[int] = mapped_column(ForeignKey("laws.id"))
    to_law_id: Mapped[int | None] = mapped_column(ForeignKey("laws.id"))
    to_law_name: Mapped[str] = mapped_column(String(200))
    relation_type: Mapped[str] = mapped_column(String(20), default="引用")  # 引用/依据
    article_id: Mapped[int | None] = mapped_column(ForeignKey("articles.id"))


class Reading(Base):
    """AI 解读缓存：同一条款同一种类取最新一条。"""

    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20))                         # interpret / scenario
    model: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class PracticeLog(Base):
    __tablename__ = "practice_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    paragraph_id: Mapped[int] = mapped_column(ForeignKey("paragraphs.id"), index=True)
    correct: Mapped[bool] = mapped_column(Boolean)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
