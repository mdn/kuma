// Detect the set of OSes and browsers we care about in the wiki.
// Adapted from http://www.quirksmode.org/js/detect.html with these changes:
//
// * Changed the dataOS identity properties to lowercase to match the {for}
//   abbreviations in models.OPERATING_SYSTEMS.
// * Added Maemo and Android OS detection. Removed iPhone.
// * Added Fennec browser detection.
// * Changed Firefox's browser identity to "fx" and Fennec's to "m" to match
//   {for} syntax and avoid yet another representation.
// * Removed fallbacks to the string "an unknown ____" in favor of just
//   returning undefined.
// * Deleted the browsers we don't care about.
var BrowserDetect = {
    init: function () {
        this.browser = this.searchString(this.dataBrowser);
        this.version = this.searchVersion(navigator.userAgent)
            || this.searchVersion(navigator.appVersion);
        this.OS = this.searchString(this.dataOS);
    },
    searchString: function (data) {
        for (var i=0;i<data.length;i++)	{
            var dataString = data[i].string;
            var dataProp = data[i].prop;
            this.versionSearchString = data[i].versionSearch || data[i].identity;
            if (dataString) {
                if (dataString.indexOf(data[i].subString) != -1)
                    return data[i].identity;
            }
            else if (dataProp)
                return data[i].identity;
        }
    },
    searchVersion: function (dataString) {
        var index = dataString.indexOf(this.versionSearchString);
        if (index == -1) return;
        return parseFloat(dataString.substring(index+this.versionSearchString.length+1));  // Turns "1.1.1" into 1.1 rather than 1.11. :-(
    },
    dataBrowser: [
        {
            string: navigator.userAgent,
            subString: "Fennec",
            versionSearch: "Fennec",
            identity: "m"
        },
        {
            string: navigator.userAgent,
            subString: "Firefox",
            versionSearch: "Firefox",
            identity: "fx"
        }
    ],
    dataOS : [
        {
            string: navigator.platform,
            subString: "Win",
            identity: "win"
        },
        {
            string: navigator.platform,
            subString: "Mac",
            identity: "mac"
        },
        {
            string: navigator.userAgent,
            subString: "Android",
            identity: "android"
        },
        {
            string: navigator.userAgent,
            subString: "Maemo",
            identity: "maemo"
        },
        {
            string: navigator.platform,
            subString: "Linux",
            identity: "linux"
        }
    ]
};
BrowserDetect.init();  // TODO: Do this lazily.
