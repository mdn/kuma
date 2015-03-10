import os
import sys
import site

ROOT = os.path.dirname(os.path.abspath(__file__))


def setup():
    prev_sys_path = list(sys.path)
    vendor_path = os.path.join(ROOT, '..', 'vendor')
    site.addsitedir(vendor_path)

    # Move the new items to the front of sys.path.
    new_sys_path = []
    for item in list(sys.path):
        if item not in prev_sys_path:
            new_sys_path.append(item)
            sys.path.remove(item)
    sys.path[:0] = new_sys_path
