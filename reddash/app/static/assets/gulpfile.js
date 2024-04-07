let gulp = require('gulp');
let path = require('path');
let sass = require('gulp-sass')(require('sass'));
let autoprefixer = require('gulp-autoprefixer');
let sourcemaps = require('gulp-sourcemaps');
let open = require('gulp-open');

let Paths = {
  HERE: './',
  DIST: 'dist/',
  CSS: './css/',
  SCSS_TOOLKIT_SOURCES: './scss/argon-dashboard.scss',
  SCSS: './scss/**/**'
};

gulp.task('scss', function() {
  return gulp.src(Paths.SCSS_TOOLKIT_SOURCES)
    .pipe(sourcemaps.init())
    .pipe(sass().on('error', sass.logError))
    .pipe(autoprefixer())
    .pipe(sourcemaps.write(Paths.HERE))
    .pipe(gulp.dest(Paths.CSS));
});

gulp.task('watch', function() {
  gulp.watch(Paths.SCSS, gulp.series('compile-scss'));
});

gulp.task('open', function() {
  gulp.src('pages/dashboard.html')
    .pipe(open());
});

gulp.task('open-app', gulp.parallel('open', 'watch'));