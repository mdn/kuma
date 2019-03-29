/* Prevent auto-execution of scripts when no explicit dataType was provided
 * See https://github.com/jquery/jquery/issues/2432
 */
jQuery.ajaxPrefilter( function( s ) {
    if ( s.crossDomain ) {
        s.contents.script = false;
    }
} );
