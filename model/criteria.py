from model.database import Database as Database
from model.column import Column as Column
from model.type import Type as Type


class Criteria(object):
    def __init__(self, klass):
        self._klass = klass
        self._lst = []
        self._i = 0

    def initialize(self):
        self._lst = []
        self._i = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._i == len(self._lst):
            raise StopIteration()
        value = self._lst[self._i]
        self._i += 1
        return value

    def create(self):
        self.initialize()
        connector = None
        try:
            connector = Database.connector()
            cursor = connector.cursor()
            try:
                sql = "DROP TABLE IF EXISTS `" + Criteria.table_name(self) + "`;\n"
                cursor.execute(sql)

                sql = "create table `" + Criteria.table_name(self) + "` (\n"
                sql += "    `id` int(11) unsigned NOT NULL AUTO_INCREMENT,\n"
                for k, v in self._klass.__dict__.items():
                    if v.__class__ == Column:
                        if v.type == Type.int:
                            sql += "    `" + k + "` int(11) DEFAULT NULL,\n"
                        elif v.type == Type.text:
                            sql += "    `" + k + "` text,\n"
                        elif v.type == Type.varchar:
                            sql += "    `" + k + "` varchar(" + str(v.length) + ") DEFAULT NULL,\n"
                        elif v.type == Type.timestamp:
                            sql += "    `" + k + "` timestamp NULL DEFAULT NULL,\n"
                        else:
                            print("error: invalid field type `" + v.type + "`")
                sql += "    PRIMARY KEY (`id`)\n"
                sql += ") ENGINE=InnoDB DEFAULT CHARSET=utf8;\n"
                cursor.execute(sql)

                sql = "LOCK TABLES `" + Criteria.table_name(self) + "` WRITE;"
                cursor.execute(sql)
            finally:
                cursor.close()
        finally:
            connector.commit()
            connector.close()

    def query(self, where, order):
        self.initialize()
        connector = None
        ret = None
        try:
            connector = Database.connector()
            cursor = connector.cursor()
            try:
                sql = "select * from " + Criteria.table_name(self)
                if len(where) > 0:
                    sql += " where"
                    for i, v in enumerate(where):
                        if i > 0:
                            sql += " and"
                        sql += " " + v

                if len(order) > 0:
                    sql += " order by"
                    for v in order:
                        sql += " " + v

                sql += ";"
                cursor.execute(sql)
                ret = [dict(line) for line in [zip([column[0] for column in
                                                    cursor.description], row) for row in cursor.fetchall()]]
            finally:
                cursor.close()
                pass
        finally:
            connector.close()

        self._lst = self.recursive(ret, self._lst)
        return self

    def recursive(self, ret=[], lst=[]):
        if len(ret) == 0:
            return lst
        else:
            r = ret.pop()
            c = self._klass()
            for k, v in c.__class__.__dict__.items():
                if v.__class__ is not Column:
                    continue
                setattr(c, k, r[k])
            lst.append(c)
            return self.recursive(ret, lst)

    def where(self):
        return self

    def all(self):
        return self

    def first(self):
        return self._lst[0] if len(self._lst) > 0 else None

    def size(self):
        return len(self._lst)

    def is_exist_table(self):
        flag = True
        connector = None
        try:
            connector = Database.connector()
            cursor = connector.cursor()
            try:
                sql = "SHOW TABLES;"
                cursor.execute(sql)
                ret = [d[0] for d in cursor.fetchall()]
                if Criteria.table_name(self) not in ret:
                    flag = False
            except Exception as e:
                print('type:' + str(type(e)))
                print('args:' + str(e.args))
            finally:
                cursor.close()
        finally:
            connector.close()
            return flag

    def difference(self, attributes):
        diff = {}
        connector = None
        try:
            connector = Database.connector()
            cursor = connector.cursor()
            try:
                sql = "show columns from " + Criteria.table_name(self)
                cursor.execute(sql)
                ret = {d[0] for d in cursor.fetchall()}
                for a in attributes:
                    if a not in ret:
                        diff[a] = "new"
                for r in ret:
                    if r not in attributes:
                        diff[r] = "deleted"
            except Exception as e:
                print('type:' + str(type(e)))
                print('args:' + str(e.args))
            finally:
                cursor.close()
        finally:
            connector.close()
            if diff == {}:
                return None
            else:
                return diff

    def add_column(self, name, column):
        connector = None
        try:
            connector = Database.connector()
            cursor = connector.cursor()
            try:
                sql = "alter table " + Criteria.table_name(self)
                if column.type == Type.int:
                    return
                elif column.type == Type.text:
                    sql += " add " + name + " " + column.type + "(" + column.length + ")"
                else:
                    sql += " add " + name + " " + column.type
                cursor.execute(sql)
            finally:
                cursor.close()
        finally:
            connector.commit()
            connector.close()

    def delete_column(self, name):
        connector = None
        try:
            connector = Database.connector()
            cursor = connector.cursor()
            try:
                sql = "alter table " + Criteria.table_name(self) + " drop column " + name
                cursor.execute(sql)
            finally:
                cursor.close()
        finally:
            connector.commit()
            connector.close()

    @staticmethod
    def table_name(this):
        return this._klass.__name__.lower()
