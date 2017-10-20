// Quick and dirty way to bust out of a frame / iframe.
if (top.location !== self.location) {
    top.location = self.location.href;
}
