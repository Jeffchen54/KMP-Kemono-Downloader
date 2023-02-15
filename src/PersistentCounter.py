class PersistentCounter():
    """
    A counter but an object instead of an int
    """
    __value:int             # Current lock's value
    
    def __init__(self, starting:int=0) -> None:
        """
        Initializes the counter with starting value
        
        starting: starting value of the counter
        """
        self.__value = starting
    
    def toggle(self) -> int:
        """
        Increments counter by 1
        
        Returns: counter value immediately after toggle
        """
      
        self.__value += 1
        return self.__value
    
    def get(self) -> int:
        """
        Returns the counter's value

        Returns:
            int: counter value
        """
        return self.__value

    def set(self, target:int) -> None:
        """
        Sets the counter's value

        Args:
            target (int): counter's new value
        """
        self.__value = target