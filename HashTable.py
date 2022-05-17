from typing import List
from typing import TypeVar, Generic

T = TypeVar('T')
V = TypeVar('V')
MINIMUM_SIZE = 2
class Error(Exception):
    """Base class for other exceptions"""
    pass


class MismatchTypeException(Error):
    """Raised when a comparison is made on 2 different types"""
    pass


class KVPair (Generic[V,T]):
    """
    Generic KVPair structure where:
        Key is generic V
        Value is generic T
        Tombstone is bool & optional
    Upon initiailization, data becomes read-only
    """
    __key: V
    __value: T
    __tombstone: bool

    def __init__(self, key: V, value: T) -> None:
        """
        Initializes KVPair. Tombstone is disabled by default.

        Param
            key: key (use to sort)
            value: value (data)

        """
        self.__value = value
        self.__key = key
        self.__tombstone = False

    def getKey(self) -> V:
        """
        Returns key
        Return: key
        """
        return self.__key

    def getValue(self) -> T:
        """
        Returns value
        Return: value
        """
        return self.__value
    
    def setValue(self, newValue:T)->None:
        """
        Set value
        Param: value
        """
        self.__value = newValue

    def compareTo(self, other) -> int:
        """
        Compares self and other key value. Ignores generic typing

        Raise: MismatchTypeException if other is not a KVPair\n
        Return:
            self.getKey() > other.getKey() -> 1\n
            self.getKey() == other.getKey() -> 0\n
            self.getKey() < other.getKey() -> -1\n

        """
        if other == None or not isinstance(other, KVPair):
            raise MismatchTypeException("other is not of type KVPair(V,T)")

        if self.__key > other.getKey():
            return 1
        if self.__key == other.getKey():
            return 0
        return -1

    def __str__(self) -> str:
        """
        toString function which returns KVPair in json style formatting
        {key:<keyval>, value:<val>, Tomb:<val>}

        value relies on T's __str__ function

        Return: KVPair in json style format
        """
        return "{key:" + str(self.__key) + ", value:" + str(self.__value) + ", Tomb:" + ("T" if self.__tombstone else "F") + "}"

    def setTombstone(self) -> None:
        """
        Turns on tombstone
        """
        self.__tombstone = True

    def disableTombstone(self) -> None:
        """
        Turns off tombstone
        """
        self.__tombstone = False

    def isTombstone(self) -> bool:
        """
        Returns tombstone status

        Return true if set, false if disabled
        """
        return self.__tombstone


