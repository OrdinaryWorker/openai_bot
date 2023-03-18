import psycopg2
import sys

# https://github.com/alexn1st0r/postgresql-python-class
class PostgresqlDBManagementSystem(object):
    """Питоновский класс для баловства с postgresql"""

    __instance = None
    __host = None
    __user = None
    __password = None
    __database = None
    __cursor = None
    __connection = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance or not cls.__database:
            cls.__instance = super(PostgresqlDBManagementSystem, cls).__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self, host='localhost', user='nester', password='', database=''):
        self.__host = host
        self.__user = user
        self.__password = password
        self.__database = database

    def __open(self):

        try:
            self.__connection = psycopg2.connect("dbname='{0}' user='{1}'".
                                                 format(self.__database, self.__user))
            self.__cursor = self.__connection.cursor()

        except psycopg2.DatabaseError as error:
            if self.__connection:
                    self.__connection.rollback()
            print('Error %s' % error)
            sys.exit(1)

    def __close(self):
        self.__connection.close()

    def create_table(self, table_name, table_structure):

        query = "CREATE TABLE " + table_name + table_structure
        self.__open()
        self.__cursor.execute("DROP TABLE IF EXISTS {0}".format(table_name))
        self.__cursor.execute(query)
        self.__connection.commit()
        self.__close()

    def insert(self, table, *args, **kwargs):

        values = None
        query = 'INSERT INTO {0} '.format(table)
        if kwargs:
            keys = kwargs.keys()
            values = tuple(kwargs.values())
            query += "(" + ",".join(["%s"] * len(keys)) % tuple(keys) + \
                     ") VALUES (" + ",".join(["%s"]*len(values)) + ")"
        elif args:
            values = args
            query += " VALUES(" + ",".join(["%s"]*len(values)) + ")"

        self.__open()
        self.__cursor.execute(query, values)
        self.__connection.commit()
        self.__close()

    def select(self, table, where=None, *args, **kwargs):

        query = 'SELECT '
        keys = args
        values = tuple(kwargs.values())
        l = len(keys) - 1

        for i, key in enumerate(keys):
            query += key
            if i < l:
                query += ","

        query += 'FROM %s' % table

        if where:
            query += " WHERE {0}".format(where)

        self.__open()
        self.__cursor.execute(query, values)
        rows = self.__cursor.fetchall()
        self.__connection.commit()
        self.__close()

        return rows

    def select_all(self, table):
        self.__open()
        self.__cursor.execute("SELECT * FROM {0}".format(table))
        rows = self.__cursor.fetchall()
        self.__connection.commit()
        self.__close()

        return rows

    def delete(self, table, where=None, *args):
        query = "DELETE FROM {0}".format(table)
        if where:
            query += ' WHERE %s' % where

        values = tuple(args)

        self.__open()
        self.__cursor.execute(query, values)
        self.__connection.commit()
        self.__close()

    def update(self, table, where=None, *args, **kwargs):

        query = "UPDATE %s SET " % table
        keys = kwargs.keys()
        values = tuple(kwargs.values()) + tuple(args)
        l = len(keys) - 1
        for i, key in enumerate(keys):
            query += key+" = %s"
            if i < l:
                query += ","

        query += " WHERE %s" % where

        self.__open()
        self.__cursor.execute(query, values)
        self.__connection.commit()
        self.__close()