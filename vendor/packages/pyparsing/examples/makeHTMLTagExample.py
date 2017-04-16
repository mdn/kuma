import urllib

from pyparsing import *

anchorStart,anchorEnd = makeHTMLTags("a")

# read HTML from a web page
serverListPage = urllib.urlopen( "http://www.yahoo.com" )
htmlText = serverListPage.read()
serverListPage.close()

anchor = anchorStart + SkipTo(anchorEnd).setResultsName("body") + anchorEnd


for tokens,start,end in anchor.scanString(htmlText):
    print tokens.body,'->',tokens.href
    