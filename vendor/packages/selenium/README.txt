About Selenium Python Client Driver

This is a redistribution of the Python client driver that is part
of Selenium RC.

The reason this redistribution exists is that Python programmers
need an easy way of installing their client driver. 

About Selenium RC

Selenium RC (aka SRC) is a server that allows you to launch browser sessions and
run Selenium tests in those browsers. Conceptually, the server exposes two main
interfaces to the outside. One is for controlling the browser, the other is to 
receive commands that instruct it what to do. This way, independent processes 
(think: test programs) can instruct SRC which action to perform on the browser.

In order to achieve this, the SRC server acts as an intercepting proxy for the 
browser. With the initial URL at startup, the browser obtains the Selenium
engine (Selenium Core and other tools). Subsequent calls to open URLs are passed
through SRC which proxies these requests. This way the AUT is received and can
be controlled by Selenium in the browser. Further commands do the usual Selenium
stuff, like asserting page elements, clicking links and filling forms. All these
commands are received by SRC through its command interface from independent
processes. There is a variety of language bindings available (Java, Python, 
Ruby, ...) to write programs to this end.

Additionally to the image provided in the Selenium RC tutorial there is a
(slightly more accessible) overview diagram of the Selenium RC architecture in
the attachment section of this article (selenium-rc-overview.pdf). If you want
to get started with Selenium RC, do read the tutorial.

 Python Client Driver 

More about Selenium Remote Control:

http://wiki.openqa.org/display/SRC/Home