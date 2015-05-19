__author__ = 'nikitavasilyev'
import logging
import sys
from time import time,sleep
import threading
from queue import Queue

#To Do:
#- Fix function arguments
#- Implement a way to increase the number of functions
#- Implement a way to join functions when there is a low load requirement
#- Implement input queue polling
#- Implement input iterator polling
#- Start Joining Threads


#- Joining backgrounders should be at object and not queue level
#- Remap worker processes and COMPLETION to make sure it's sycned


class Backgrounder():

    def __init__(self,
                func,
                name='BG',
                fn_args=(),
                fn_kwargs={},
                in_q = None,
                in_bg = None,
                in_iter = None,
                min_q = 5,
                max_q = 10,
                sentinel=False,
                max_threads = 5,
                min_threads = 1,
                closure=False,
                generator=False,
                ):

        self.func = func
        self.fn_args = fn_args
        self.fn_kwargs = fn_kwargs
        self.in_q = in_q
        self.in_bg = in_bg
        self.in_iter = in_iter
        self.out_q = Queue()
        self.min_q = min_q
        self.name = name
        self.max_q = max_q
        self.sentinel = sentinel
        self.threads = []
        self.running_threads = 0
        self.max_threads = max_threads
        self.min_threads = min_threads
        self.delay = 1
        self.metrics = {}
        self.go = False 
        # Whenever threads should proceed processing. 
        # Can be set to False/True to indicate whenever threads will work or should pause. Will change during runtime.
        self.event_loop_delay = 2
        self.thread_sleep = 0.1
        self.notdone=True 
        # Controls the main execution of things. This will only be set to False when all tasks are processed 
        # as indicated by sentinel value or external call. Threads will finish their current work and stop.
        self.closure = closure
        self.stopper = threading.Thread(target=self._stopper,name='{} - ThreadStopper'.format(self.name))
        self.stopper.start()
        # Turn the logging to super high, used for dev only.
        self.verbose = False
        self.stopathread = False 
        # Will kick in if backgrounder is processing too fast and there are long pauses. 
        # Threadstopper will pick this up and try to stop a thread
        self.totally_done = False 
        # Indicates that all work is finished and all threads are joined. No more modifications to the queues
        self.generator = generator
        if self.closure:
            self.max_threads = 1
            self.func = self.func(*self.fn_args,**self.fn_kwargs)

        if generator:
            self.gen = func(*fn_args,**fn_kwargs)
            self.func = self.gen.__next__
            self.max_threads = 1

        # General Params:
        self.max_event_loop_delay = 70
        self._start()

    def _start(self):
        # Create a separate thread for managing this object
        if self.verbose:
            logging.debug("Starting Backgrounder Processing")
        self.event_loop = threading.Thread(target=self._event_loop,name='{}-EventLoopThread'.format(self.name))
        self.event_loop.start()
        sleep(3)

    def _stopper(self):
        # Internal method for thread joining while processing is happening.
        # Need this because joining threads using event loop thread will pause execution.
        while True:
            sleep(3)
            if self.verbose:
                logging.debug("Stopper checking to see if any threads need to be stopped")
            if self.stopathread is True and len(self.threads) > 2 and len(self.threads) > self.min_threads + 1:
                if self.verbose:
                    logging.debug("Going to try to stop a thread")
                thread = self.threads.pop()
                thread._prep_to_halt()
                thread.join()
                self.stopathread=False
            if not self.notdone:
                return

    def status(self):
        if self.out_q.qsize() != 0:
            # If there is stuff in the out q we are still running
            return True
        elif self.in_q:
            # If there is still in the in q we are still running
            return True
        elif self.in_bg and self.in_bg.status():
            # If up steam backgrounder is still running
            return True
        elif self.notdone:
            # If threads didn't get the sentinel value we are still running
            return True
        elif not self.totally_done:
            return True
        # self._dump_guts()
        return False

    def _dump_guts(self):
        logging.debug("NOTDONE: {}".format(self.notdone))
        logging.debug("OUT_Q_SIZE: {}".format(self.out_q.qsize()))
        logging.debug("TOTALLY_DONE: {}".format(self.totally_done))
        logging.debug("GO: {}".format(self.go))
        logging.debug("threads: {}".format(self.threads))
        if self.in_bg:
            logging.debug("IN_BG: {}".format(self.in_bg.status()))

    def get_one(self):
        if self.out_q.qsize()>0:
            i = self.out_q.get()
            self.out_q.task_done()
            return i

    def get_out_q(self):
        return self.out_q

    def iter(self):
        while self.out_q.qsize() > 0 and self.notdone:
            t = self.out_q.get()
            self.out_q.task_done()
            yield t

    def oqsize(self):
        return self.out_q.qsize()

    def _pause_work(self):
        if self.go:
            if self.verbose:
                logging.debug("Pausing Workers")
            self.go=False

    def _resume_work(self):
        if not self.go:
            if self.verbose:
                logging.debug("Resuming Workers")
            self.go=True

    def _is_working(self):
        return self.go

    def _event_loop_sleep(self):
        if self.verbose:
            logging.debug("Event Loop Sleeping for: {}".format(str(self.event_loop_delay)))
        sleep(self.event_loop_delay)

    def stop_work(self):
        '''
        Start Joining all threads
        '''
        self._pause_work()
        self.notdone = False
        while not self.totally_done:
            sleep(0.1)
            if self.verbose:
                logging.debug("Waiting to be completely finished")
        logging.info("Backgrounder {} is finished".format(self.name))
        return True


    def _event_loop(self):
        [self._start_thread() for x in range(self.min_threads)]
        # Cons tracks consequtive loop iterations without any new action (i.e. queue is not decreasing)
        # Will track to stop a thead if possible and will increase the event loop delay
        cons = 0
        # Run tracks consequtive loop iterations where the threads are still running (i.e. queue is not growing fast enough).
        #  Will try to kick in some additional threads.
        run = 0
        while self.notdone:
            if self.out_q.qsize() < self.max_q:
                cons = 0
                run +=1
                self._resume_work()
                self._event_loop_sleep()

            if self.out_q.qsize() >= self.max_q:
                cons +=1
                runs = 0
                self._pause_work()
                self._event_loop_sleep()

            if cons > 5:
                # More than 5 iterations without doing any new work. Increase the sleep delay
                # This will kick in if we are pulling in data too fast.
                if self.event_loop_delay * 2 > self.max_event_loop_delay:
                    self.event_loop_delay = self.max_event_loop_delay
                else:
                    self.event_loop_delay = self.event_loop_delay * 2
                if self.verbose:
                    logging.debug("Increasing event loop delay to: " + str(self.event_loop_delay))
                runs = 0
                cons = 0
                self.stopathread=True

            if run > 5 and (self.out_q.qsize() < (self.max_q * 0.60)) and len(self.threads) < self.max_threads:
                # If after 5 runs the out queue is still smaller than 60 % of maximum, increase some threads
                # This will kick in if we are pulling in data too slowly to maintain a queue
                logging.debug("Starting Another Thread")
                self._start_thread()
                run = 0
                cons = 0

            cons += 1
            if self.verbose:
                logging.debug("Event Loop Sleeping: CONS: {}, RUNS: {}, outQSize: {}".format(cons,run,self.out_q.qsize()))
                self._dump_guts()
            self.cons = cons
            self.run = run
            self._event_loop_sleep()

        if self.verbose:
            logging.debug("Finished Working, Going to Join Threads")

        for thread in self.threads:
            thread.join()

        if self.verbose:
            logging.debug("Joining the Stopper")
        self.stopper.join()
        self.totally_done = True

    def _start_thread(self):
        if self.verbose:
            logging.debug("Starting New Worker Thread")
        thread = ''
        if self.fn_args and self.fn_kwargs:
            thread = BackgrounderWorker(bg=self,args=(self.fn_args), kwargs=(self.fn_kwargs),name='{}-Worker-{}'.format(self.name,str(len(self.threads)+1)))
        elif self.fn_args:
            thread = BackgrounderWorker(bg=self,args=(self.fn_args),name='{}-Worker-{}'.format(self.name,str(len(self.threads)+1)))
        elif self.fn_kwargs:
            thread = BackgrounderWorker(bg=self,kwargs=(self.fn_kwargs),name='{}-Worker-{}'.format(self.name,str(len(self.threads)+1)))
        else:
            thread = BackgrounderWorker(bg=self,name='{}-Worker-{}'.format(self.name,str(len(self.threads)+1)))
        thread.start()

        self.threads.append(thread)
        return thread


