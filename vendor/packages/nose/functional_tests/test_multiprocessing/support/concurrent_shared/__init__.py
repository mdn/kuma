counter=[0]
_multiprocess_shared_ = True
def setup_package():
    counter[0] += 1
def teardown_package():
    counter[0] -= 1
