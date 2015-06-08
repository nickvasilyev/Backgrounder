#Backgrounder README

[![Build Status](https://travis-ci.org/nickvasilyev/Backgrounder.svg?branch=develop)](https://travis-ci.org/nickvasilyev/Backgrounder)

Lets say you have something like this: 

    x = self.slow_data_getting_function(some_args) #Lets say this takes a second
    while x:
        self.slow_processing_function(x) #Lets say this takes a second too
        x = self.slow_data_getting_function(some_args)

You can run it like this with backgroudner and cut the time almost in half:

    bg=Backgrounder(self.slow_data_getting_function,fn_args=[some_args]) #Starts backgrounder
    while bg.status(): 
        x = bg.get_one() #While it is running pull out some items
        if x:
            self.slow_processing_function(x) $Process it. Once this is done, next data from slow_data_getting_function is already available.
            
If this has to process 10 items, it will take 20 seconds and some change. 10 seconds for pulling and 10 seconds for processing.Backgroudner is supposed to run methods like getdata in a background thread, so once do_stuff_to() returns, the next call to getdata will pull results that are already local.

Results look something like this:

    2015-04-28 22:28:22,282 [INFO] (27495) (MainThread) Running CASE1 - Simple fetch/process - No Backgrounder
    2015-04-28 22:28:22,282 [INFO] (27495) (MainThread) Slow fetch process getting data 10
    2015-04-28 22:28:23,282 [INFO] (27495) (MainThread) Running a slow processing function: 10
    2015-04-28 22:28:24,282 [INFO] (27495) (MainThread) Slow fetch process getting data 9
    2015-04-28 22:28:25,282 [INFO] (27495) (MainThread) Running a slow processing function: 9
    2015-04-28 22:28:26,282 [INFO] (27495) (MainThread) Slow fetch process getting data 8
    2015-04-28 22:28:27,282 [INFO] (27495) (MainThread) Running a slow processing function: 8
    2015-04-28 22:28:28,282 [INFO] (27495) (MainThread) Slow fetch process getting data 7
    2015-04-28 22:28:29,282 [INFO] (27495) (MainThread) Running a slow processing function: 7
    2015-04-28 22:28:30,282 [INFO] (27495) (MainThread) Slow fetch process getting data 6
    2015-04-28 22:28:31,282 [INFO] (27495) (MainThread) Running a slow processing function: 6
    2015-04-28 22:28:32,282 [INFO] (27495) (MainThread) Slow fetch process getting data 5
    2015-04-28 22:28:33,282 [INFO] (27495) (MainThread) Running a slow processing function: 5
    2015-04-28 22:28:34,282 [INFO] (27495) (MainThread) Slow fetch process getting data 4
    2015-04-28 22:28:35,282 [INFO] (27495) (MainThread) Running a slow processing function: 4
    2015-04-28 22:28:36,282 [INFO] (27495) (MainThread) Slow fetch process getting data 3
    2015-04-28 22:28:37,282 [INFO] (27495) (MainThread) Running a slow processing function: 3
    2015-04-28 22:28:38,282 [INFO] (27495) (MainThread) Slow fetch process getting data 2
    2015-04-28 22:28:39,282 [INFO] (27495) (MainThread) Running a slow processing function: 2
    2015-04-28 22:28:40,282 [INFO] (27495) (MainThread) Slow fetch process getting data 1
    2015-04-28 22:28:41,282 [INFO] (27495) (MainThread) Running a slow processing function: 1
    2015-04-28 22:28:42,282 [INFO] (27495) (MainThread) CASE 1 Finished - Took 20.00010108947754
    .2015-04-28 22:28:42,283 [INFO] (27495) (MainThread) Running CASE1BG - Simple fetch/process - With Backgrounder defaults
    2015-04-28 22:28:44,284 [INFO] (27495) (Thread-1  ) Slow fetch process getting data 10
    2015-04-28 22:28:45,284 [INFO] (27495) (Thread-1  ) Slow fetch process getting data 9
    2015-04-28 22:28:45,285 [INFO] (27495) (MainThread) Running a slow processing function: 10
    2015-04-28 22:28:46,284 [INFO] (27495) (Thread-1  ) Slow fetch process getting data 8
    2015-04-28 22:28:46,285 [INFO] (27495) (MainThread) Running a slow processing function: 9
    2015-04-28 22:28:47,285 [INFO] (27495) (Thread-1  ) Slow fetch process getting data 7
    2015-04-28 22:28:47,285 [INFO] (27495) (MainThread) Running a slow processing function: 8
    2015-04-28 22:28:48,285 [INFO] (27495) (Thread-1  ) Slow fetch process getting data 6
    2015-04-28 22:28:48,286 [INFO] (27495) (MainThread) Running a slow processing function: 7
    2015-04-28 22:28:49,285 [INFO] (27495) (Thread-1  ) Slow fetch process getting data 5
    2015-04-28 22:28:49,286 [INFO] (27495) (MainThread) Running a slow processing function: 6
    2015-04-28 22:28:50,285 [INFO] (27495) (Thread-1  ) Slow fetch process getting data 4
    2015-04-28 22:28:50,286 [INFO] (27495) (MainThread) Running a slow processing function: 5
    2015-04-28 22:28:51,285 [INFO] (27495) (Thread-1  ) Slow fetch process getting data 3
    2015-04-28 22:28:51,286 [INFO] (27495) (MainThread) Running a slow processing function: 4
    2015-04-28 22:28:52,285 [INFO] (27495) (Thread-1  ) Slow fetch process getting data 2
    2015-04-28 22:28:52,286 [INFO] (27495) (MainThread) Running a slow processing function: 3
    2015-04-28 22:28:53,285 [INFO] (27495) (Thread-1  ) Slow fetch process getting data 1
    2015-04-28 22:28:53,286 [INFO] (27495) (MainThread) Running a slow processing function: 2
    2015-04-28 22:28:54,285 [DEBUG] (27495) (Thread-1  ) Got Sentinel Value
    2015-04-28 22:28:54,286 [INFO] (27495) (MainThread) Running a slow processing function: 1
    2015-04-28 22:28:55,286 [INFO] (27495) (MainThread) CASE 1BG Finished - Took 13.002686023712158


You can insert this in there and make it run in the background, while do_stuff_to() runs. This way, When do_stuff_to() comes back, you don't have to wait to get the next some_item, instead it will already be there waiting for you.

Usage Examples:

Let say you have something like this:

    def slow_data_getting_function(self,delay,inp):
        try:
            x = inp.pop(0)
            logging.info("slow_data_getting_function: DELAY: {}, DATA: {}".format(delay,str(x)))
            sleep(delay)
            return x
        except:
            return False

    def slow_processing_function(self,x):
        #Will wait for a second and return the item passed to it. 
        logging.info("slow_processing_function: {}".format(str(x)))
        sleep(1)
        return x
        
And you run it like this:

    test1 = [x for x in range(1,21)] 
    test1results=[]
    x = self.slow_data_getting_function(1,test1)
    while x:
        test1results.append(self.slow_processing_function(x))
        x = self.slow_data_getting_function(1,test1)

You can run it like this with backgroudner and cut the time almost in half:

    test2 = [x for x in range(1,21)]
    test2results = []
    bg=Backgrounder(self.slow_data_getting_function,fn_args=[1,test2])
    while bg.status():
        x = bg.get_one()
        if x:
            test2results.append(self.slow_processing_function(x))
            

Additionally, if the results of the next data_getting function are determined by the results of the previous query, like this:

    def reusable_slow_db_function(self,start_id,offset,max_id):
        #Returns a range from sid to mid
        sleep(1)
        if offset > max_id:
            return False
        d = [x for x in range(start_id,offset)]
        return d

    test1 = [x for x in range(1,101)] 
    start_id = 1
    offset = 10
    max_id = 100
    test1results = []
    while True:
        data = self.reusable_slow_db_function(start_id,offset,max_id)
        if data:
            test1results.append(self.slow_processing_function(data))
            start_id = max(data) + 1
            offset = start_id + 10
        else:
            break
    
You can run it with backgrounder by passing it a closure like so, note that you have to tell Backgrounder that it is a closure through closure=True argument:
  
    def closure_test(self,start_id,offset,max_id):
        #Something like getting data from the database
        because_python = {
            'start_id': start_id,
            'offset': offset,
            'max_id': max_id}
        def inner():
            data = self.reusable_slow_db_function(because_python['start_id'],because_python['offset'],because_python['max_id'])
            if data:
                because_python['start_id'] = max(data)+1
                because_python['offset'] = because_python['start_id'] + 10
            return data
        return inner
        
        
    test3 = [x for x in range(1,101)] 
    start_id = 1
    offset = 10
    max_id = 100
    test3results = []
    a = time()
    bg = Backgrounder(self.closure_test, fn_args=[start_id,offset,max_id],closure=True)
    while bg.status():
        data = bg.get_one()
        if data:
            test3results.append(self.slow_processing_function(data))
            
Check out the unit tests for more examples on how to run it. 
