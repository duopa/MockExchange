# -*- encoding: UTF-8 -*-


class SqliteWrapper(object):
    def __init__(self, db_path: str, clear_db=False):
        from sqlalchemy import create_engine, MetaData
        from sqlalchemy.orm import sessionmaker
        self.engine = create_engine('sqlite:///{host}'.format(host=db_path), echo=False)
        self.metadata = MetaData(bind=self.engine)
        self.__table_definition__()
        if clear_db is True:
            self.clear_db()
        self.metadata.create_all(bind=self.engine, checkfirst=True)
        self.__table_mapping__()
        session = sessionmaker(bind=self.engine)
        self.session = session()
        # from sqlalchemy.orm import create_session
        # self.session = create_session(bind=self.engine)

    def __table_definition__(self):
        # self.events_table = define_event_table(self.metadata)
        pass

    def __table_mapping__(self):
        # from sqlalchemy.orm import mapper
        # mapper(Event, self.events_table)
        pass

    def add_all(self, obj):
        if len(obj) > 0:
            self.session.add_all(obj)
            self.session.commit()

    def add(self, obj):
        self.session.add(obj)
        self.session.commit()

    def drop_tables(self, table):
        from sqlalchemy import Table
        assert isinstance(table, Table), str(TypeError('table should be of type sqlalchemy.Table'))
        self.metadata.remove(table)

    def clear_db(self):
        self.metadata.drop_all()

    def get_all(self, obj_type: type, **filter_by):
        """get_all all {obj_type} filter by {kwargs} -> list"""
        return self.session.query(obj_type).filter_by(**filter_by).all()

    def get_one(self, obj_type: type, **filter_by):
        return self.session.query(obj_type).filter_by(**filter_by).one()
