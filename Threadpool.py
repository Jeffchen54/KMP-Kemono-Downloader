import logging
import threading
from threading import Lock
"""
Simple task stealing threadpool. Handles fully generic tasks of any kind

Written from scratch, does not use any logic from other projects such as CS3214 Fork Join Threadpool
https://courses.cs.vt.edu/cs3214/videos/cs3214_fall20_threadpool_info_2_slides.pdf


Author: Jeff Chen
Last modified: 6/14/2022
"""
thread_id = threading.local()   # TLV for thread name


class MutexCounter():
    """
    Counter with a mutex
    """
    __mutex: Lock
    __counter: int

    def __init__(self, value: int) -> None:
        """
        Inits counter with starting value
        """
        self.__counter = value
        self.__mutex = Lock()

    def get(self) -> int:
        """
        returns current count
        """
        self.__mutex.acquire()
        v = self.__counter
        self.__mutex.release()
        return v

    def get_nowait(self) -> int:
        """
        Return current count immediately
        """
        return  self.__counter

    def acquire(self) -> None:
        """
        Acquire mutex, does not need to be called unless extended ._nowait() is needed

        post: release() called after
        """
        self.__mutex.acquire()

    def release(self) -> None:
        """
        Release mutex

        pre: acquire() called before
        """
        self.__mutex.release()

    def decrement(self) -> None:
        """
        Decrement count
        """
        self.__mutex.acquire()
        v = self.__counter - 1

        if v < 0:
            self.__mutex.release()
            logging.critical("Counter was decremented below 0")
            raise ValueError()

        self.__counter -= 1
        self.__mutex.release()

    def decrement_nowait(self) -> None:
        """
        Decrement count immediately
        """
        v = self.__counter - 1

        if v < 0:
            logging.critical("Counter was decremented below 0")
            raise ValueError()

        self.__counter -= 1

    def increment(self) -> None:
        """
        Increment count
        """
        self.__mutex.acquire()
        self.__counter += 1
        self.__mutex.release()

    def increment_nowait(self) -> None:
        """
        Increment count immediately
        """
        self.__counter += 1


