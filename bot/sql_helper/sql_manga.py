from bot.sql_helper import Base, Session, engine
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy import or_


class Manga(Base):

    __tablename__ = 'manga'
    manga_id = Column(String(255), primary_key=True, autoincrement=False)
    embyid = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    pwd = Column(String(255), nullable=True)


Manga.__table__.create(bind=engine, checkfirst=True)


def sql_add_manga(manga_info):
    """
    添加一条manga记录，如果manga_id已存在则忽略
    """
    with Session() as session:
        try:
            if not isinstance(manga_info, Manga):
                return
            condition = or_(Manga.embyid == manga_info.embyid, Manga.manga_id == manga_info.manga_id)
            manga = session.query(Manga).filter(condition).one()
            if manga:
                return
            session.add(manga_info)
            session.commit()
        except:
            pass


def sql_delete_manga(embyid=None, manga_id=None):
    """
    根据embyid或manga_id删除一条manga记录
    """
    with Session() as session:
        try:
            condition = or_(Manga.embyid == embyid, Manga.manga_id == manga_id)
            manga = session.query(Manga).filter(condition).with_for_update().first()
            if manga:
                session.delete(manga)
                session.commit()
                return True
            else:
                return None
        except:
            return False


def sql_update_manga_password(embyid, manga_id, pwd):
    """
        根据embyid或manga_id删除一条manga记录
        """
    with Session() as session:
        try:
            manga = session.query(Manga).filter(or_(Manga.embyid == embyid, Manga.manga_id == manga_id)).one()
            if pwd is None:
                return False
            manga.pwd = pwd
            session.commit()
            return True
        except:
            return False


def sql_get_manga(embyid, manga_id=None):
    """
    查询一条manga记录，可以根据embyid或manga_id来查询
    """
    with Session() as session:
        try:
            manga = session.query(Manga).filter(or_(Manga.embyid == embyid, Manga.manga_id == manga_id)).one()
            return manga
        except:
            return None