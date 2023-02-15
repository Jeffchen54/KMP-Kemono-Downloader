import sqlite3
from sqlite3 import Connection, Cursor
from threading import Lock
import threading

class DB():
    __db_name:str
    __connection:Connection
    __cursor:Cursor
    __lock:Lock
    
    def __init__(self, db_name:str) -> None:
        """
        Creates a database or reopens a database if a database
        with the provided name already exists.
        
        Args:
            db_name (str): name of the database
        Pre: db_name must have .db or other suffixes, some exceptions such as 
                memory only database exists
        """
        self.__db_name = db_name
        self.__connection = sqlite3.connect(db_name)
        self.__cursor = self.__connection.cursor()
        self.__lock = threading.Lock()
    
    def execute(self, cmd:str|tuple) -> any:
        """
        Thread safe; Executes a command, if the command returns something,
        it will be returned.

        Args:
            cmd (str): sql command
        Returns: anything the cmd returns
        """
        self.__lock.acquire()
        
        if(isinstance(cmd, str)):
            content = self.__cursor.execute(cmd)
        
        else:
            content = self.__cursor.execute(*cmd)
        self.__lock.release()
        
        return content
    
    def executeBatch(self, cmds:list[str|tuple]) -> any:
        """
        Thread safe; Executes batch commands, if the command returns something,
        it will be returned.

        Args:
            cmd (str): sql command
        Returns: list containing anything the cmd returns
        """
        self.__lock.acquire()
        content = list[len(cmds)]
        for i, item in enumerate(cmds):
            if(isinstance(item, str)):
                content = self.__cursor.execute(item)
            else:
                content[i] = self.__cursor.execute(*item)
        self.__lock.release()
        
        return content
    
    def executeNCommit(self, cmd:str|tuple) -> any:
        """
        Thread safe; Executes a command, if the command returns something,
        it will be returned. 
        
        Commit is done after the opertion has been completed

        Args:
            cmd (str): sql command
        Returns: anything the cmd returns
        """
        self.__lock.acquire()
        
        if(isinstance(cmd, str)):
            content = self.__cursor.execute(cmd)
        
        else:
            content = self.__cursor.execute(*cmd)
        self.__connection.commit()
        self.__lock.release()
        
        return content
    
    def executeBatchNCommit(self, cmds:list[str|tuple]) -> any:
        """
        Thread safe; Executes a command, if the commands returns something,
        it will be returned. 
        
        Commit is done after the opertion has been completed

        Args:
            cmd (str): sql command
        Returns: list of anything anything the cmd returns
        """
        self.__lock.acquire()
        content = list[len(cmds)]
        for i, item in enumerate(cmds):
            if(isinstance(item, str)):
                content = self.__cursor.execute(item)
            else:
                content[i] = self.__cursor.execute(*item)
        self.__connection.commit()
        self.__lock.release()
        
        return content
    
    def commit(self) -> None:
        """
        Thread safe; Commits unsaved changes.
        """
        self.__lock.acquire()
        self.__connection.commit()
        self.__lock.release()
    
    def closeNOpen(self)->None:
        """
        Closes and reopens the database connection
        """
        self.__connection.close()
        self.__connection = sqlite3.connect(self.__db_name)
        self.__cursor = self.__connection.cursor()
    
    
    def close(self)->None:
        """
        Closes the database connection
        """
        self.__connection.close()
        