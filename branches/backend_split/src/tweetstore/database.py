# -*- coding: utf-8 -*-

import threading
import sqlite3
from Queue import Queue 

class ThreadSafeDatabase:
    """ Threadsafe database connection to an sqlite database

        This object is highly inspired by http://code.activestate.com/recipes/526618/
        and offers a simple wrapper around a single sqlite database connection. This
        object is threadsafe, and can be accessed from any thread.

        This wrapper uses a thread which owns a database connection and a queue to
        synchronize requests to this worker thread. This might look like a poorly
        performing solution. However, GIL usually locks thread so that SMP machines
        wouldn't benefit from multithreading anyway. So at the end of the day this
        object causes thread synchronization instead of multiple database connections.

        Note: This class can also with only a few simple modifications be used for 
        other databases than sqlite.

        >>> db = ThreadSafeDatabase()
        >>> db.execute("create table test (id integer primary key, value TEXT)")
        ()
        >>> res = db.execute("insert into test (value) values (?)", "My dummy text")
        >>> isinstance(res, (long, int))
        True
        >>> first, = db.execute("select value from test where id = ?", res)
        >>> first["value"] == "My dummy text"
        True
        >>> db.close()
    """
    def __init__(self, database = ":memory:"):
        """ Create an instance of ThreadSafeDatabase connected to a database

            database:   Database path of the database that should be connected,
                        defaults to a database stored in memory.
            """
        assert isinstance(database, basestring), "database must be a string"
        self.__database = database
        self.__requests = Queue()
        self.isRunning = True
        self.__thread = threading.Thread(target = self.__run)
        self.__thread.start()

    def __run(self):
        """Run the database on this thread"""
        connection = sqlite3.connect(self.__database)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        while True:
            sql, args, result = self.__requests.get()
            if sql == "--close--": break
            if sql == "--commit--":
                connection.commit()
                continue
            #Execute sql statement
            try:
                cursor.execute(sql, args)
            except BaseException, e:
                result.put("--exception--")
                result.put(e)
                continue
            #If there's a lastrowid, we did an INSERT statement, return the lastrowid
            if cursor.lastrowid:
                result.put("--lastrowid--")
                result.put(cursor.lastrowid)
            else:
                #Return the records if any
                for record in cursor:
                    result.put(record)
                result.put("--executed--")
        cursor.close()
        connection.close()

    def execute(self, sql, *args):
        """ Execute an SQL statement with optional arguments

            Note: This method blocks the thread till the SQL statement have been
            executed. This should not cause any serious performance issues as
            GIL prevents SMP machine from utilizing multiple cores anyway.

            If the execution throws an execption this is rethrown here.

            returns:
                empty tuple if no rows is returned.
                row generator, if rows is returned.
                lastrowid if a row was inserted.
        """
        if not self.isRunning:
            raise DatabaseClosedError, "cannot execute sql statement: " + str(sql)
        results = Queue()
        self.__requests.put((sql, args, results))
        result = results.get()
        if result == "--executed--":
            return tuple()
        if result == "--lastrowid--":
            return results.get()
        if result == "--exception--":
            raise results.get()
        return self.__generate_results(result, results)

    def __generate_results(self, result, results):
        """ Generate results

            This method yields results returning a generator, offering better performance
            and lacy evaluation.
        """
        while result != "--executed--":
            yield result
            result = results.get()

    def fetchone(self, sql, *args):
        """ Execute SQL statement with optional arguments and fetch only the first row

            This does the same as execute() except it only returns the first row or None.
            For better performance consider appending " LIMIT 1" to all select statements,
            executed with this command.

            returns:
                None of no rows is returned.
                First row, if rows is returned.
                lastrowid if a row was inserted.
        """
        if not self.isRunning:
            raise DatabaseClosedError, "cannot execute sql statement: " + str(sql)
        results = Queue()
        self.__requests.put((sql, args, results))
        result = results.get()
        if result == "--executed--":
            return None
        if result == "--lastrowid--":
            return results.get()
        if result == "--exception--":
            raise results.get()
        return result

    def fetchall(self, sql, *args):
        """ Execute an SQL statement with optional arguments and fetch all rows in a list

            This does the same as execute() except it returns the rows in a list instead of
            returning them using a generator. Generators might offer better performance because
            they lazily evaluates the result. However, for some purposes list may be preferred.
            For instance the length of a generator cannot be computed.

            returns:
                empty tuple if no rows is returned.
                tuple of rows, if rows is returned.
                lastrowid if a row was inserted.
        """
        if not self.isRunning:
            raise DatabaseClosedError, "cannot execute sql statement: " + str(sql)
        results = Queue()
        self.__requests.put((sql, args, results))
        result = results.get()
        if result == "--executed--":
            return tuple()
        if result == "--lastrowid--":
            return results.get()
        if result == "--exception--":
            raise results.get()
        return tuple(self.__generate_results(result, results))

    def commit(self):
        """Commit any changes to database"""
        if not self.isRunning:
            raise DatabaseClosedError, "cannot commit changes, this is probably already done."
        self.__requests.put(("--commit--", None, None))

    def close(self):
        """Close the database connection"""
        assert self.isRunning, "Database cannot be closed more that once."
        self.isRunning = False
        self.__requests.put(("--close--", None, None))
        self.__thread.join()

    def __del__(self):
        """Release ressources held by this instance"""
        if self.isRunning:
            self.close()

class DatabaseClosedError(Exception):
    """Exception that occurs if a ThreadSafeDatabase is invoked after being closed."""
    def __init__(self, msg = None):
        self.msg = msg

    def __str__(self):
        if msg:
            return "Database is not running, " + self.msg
        else:
            return "Database is not running."

if __name__ == "__main__":
    import doctest
    doctest.testmod()

