from threading import Lock, Condition
class LockingCounter():
    """
    Represents a thread safe counter with multiple operations
    """
    __value:int             # Current lock's value
    __mutex:Lock            # Lock used for counter itself
    __cond_list:list        # List of conditionals
    
    def __init__(self, starting:int=0) -> None:
        """
        Initializes the counter with starting value and initializes any other
        required variables.
        
        starting: starting value of the counter
        """
        self.__value = starting
        self.__mutex = Lock()
        self.__cond_list = list()
        
    def toggle(self) -> int:
        """
        Increments counter by 1
        
        Returns: counter value immediately after toggle
        """
        self.__mutex.acquire()
        self.__value += 1
        saved = self.__value        
        self.__mutex.release()
        
        # Notify waiting threads 
        for cond in self.__cond_list:
            cond.acquire()
            cond.notify()
            cond.release()
        return saved
    
    def wait_until(self, target:int) -> None:
        """
        Block until target is <= counter

        Args:
            target (int): value to block for
        """
        # Get current value and see if target has already been met
        curr = self.get()
        
        if curr >= target:
            return
        
        # If not met, block until is met
        cond = Condition()
        self.__cond_list.append(cond)
        cond.acquire()
        cond.wait_for(predicate= lambda:self.__compare(target, self.get()))
        cond.release()
        self.__cond_list.remove(cond)
        return
    
    def __compare(self, i1:int, i2:int) -> bool:
        """
        Performs i1 <= i2 and returns the result

        Args:
            i1 (int): int 1 
            i2 (int): int 2

        Returns:
            bool: i1 <= i2 is returned
        """
        return i1 <= i2
    
    def get(self) -> int:
        """
        Returns counter value

        Returns:
            int: counter value
        """
        self.__mutex.acquire()
        saved = self.__value
        self.__mutex.release()
        return saved
    
    def set(self, target:int) -> None:
        """
        Set counter to target value
        
        target (int): value to set counter to 
        """
        self.__mutex.acquire()
        self.__value = target
        self.__mutex.release()