/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

const gulp = require('gulp');
const sass = require('gulp-sass');
const stylelint = require('gulp-stylelint');
const watch = require('gulp-watch');

// compiles top-level .scss files
gulp.task('styles', () => {
    // Process files in /styles root
    gulp.src('./kuma/static/styles/*.scss')
        .pipe(sass().on('error', sass.logError))
        // send compiled files to where expected by Django Pipeline
        .pipe(gulp.dest('./static/styles'));
    // Process files in /styles/locales
    gulp.src('./kuma/static/styles/locales/*.scss')
        .pipe(sass().on('error', sass.logError))
        // send compiled files to where expected by Django Pipeline
        .pipe(gulp.dest('./static/styles/locales'));
});

// lints .scss files with stylelint
gulp.task('css:lint', () => {
  return gulp.src('./kuma/static/styles/**/*.scss')
    .pipe(stylelint({
      reporters: [{
        formatter: 'string',
        console: true
      }]
    }));
});

// initiates 'styles' task above for *all* .scss file changes
// (so if a lib file is changed, re-render all top-level .scss files that may include said lib file)
gulp.task('styles:watch', () => {
    /* compile all files */
    gulp.watch('./kuma/static/styles/**/*.scss', ['styles']);
    /* pass only changed file to the linter */
    gulp.watch('./kuma/static/styles/**/*.scss').on('change', file => {
      return gulp.src(file.path)
        .pipe(stylelint({
            failAfterError: false,
            reporters: [{
                formatter: 'string',
                console: true
            }]
        }));
   });
});

// watches all non-Sass files in /kuma/static and copies them over to /static
gulp.task('static:watch', () => {
    return gulp.src('./kuma/static/**/*')
        .pipe(watch(['./kuma/static/**/*', '!./kuma/static/styles/**/*.scss', '!./kuma/static/styles/**/*.sass'], {
            'verbose': true
        }))
        .pipe(gulp.dest('./static'));
});

gulp.task('default', () => {
    gulp.start(['static:watch', 'styles:watch']);
});
