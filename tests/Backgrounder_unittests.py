import logging
import sys
import code
import unittest
import backgrounder
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s [%(levelname)s] (%(process)d) (%(threadName)-10s) %(message)s')
from time import time,sleep


class BackgrounderTests(unittest.TestCase):
    # Regular functions
    def reusable_slow_db_function(self,start_id,offset,max_id):
        # Returns a range from sid to mid
        logging.info("reusable_slow_db_function start: {}, offset:{}, max:{}".format(start_id,offset,max_id))
        sleep(1)
        if offset > max_id:
            return False
        d = [x for x in range(start_id,offset)]
        logging.info("Returning " + str(d))
        return d
    
    def closure_test(self,start_id,offset,max_id):
        # Something like getting data from the database
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
    
    def slow_processing_function(self, x):
        # Will wait for a second and return the item passed to it.
        logging.info("slow_processing_function: {}".format(str(x)))
        sleep(1)
        return x

    def ver_slow_processing_function(self, x):
        # Will wait 2 seconds and return the item passed to it.
        logging.info("Running a slow processing function: {}".format(str(x)))
        sleep(2)
        return x

    def fast_processing_function(self, x):
        logging.info("Running a fast processing function: {}".format(str(x)))
        return x

    def slow_data_getting_function(self,delay,inp):
        try:
            x = inp.pop(0)
            logging.info("slow_data_getting_function: DELAY: {}, DATA: {}".format(delay,str(x)))
            sleep(delay)
            return x
        except:
            return False
    
    def slow_generator(self,delay,data,sentinel='potato'):
        logging.info("Starting Generator with DELAY: {}, DATA: {}".format(delay,data))
        for x in data:
            logging.info("slow_generator: DELAY: {} DATA: {}".format(delay,x))
            sleep(delay)
            yield x
    
    #### 
    #### Test Cases

    def test_regular_slow_function(self):
        basedata = [x for x in range(1,21)] 
        #Run it as usually
        test1 = list(basedata)
        test1results = []
        a = time()
        x = self.slow_data_getting_function(1,test1)
        while x and x != 'sentinel':
            test1results.append(self.slow_processing_function(x))
            x = self.slow_data_getting_function(1,test1)
        logging.info("test_regular_function Regular Completed in {} seconds".format(str(time() - a)))
        
        
        #Run it with BG
        logging.info("test_regular_function Starting test with Backgrounder")
        test2 = list(basedata)
        test2results = []
        a = time()
        bg = backgrounder.Backgrounder(self.slow_data_getting_function,fn_args=[1,test2])
        while bg.status():
            x = bg.get_one()
            if x and x != 'sentinel':
                test2results.append(self.slow_processing_function(x))
        logging.info("test_regular_function Backgrounder Completed in {} seconds".format(str(time() - a)))
        logging.info(test1results)
        logging.info(test2results)
        self.assertEqual(test1results,test2results)

    def test_regular_fast_function(self):
        basedata = [x for x in range(1,21)]
        #Run it as usually
        test1 = list(basedata)
        test1results = []
        a = time()
        x = self.slow_data_getting_function(1, test1)
        while x and x != 'sentinel':
            test1results.append(self.fast_processing_function(x))
            x = self.slow_data_getting_function(1, test1)
        logging.info("test_regular_fast_function Regular Completed in {} seconds".format(str(time() - a)))


        #Run it with BG
        logging.info("test_regular_fast_function Starting test with Backgrounder")
        test2 = list(basedata)
        test2results = []
        a = time()
        bg = backgrounder.Backgrounder(self.slow_data_getting_function, fn_args=[1, test2],min_threads=3)
        while bg.status():
            x = bg.get_one()
            if x and x != 'sentinel':
                test2results.append(self.fast_processing_function(x))
        logging.info("test_regular_fast_function Backgrounder Completed in {} seconds".format(str(time() - a)))
        logging.info(test1results)
        logging.info(test2results)
        self.assertEqual(test1results,test2results)

    def test_closure_function(self):
        basedata = [x for x in range(1,101)] 
        
        logging.info("Starting test_closure_function Regular")
        test1 = list(basedata)
        start_id = 1
        offset = 10
        max_id = 100
        a = time()
        test1results = []
        while True:
            data = self.reusable_slow_db_function(start_id,offset,max_id)
            if data:
                test1results.append(self.slow_processing_function(data))
                start_id = max(data) + 1
                offset = start_id + 10
            else:
                break
        logging.info("test_closure_function Regular Completed in {} seconds".format(str(time() - a)))
        
        #Test Closure
        logging.info("test_closure_function Testing Closure without Backgrounder")
        test2 = list(basedata)
        start_id = 1
        offset = 10
        max_id = 100
        test2results = []
        a = time()
        closure = self.closure_test(start_id,offset,max_id)
        while True:
            data = closure()
            if data:
                test2results.append(self.slow_processing_function(data))
            else:
                break 
        logging.info("test_closure_function Testing Closure without Backgrounder Completed in {} seconds".format(str(time() - a)))
        self.assertEqual(test1results,test2results)
        
        #Test Closure with BG
        logging.info("test_closure_function Testing Closure with Backgrounder")
        test3 = list(basedata)
        start_id = 1
        offset = 10
        max_id = 100
        test3results = []
        a = time()
        bg = backgrounder.Backgrounder(self.closure_test, fn_args=[start_id,offset,max_id], closure=True)
        while bg.status():
            data = bg.get_one()
            if data is not False:
                test3results.append(self.slow_processing_function(data))
        logging.info("test_closure_function Testing Closure with Backgrounder Completed in {} seconds".format(str(time() - a)))
        for x in [test1results,test2results,test3results]:
            logging.info(x)
        self.assertEqual(test1results,test3results)
    
    

    def test_with_generator_as_input(self):
        basedata = [x for x in range(1,11)] 
        
        logging.info("Starting test_with_generator_as_input Regular")
        test1 = list(basedata)
        a = time()
        test1results = []
        for data in self.slow_generator(1,test1,'sentinel'):
            if data:
                test1results.append(self.slow_processing_function(data))
        logging.info("test_with_generator_as_input Testing Regular Completed in {} seconds".format(str(time() - a)))
        
        # Starting Backgrounder Test
        logging.info("Starting test_with_generator_as_input Backgrounder")
        test2 = list(basedata)
        a = time()
        test2results = []
        bg = backgrounder.Backgrounder(self.slow_generator, fn_args=[1, test2], generator=True)
        while bg.status():
            data = bg.get_one()
            if data:
                test2results.append(self.slow_processing_function(data))
        logging.info("test_with_generator_as_input Testing Backgrounder Completed in {} seconds".format(str(time() - a)))
        logging.info(test1results)
        logging.info(test2results)
        self.assertEqual(test1results,test2results)
        
    @unittest.skip("WIP")
    def test_nested_backgrounders(self):
        basedata = [x for x in range(1,21)]
        
        # Regular test without back grounder
        logging.info("Starting test_nested_backgrounders Regular")
        '''
        Pull and process both running in backgrounder with a shared queue        
        

        test1 = list(basedata)
        test1results = []
        a = time()
        x = self.slow_data_getting_function(1,test1)
        while x and x != 'sentinel_get':
            test1results.append(self.slow_processing_function(x))
            x = self.slow_data_getting_function(1,test1)
        logging.info("test_nested_backgrounders Testing Regular Completed in {} seconds".format(str(time() - a)))
        '''
        
        logging.info("Starting test_nested_backgrounders Backgrounder")
        test2 = list(basedata)
        test2results = []
        a = time()
        bg_get = backgrounder.Backgrounder(self.slow_data_getting_function,fn_args=[1,test2],sentinel='sentinel_get',name='bg_get')
        bg_proc = backgrounder.Backgrounder(self.slow_processing_function,in_bg=bg_get,max_threads=1)
        while bg_proc.status():
            x = bg_proc.get_one()
            if x and x != 'sentinel':
                test2results.append(x)
        sleep(1)
        logging.info("BG_PROC_QUEUE: {}".format(bg_proc.out_q.qsize()))
            
        logging.info("test_nested_backgrounders Testing Backgrounder Completed in {} seconds".format(str(time() - a)))
        logging.info(test1results)
        logging.info(test2results)
        self.assertEqual(test1results,test2results)
            
        
        
        
if __name__ == '__main__':
    unittest.main()