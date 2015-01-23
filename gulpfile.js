var gulp = require('gulp');
var install = require('gulp-install');
var mainBowerFiles = require('main-bower-files');

var npmManifest = ['package.json'];
var bowerManifest = ['bower.json'];

gulp.task('default', ['install-npm-packages', 'build-javascript']);

gulp.task('watch', ['default'], function() {
    gulp.watch(npmManifest, ['install-npm-packages']);
    gulp.watch(bowerManifest, ['install-bower-packages']);
});

gulp.task('install-npm-packages', function() {
    gulp.src(npmManifest)
        .pipe(install());
});

gulp.task('install-bower-packages', function() {
    return gulp.src(bowerManifest)
               .pipe(install());
});

gulp.task('build-javascript', ['install-bower-packages'], function() {
    var productionJS = mainBowerFiles({ filter: '**/*.js' });
    gulp.src(productionJS)
        .pipe(gulp.dest('media/js/libs'));
});