class BackgrounderWorker(threading.Thread):
    def __init__(self,*args,**kwargs):
        threading.Thread.__init__(self)
        self.bg=kwargs['bg']
        self.halt = False
        # Halt means thread should stop after it's loop and get ready to be joined
        self.func = None
        self.got_sentinel = False

        if 'name' in kwargs:
            self._name = kwargs['name']

    def run(self,*args,**kwargs):
        # While the module is running
        while self.bg.notdone:
            # While queue still needs additional items
            while self.bg.go:
                out = ''
                if self.bg.closure:
                    out = self.bg.func()
                elif self.bg.generator:
                    out = self._proc_gen()
                elif self.bg.in_bg:
                    out = self._proc_bg()
                elif self.bg.in_q:
                    out = self._proc_in_q()
                else:
                    out = self.bg.func(*self.bg.fn_args,**self.bg.fn_kwargs)

                if self._is_sentinel(out):
                    self._finish_working()
                else:
                    self.bg.out_q.put(out)

                self._check_if_should_return()
                # End of bg.go loop

            sleep(self.bg.thread_sleep)
            self._check_if_should_return()
            # End of notdone loop
        logging.debug("Thread Completed Task - Marking As Complete")

    def _proc_gen(self):
        try:
            out = self.bg.func()
            return out
        except StopIteration:
            logging.debug("Ran out of iterator")
            self._finish_working()
        except Exception as e:
            logging.exception(e)
            logging.error("Crashed while running the generator")
            self.halt=True


    def _check_if_should_return(self):
        if self.halt:
            logging.debug("Stopping this thread")
            return


    def _proc_bg(self):
        # Pull item from another backgrounder
        try:
            if self.bg.in_bg.out_q.qsize()>0:
                item = self.bg.in_bg.get_one()
                if item:
                    out = self.bg.func(item)
                    if out:
                        return out
                elif self.bg.in_bg.totally_done:
                    self.got_sentinel = True
        except Exception as e:
            logging.error("Processing input: []".format(item))
            logging.exception(e)


    def _proc_in_q(self):
        # Pull item from the queue and process it
        try:
            item = self.bg.in_q.get()
            if item:
                out = self.bg.func(item)
                if out:
                    self.bg.in_q.task_done()
                    return out
        except Exception as e:
            logging.error("Processing input: []".format(item))
            logging.exception(e)


    def _is_sentinel(self,val):
        if val == self.bg.sentinel:
            logging.debug("Got Sentinel Value [{}]".format(val))
            self.got_sentinel = True
            return True
        else:
            return False

    def _check_queues(self):
        if (self.in_q and self.in_q.qsize() != 0) or self.bg.in_bg.out_q.qsize() > 0:
            return
        self._finish_working()
        return

    def _finish_working(self):
        self.bg.notdone = False
        #Stops Event Loop After this Iteration
        self.bg._pause_work()
        #Pauses Threads

    def _prep_to_halt(self):
        logging.debug("Getting ready to terminate thread")
        self.halt=True
