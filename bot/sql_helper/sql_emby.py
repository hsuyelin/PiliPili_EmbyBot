"""
基本的sql操作
"""
from bot.sql_helper import Base, Session, engine
from sqlalchemy import Column, BigInteger, String, DateTime, Integer, case, text
from sqlalchemy import func
from sqlalchemy import or_


class Emby(Base):
    """
    emby表，tg主键，默认值lv，us，iv
    """
    __tablename__ = 'emby'
    tg = Column(BigInteger, primary_key=True, autoincrement=False)
    embyid = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    pwd = Column(String(255), nullable=True)
    pwd2 = Column(String(255), nullable=True)
    lv = Column(String(1), default='d')
    cr = Column(DateTime, nullable=True)
    ex = Column(DateTime, nullable=True)
    us = Column(Integer, default=0)
    iv = Column(Integer, default=0)
    ch = Column(DateTime, nullable=True)


Emby.__table__.create(bind=engine, checkfirst=True)


def sql_add_emby(tg: int):
    """
    添加一条emby记录，如果tg已存在则忽略
    """
    with Session() as session:
        try:
            emby = Emby(tg=tg)
            session.add(emby)
            session.commit()
        except:
            pass


def sql_delete_emby(tg=None, embyid=None, name=None):
    """
    根据tg, embyid或name删除一条emby记录
    """
    with Session() as session:
        try:
            # 构造一个or_条件，只要有一个参数不为None就可以匹配
            condition = or_(Emby.tg == tg, Emby.embyid == embyid, Emby.name == name)
            # 用filter来过滤，注意要加括号
            emby = session.query(Emby).filter(condition).with_for_update().first()
            if emby:
                session.delete(emby)
                session.commit()
                return True
            else:
                return None
        except:
            return False


def sql_update_embys(some_list: list, method=None):
    """ 根据list中的tg值批量更新一些值 ，此方法不可更新主键"""
    with Session() as session:
        if method == 'iv':
            try:
                mappings = [{"tg": c[0], "iv": c[1]} for c in some_list]
                session.bulk_update_mappings(Emby, mappings)
                session.commit()
                return True
            except:
                session.rollback()
                return False
        if method == 'ex':
            try:
                mappings = [{"tg": c[0], "ex": c[1]} for c in some_list]
                session.bulk_update_mappings(Emby, mappings)
                session.commit()
                return True
            except:
                session.rollback()
                return False
        if method == 'bind':
            try:
                mappings = [{"name": c[0], "embyid": c[1]} for c in some_list]
                session.bulk_update_mappings(Emby, mappings)
                session.commit()
                return True
            except:
                session.rollback()
                return False


def sql_get_emby(tg):
    """
    查询一条emby记录，可以根据tg, embyid或者name来查询
    """
    with Session() as session:
        try:
            # 使用or_方法来表示或者的逻辑，如果有tg就用tg，如果有embyid就用embyid，如果有name就用name，如果都没有就返回None
            emby = session.query(Emby).filter(or_(Emby.tg == tg, Emby.name == tg, Emby.embyid == tg)).first()
            return emby
        except:
            return None


# def sql_get_emby_by_embyid(embyid):
#     """
#     Retrieve an Emby object from the database based on the provided Emby ID.
#
#     Parameters:
#         embyid : The Emby ID used to identify the Emby object.
#
#     Returns:
#         tuple: A tuple containing a boolean value indicating whether the retrieval was successful
#                and the retrieved Emby object. If the retrieval was unsuccessful, the boolean value
#                will be False and the Emby object will be None.
#     """
#     with Session() as session:
#         try:
#             emby = session.query(Emby).filter((Emby.embyid == embyid)).first()
#             return True, emby
#         except Exception as e:
#             return False, None


def get_all_emby(condition):
    """
    查询所有emby记录
    """
    with Session() as session:
        try:
            embies = session.query(Emby).filter(condition).all()
            return embies
        except:
            return None


def sql_update_emby(condition, **kwargs):
    """
    更新一条emby记录，根据condition来匹配，然后更新其他的字段
    """
    with Session() as session:
        try:
            # 用filter来过滤，注意要加括号
            emby = session.query(Emby).filter(condition).first()
            if emby is None:
                return False
            # 然后用setattr方法来更新其他的字段，如果有就更新，如果没有就保持原样
            for k, v in kwargs.items():
                setattr(emby, k, v)
            session.commit()
            return True
        except:
            return False

def sql_change_emby_tg(embyid, new_tg):
    """
    根据 embyid 将记录的主键值更新为新的 tg 值

    :param embyid: 要更新的记录的 embyid
    :param new_tg: 新的 tg 值
    :return: 更新是否成功以及可能的错误消息
    """
    with Session() as session:
        try:
            old_record = session.query(Emby).filter_by(embyid=embyid).first()
            if old_record is None:
                return False, f"未找到embyid为{embyid}的记录"

            new_record = session.query(Emby).filter_by(tg=new_tg).first()
            if new_record:
                for column in Emby.__table__.columns:
                    if column.name != 'tg':
                        setattr(new_record, column.name, getattr(old_record, column.name))
            else:
                new_record = Emby(tg=new_tg, embyid=old_record.embyid, name=old_record.name, pwd=old_record.pwd,
                                  pwd2=old_record.pwd2, lv=old_record.lv, cr=old_record.cr, ex=old_record.ex,
                                  us=old_record.us, iv=old_record.iv, ch=old_record.ch)
                session.add(new_record)

            session.delete(old_record)
            session.commit()

            return True, "TGID更新成功"
        except Exception as e:
            session.rollback()
            return False, f"TGID更新失败: {str(e)}"


#
# def sql_change_emby(name, new_tg):
#     with Session() as session:
#         try:
#             emby = session.query(Emby).filter_by(name=name).first()
#             if emby is None:
#                 return False
#             emby.tg = new_tg
#             session.commit()
#             return True
#         except Exception as e:
#             print(e)
#             return False


def sql_count_emby():
    """
    # 检索有tg和embyid的emby记录的数量，以及Emby.lv =='a'条件下的数量
    # count = sql_count_emby()
    :return: int, int, int
    """
    with Session() as session:
        try:
            # 使用func.count来计算数量，使用filter来过滤条件
            count = session.query(
                func.count(Emby.tg).label("tg_count"),
                func.count(Emby.embyid).label("embyid_count"),
                func.count(case((Emby.lv == "a", 1))).label("lv_a_count")
            ).first()
        except:
            return None, None, None
        else:
            return count.tg_count, count.embyid_count, count.lv_a_count


def sql_get_iv_ranks(num_records, excluded_tgs):
    with Session() as session:
        try:
            if not isinstance(num_records, int):
                num_records = 10

            if not isinstance(excluded_tgs, list):
                excluded_tgs = []

            if excluded_tgs:
                excluded_tgs_str = ', '.join(map(str, excluded_tgs))
                sql_query = text(f"""  
                    SELECT * FROM emby  
                    WHERE tg NOT IN ({excluded_tgs_str})  
                    ORDER BY iv DESC  
                    LIMIT :num_records  
                """)
            else:
                sql_query = text("""  
                    SELECT * FROM emby  
                    ORDER BY iv DESC  
                    LIMIT :num_records  
                """)

            return session.execute(sql_query, {'num_records': num_records})
        except Exception as e:
            return []
