#make sure all tests in this file are dispatched to the same subprocess
def setup():
    pass

def test_timeout():
    "this test *should* fail when process-timeout=1"
    from time import sleep
    sleep(2)

# check timeout will not prevent remaining tests dispatched to the same subprocess to continue to run
def test_pass():
    pass