class ThreadPool():
    # Download task queue, Contains tuples in the structure: (func(),(args1,args2,...))
    __task_queues: list[list[tuple]]
    __threads: list         # List of threads in the threadpool
    __tcount: int           # Number of threads
    __kill: list[bool]      # Thread kill switch
    __queue_lock: Lock      # Lock for all queues
    __tasks: any            # Semaphore for number of tasks remaining
    __num_tasks: MutexCounter   # Counter for number of tasks remaining
    __alive: bool    # Flag for active and inactive threadpool
    __mutex: Lock    # Mutex for all tasks done
    __all_tasks_done: threading.Condition   # Conditional for task done

    def __init__(self, tcount: int) -> None:
        """
        Initializes a threadpool

        Param:
            tcount: Number of threads for the threadpool
        """
        # Init queues
        self.__task_queues = []

        # +1 since this includes the main queue
        for i in range(0, tcount + 1):
            self.__task_queues.append([])

        self.__tcount = tcount
        self.__kill = [False]
        self.__queue_lock = Lock()
        self.__tasks = threading.Semaphore(0)
        self.__num_tasks = MutexCounter(0)
        self.__alive = False

        self.__mutex = Lock()
        self.__all_tasks_done = threading.Condition(self.__mutex)

    def start_threads(self) -> None:
        """
        Creates count number of downThreads and starts it
        """
        self.__threads = []

        # Spawn threads
        for i in range(0, self.__tcount):
            self.__threads.append(ThreadPool.TaskThread(id=i, task_queue=self.__task_queues, queue_lock=self.__queue_lock,
                                  tasks=self.__tasks, kill_switch=self.__kill, num_tasks=self.__num_tasks, all_tasks_done=self.__all_tasks_done))
            self.__threads[i].start()

        self.__alive = True
        logging.debug(str(self.__tcount) + " threads have been started")

    def kill_threads(self) -> None:
        """
        Kills all threads in threadpool. Threads are restarted and killed using a
        switch, deadlocked or infinitely running threads cannot be killed using
        this function.

        Unfinished tasks may still exist in the threadpool, however, current tasks 
        will be finished before killing
        """
        # Kill switch
        self.__kill[0] = True

        # Wake up all sleeping threads

        #to_release = 0 if self.__num_tasks.get_nowait(
        #) - self.__tcount >= 0 else self.__tcount - self.__num_tasks.get_nowait()
        
        # number of threads tasks are released because there may be tasks left over after threads are killed
        to_release = self.__tcount
        for i in range(0, to_release):
            self.__tasks.release()


        # Wait for each thead to terminate
        for i in self.__threads:
            i.join()

        self.__alive = False
        logging.debug(str(len(self.__threads)) +
                      " threads have been terminated")
        self.__kill[0] = False

    def enqueue(self, task: tuple) -> None:
        """
        Put an item in task queue

        Param:
            task: tuple in the structure (func(),(args1,args2,...))
        """
        self.__queue_lock.acquire()

        # Called by main thread
        if not hasattr(thread_id, 'id'):
            self.__task_queues[0].append(task)
            logging.debug("Enqueued into task queue #0: " + str(task))
        # Called by worker
        else:
            self.__task_queues[thread_id.id + 1].insert(0, task)
            logging.debug("Enqueued into task queue #" +
                          str(thread_id.id) + ": " + str(task))

        self.__queue_lock.release()
        self.__num_tasks.increment()
        self.__tasks.release()
       

    def join_queue(self) -> None:
        """
        Blocks until all task queue items have been processed
        """
        logging.debug("Blocking until all tasks are complete")
        with self.__all_tasks_done:
            while self.__num_tasks.get() > 0:
                self.__tasks.release()
                self.__all_tasks_done.wait()

    def get_qsize(self) -> int:
        """
        Get queue size

        Return: task queue size
        """
        return self.__num_tasks.get()

    def get_status(self) -> bool:
        """
        Check if the threadpool is alive

        Return: True if alive, false if not
        """
        return self.__alive

    class TaskThread(threading.Thread):
        """
        Fully generic threadpool where tasks of any kind is stored and retrieved in task_queue,
        threads are daemon threads and can be killed using kill variable. 
        """
        __id: int                       # ID of thread == thread_id.id when run() executes      
        __task_queue: list[list]        # Contains all queues
        __queue_mutex: Lock             # Lock for queues
        __tasks: any                    # Sem for number of tasks
        __kill_switch: list[bool]       # Kill switch that can be turned on by an outside function
        __num_tasks: MutexCounter       # Counts number of tasks remaining
        __all_tasks_done: threading.Condition   # Wake up all sleeping threads if tasks are all completed.

        def __init__(self, id: int, task_queue: list[list], queue_lock: Lock, tasks: any, kill_switch: list[bool], num_tasks: MutexCounter, all_tasks_done: threading.Condition) -> None:
            """
            Initializes thread with a thread name
            Param: 
                id: thread identifier
                task_queue: Queues to get tasks from, already initialized. 0 is main queue while task_queue[id + 1] describes which threads queue
                tasks: Semaphore assoaciated with task queue(s), already initialized
                kill_switch: Kill switch
                num_tasks: Number of tasks left 
            """
            
            self.__id = id
            self.__task_queue = task_queue
            self.__tasks = tasks
            self.__queue_mutex = queue_lock
            self.__kill_switch = kill_switch
            self.__num_tasks = num_tasks
            self.__all_tasks_done = all_tasks_done

            super(ThreadPool.TaskThread, self).__init__(daemon=True)

        def run(self) -> None:
            """
            Worker thread job. Blocks until a task is avalable via downloadables
            and retreives the task from download_queue
            """
            # Set each threads id
            thread_id.id = self.__id

            while True:
                # Wait until download is available ############
                self.__tasks.acquire()

                # Check kill signal ###########################
                if self.__kill_switch[0]:
                    logging.debug(
                        "Thread #" + str(thread_id.id) + " has terminated")
                    return

                # Pop queue and download it ###################
                self.__queue_mutex.acquire()
                task = None

                # Visit own queue
                if len(self.__task_queue[thread_id.id + 1]) > 0:
                    task = self.__task_queue[thread_id.id + 1].pop(0)
                curr = 0

                # Check the other queues
                while not task and curr < len(self.__task_queue):
                    if len(self.__task_queue[curr]) > 0:
                        task = self.__task_queue[curr].pop()
                    curr += 1
                
                # If there are no tasks remaining, thread will broadcast this 
                if not task: 
                    logging.info("No task acquired, waking up waiting threads")
                    self.__queue_mutex.release()

                    with self.__all_tasks_done:
                        self.__all_tasks_done.notify_all()
                    return

                # Release queue mutex as we are done with queues
                self.__queue_mutex.release()
                self.__num_tasks.decrement()

                # Process the task ############################
                logging.debug("Thread #" + str(thread_id.id) +
                              " Processing: " + str(task))
                task[0](*task[1])
