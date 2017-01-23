/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

/* global __dirname, require */

const gulp = require('gulp');
const watch = require('gulp-watch');

gulp.task('static:watch', () => {
    return gulp.src('./kuma/static/**/*')
        .pipe(watch('./kuma/static/**/*', {
            'verbose': true
        }))
        .pipe(gulp.dest('./static'));
});

gulp.task('default', () => {
    gulp.start('static:watch');
});