class HashTable:
    """
    Closed, extensible hash table database storing KVPairs of any type
    Was built using code I wrote in Java for CS3114 with some slight functionality
    adjustments

    @author Jeff Chen
    @created 5/8/2022
    @Last modified 5/8/2022
    """
    __size: int
    __records: List[KVPair]
    __occupied: int

    def __init__(self, size):
        """
        Construct a hash table with initial size. 

        Param:
            initialSize: Initial hash table size
        """
        
        
        self.__size = max(size, MINIMUM_SIZE)
        self.__records = [None] * self.__size
        self.__occupied = 0

    # Core Functions #################################################

    def hashtable_add(self, pair: KVPair) -> None:
        """
        Adds a KVPair to the  hash table and expands if needed
        If is a duplicate entry exists, do nothing

        Param:
            KVPair: data to add to the hash table
        """
        # Check if a record exists in the table
        if(self.hashtable_exist(pair) != -1):
            return

        # TableSz
        if(self.__isHalfFull()):
            self.__doubleTable()

        # Find insert position
        home = self.hash(str(pair.getKey()), self.__size)
        tombstone = -1
        curr = home

        step = 1
        while self.__records[curr] != None:

            if self.__records[curr].isTombstone() and tombstone == -1:
                tombstone = curr

            curr = self.__quadraticProbe(home, step, self.__size)
            step += 1
        
        # Add to hash table
        if tombstone != -1:
            self.__records[tombstone] = pair
        else:
            self.__records[curr] = pair
        
        self.__occupied += 1

    def hashtable_lookup_value(self, searchKey)->any:
        """
        Look up a KVPair and returns its value
        
        Param:
            searchKey: key to search for
        Return: value of matching KVPair, None if not found
        """
        # Get index from hash table
        index = self.hashtable_exist_by_key(searchKey)

        if(index == -1):
            return None
        return self.__records[index].getValue()

    def hashtable_edit_value(self, searchKey, newValue)->bool:
        """
        Searches for a key in hash table, if found, edits value to 
        newValue

        Param
            searchKey: key of KVPair to look for
            newValue: new value to set KVPair to
        Pre: searchKey and newValue match generic type of KVPair
        Return: True if was successful, False if not
        """
        # Get index from hash table
        index = self.hashtable_exist_by_key(searchKey)

        if(index < 0):
            return False

        # Edit value
        self.__records[index].setValue(newValue)

        return True

    def hashtable_delete(self, token:KVPair)->bool:
        """
        Removes an item from the hash table
        Param
            token: record to remove from table
        Return true if removed, false if not
        """
        # Get position
        pos = self.hashtable_exist(token)
        
        if pos == -1:
            return False
        
        # Remove from table
        self.__records[pos].setTombstone()
        self.__occupied -= 1
        return True

    def hashtable_exist_by_key(self, searchKey) -> int:
        """
        Check if a KVPair exists within a hash table. 
        If a lengthy sequence of probes (>=10) is detected, table will
        be resized 

        Params:
            searchKey: key of KVPair to search for 
        Return: position if found, -1 if not
        """
        home = self.hash(str(searchKey), self.__size)
        curr = home

        step = 1
        while self.__records[curr] != None:
            if not self.__records[curr].isTombstone() and self.__records[curr].getKey() == searchKey:
                return curr
            if step >= 10:
                self.__doubleTable()
                step = 1
                curr = self.hash(str(searchKey), self.__size)
            else:
                curr = self.__quadraticProbe(home, step, self.__size)
                step += 1
        return -1

    def hashtable_exist(self, token: KVPair) -> int:
        """
        Check if a KVPair exists within a hash table. 
        If a lengthy sequence of probes (>=10) is detected, table will
        be resized 

        Params:
            tokens: KVPair to search
        Return: position if found, -1 if not
        """
        home = self.hash(str(token.getKey()), self.__size)
        curr = home

        step = 1
        while self.__records[curr] != None:
            if not self.__records[curr].isTombstone() and self.__records[curr].compareTo(token) == 0:
                return curr
            if step >= 10:
                self.__doubleTable()
                step = 1
                curr = self.hash(str(token.getKey()), self.__size)
            else:
                curr = self.__quadraticProbe(home, step, self.__size)
                step += 1
        return -1

    # Getters ########################################################
    def hashtable_getSize(self) -> int:
        """
        Get size of hash table

        Return: size of hash table
        """
        return self.__size

    def hashtable_getOccupied(self) -> int:
        """
        Get number of occupied slots

        Return: number of occupied slots
        """
        return self.__occupied
    
    def hashtable_print(self) -> None:
        """
        Prints table in the following format
        Index\tData
        1\t\t<data1>
        2\t\t<data2>
        ...
        None entry data will be shown as <None>
        """
        print("Index\tData")
        for i in range(0, self.__size):
            print(str(i + 1) + "\t\t" + ("<None>" if self.__records[i] == None else str(self.__records[i])))

    # Utility #######################################################

    def __transfer(self, dest: List[KVPair], src: KVPair) -> None:
        """
        Transfers an existing record to dest
        Param
            dest: table to transfer records to
            src: record to transfer
        Pre: dest no tombstones and src not a tombstone. 
            dest less than half full
        """
        home = self.hash(str(src.getKey()), len(dest))
        curr = home

        step = 1
        while dest[curr] != None:
            curr = self.__quadraticProbe(home, step, len(dest))
            step += 1

        dest[curr] = src

    def __rehash(self, dest: List[KVPair]) -> None:
        """
        Rehashes and transfers over all non-tombstone entries to dest

        Param
            dest: table to transfer records to
        """
        remain = self.__occupied

        i = 0
        while remain > 0:
            if self.__records[i] != None and not self.__records[i].isTombstone():
                self.__transfer(dest, self.__records[i])
                remain -= 1
            i += 1

    def __doubleTable(self) -> None:
        """
        Doubles and rehashes hash table
        """
        newRecords: List[KVPair] = [None] * self.__size * 2
        self.__rehash(newRecords)

        self.__records = newRecords
        self.__size = len(newRecords)

    def __isHalfFull(self) -> bool:
        """
        Checks if the table is half fulll

        Return: True if half full, false if not
        """
        return (self.__size - self.__occupied) <= self.__occupied

    def __quadraticProbe(self, home: int, step: int, tableSz: int) -> int:
        """
        Performs quadratic probe on home at step
        Param:
            home: home slot
            step: nth step in quadratic step
            tableSz: size of hash table
        Return: record slot at quadratic probe step
        """
        return (home + step * step) % tableSz

    def hash(self, s: str, m: int) -> int:
        """
        Hashing algorithm using string folding. Adopted from
        OpenDSA and translated to python 

        Params
            s: string to hash
            m: size of table 
        Return: home slot of s
        """
        intLength: int = int(len(s) / 4)
        sum: int = 0

        for j in range(0, intLength):
            c = list(s[j * 4: (j * 4) + 4])
            mult = 1
            for k in range(0, len(c)):
                sum += ord(c[k]) * mult
                mult *= 256
        index = intLength * 4
        c = list(s[index:])
        mult = 1

        for k in range(0, len(c)):
            sum += ord(c[k]) * mult
            mult *= 256

        return abs(sum % m)
