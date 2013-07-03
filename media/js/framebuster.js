/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

// Quick and dirty way to bust out of a frame / iframe.
if (top.location != self.location) {
    top.location = self.location.href;
}
