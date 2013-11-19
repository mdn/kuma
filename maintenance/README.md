These files are stored here only for revision control. Getting them served up will always require additional work.

To use an asset that would normally be served from the CDN:

1. Attach the asset to index.html relative to the CDN root. For example, to attach `https://developer.cdn.mozilla.net/media/css/mdn-min.css`, use

   ```html
   <link rel="stylesheet" media="screen,projection,tv" href="media/css/mdn-min.css" />
   ```

2. Run `download-assets.sh` in the VM
