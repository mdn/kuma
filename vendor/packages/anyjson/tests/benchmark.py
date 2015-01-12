"""
Simple benchmark script to do some basic speed tests of json libs
"""

import sys
import time
import urllib

_small = """
{
    "name": "benchmark test",
    "foo": "bar",
    "age": 32,
    "weight": 100,
    "Height": 154.12,
    "married": false,
    "siblings": [],
    "bar": null
}
"""

_deep = """
{
    "foo": "bar",
    "nest": {
        "foo": %(_small)s,
        "nest": {
            "foo": %(_small)s,
            "nest": {
                "foo": %(_small)s,
                "nest": {
                    "foo": %(_small)s,
                    "nest": {
                        "foo": %(_small)s,
                        "nest": %(_small)s
                    }
                }
            }
        }
    }
}
""" % locals()

_big = """
{
    "biglist": [%(_deep)s, %(_small)s, %(_deep)s, %(_small)s, %(_deep)s,
                %(_deep)s, %(_small)s, %(_deep)s, %(_small)s, %(_deep)s,
                %(_deep)s, %(_small)s, %(_deep)s, %(_small)s, %(_deep)s,
                %(_deep)s, %(_small)s, %(_deep)s, %(_small)s, %(_deep)s,
                %(_deep)s, %(_small)s, %(_deep)s, %(_small)s, %(_deep)s,
                %(_deep)s, %(_small)s, %(_deep)s, %(_small)s, %(_deep)s,
                %(_deep)s, %(_small)s, %(_deep)s, %(_small)s, %(_deep)s,
                %(_deep)s, %(_small)s, %(_deep)s, %(_small)s, %(_deep)s,
                %(_deep)s, %(_small)s, %(_deep)s, %(_small)s, %(_deep)s,
                %(_deep)s, %(_small)s, %(_deep)s, %(_small)s, %(_deep)s,
                %(_deep)s, %(_small)s, %(_deep)s, %(_small)s, %(_deep)s,
                %(_deep)s, %(_small)s, %(_deep)s, %(_small)s, %(_deep)s,
                %(_deep)s, %(_small)s, %(_deep)s, %(_small)s, %(_deep)s,
                %(_deep)s, %(_small)s, %(_deep)s, %(_small)s, %(_deep)s,
                %(_deep)s, %(_small)s, %(_deep)s, %(_small)s, %(_deep)s,
                %(_deep)s, %(_small)s, %(_deep)s, %(_small)s, %(_deep)s,
                %(_deep)s, %(_small)s, %(_deep)s, %(_small)s, %(_deep)s,
                %(_small)s, %(_small)s, %(_small)s, %(_small)s, %(_small)s],
    "entry1": %(_small)s,
    "entry2": %(_deep)s,
    "entry3": %(_small)s,
    "entry4": %(_deep)s,
    "entry5": %(_small)s,
    "entry6": %(_deep)s
}
""" % locals()

# The following two will contain real world json from twitter and reddit if
# script is run with the --download flag
_reddit = "[]"
_twitter = "[]"

def load_external_json():
    global _reddit, _twitter
    _reddit = urllib.urlopen("http://reddit.com/.json").read()
    _twitter = urllib.urlopen("http://api.twitter.com/1/statuses/user_timeline.json?screen_name=twitterapi&count=200").read()


def do_benchmark(impspec, json, runs=10):
    modulename, parsename, emitname = impspec

    try:
        __import__(modulename)
        mod = sys.modules[modulename]
        reads = getattr(mod, parsename)
        dumps = getattr(mod, emitname)
    except:
        return None

    start = time.time()
    for n in xrange(runs):
        data = reads(json)

    readtime = time.time() - start

    start = time.time()
    for n in xrange(runs):
        devnull = dumps(data)

    return readtime, time.time() - start # tuple (readtime, writetime)


modules = [("json", "loads", "dumps"),
           ("simplejson", "loads", "dumps"),
           ("yajl", "loads", "dumps"),
           ("cjson", "decode", "encode"),
           ("django.utils.simplejson", "loads", "dumps"),
           ("jsonpickle", "decode", "encode"),
           ("jsonlib", "read", "write"),
           ("jsonlib2", "read", "write"),
           #("demjson", "decode"), terribly slow. wont include it
           ]

if len(sys.argv) > 1 and sys.argv[1] == "--download":
    load_external_json()

res = []
runs = 100
for e in modules:
    res.append((e[0], do_benchmark(e, _small, runs),
                      do_benchmark(e, _deep , runs),
                      do_benchmark(e, _big, runs),
                      do_benchmark(e, _reddit, runs),
                      do_benchmark(e, _twitter, runs),
    ))

no_res = set([e for e in res if e[1] is None])
res = list(set(res) - no_res)
res = [(e[0], sum(map(lambda x:x[0], e[1:])), sum(map(lambda x:x[1], e[1:]))) for e in res]

res.sort(lambda a,b: cmp((a[1]+a[2]), b[1]+b[2]))

print "Total  Read   Write  Implementation"
print "-----------------------------------"
for e in res:
    print "%.3f  %.3f  %.3f  %s" % (e[1]+e[2], e[1], e[2], e[0])
for e in no_res:
    print "Not installed:", e[0]
