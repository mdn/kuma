suite( 'Description list - enter at the end of an item changes blok type' );

test( 'at the end of a single-item list in dt', function() {
	tests.setHtmlWithSelection( '<dl><dt>foo[]</dt></dl>' );
	tests.editor.execCommand( 'enter' );
	assert.areSame( '<dl><dt>foo</dt><dd>[]</dd></dl>', tests.getHtmlWithSelection() );
} );

test( 'at the end of a single-item list in dd', function() {
	tests.setHtmlWithSelection( '<dl><dd>foo[]</dd></dl>' );
	tests.editor.execCommand( 'enter' );
	assert.areSame( '<dl><dd>foo</dd><dt>[]</dt></dl>', tests.getHtmlWithSelection() );
} );

test( 'in the middle of a multi-item list', function() {
	tests.setHtmlWithSelection( '<dl><dt>x</dt><dd>foo[]</dd><dt>y</dt></dl>' );
	tests.editor.execCommand( 'enter' );
	assert.areSame( '<dl><dt>x</dt><dd>foo</dd><dt>[]</dt><dt>y</dt></dl>', tests.getHtmlWithSelection() );
} );

suite( 'Description list - enter not at the end of an item splits it' );

test( 'at the beginning of a single-item list', function() {
	tests.setHtmlWithSelection( '<dl><dt>[]foo</dt></dl>' );
	tests.editor.execCommand( 'enter' );
	assert.areSame( '<dl><dt>&nbsp;</dt><dt>[]foo</dt></dl>', tests.getHtmlWithSelection() );
} );

test( 'in the middle of a multi-item list', function() {
	tests.setHtmlWithSelection( '<dl><dd>x</dd><dt>ff[]oo</dt><dd>y</dd></dl>' );
	tests.editor.execCommand( 'enter' );
	assert.areSame( '<dl><dd>x</dd><dt>ff</dt><dt>[]oo</dt><dd>y</dd></dl>', tests.getHtmlWithSelection() );
} );

suite( 'Description list - enter in an empty item splits list' );

test( 'in a single-item a list', function() {
	tests.setHtmlWithSelection( '<p>x</p><dl><dt>[]@</dt></dl><p>y</p>' );
	tests.editor.execCommand( 'enter' );
	assert.areSame( '<p>x</p><p>[]</p><p>y</p>', tests.getHtmlWithSelection() );
} );

test( 'in the middle of a list', function() {
	tests.setHtmlWithSelection( '<p>x</p><dl><dd>a</dd><dt>[]@</dt><dd>b</dd></dl><p>y</p>' );
	tests.editor.execCommand( 'enter' );
	assert.areSame( '<p>x</p><dl><dd>a</dd></dl><p>[]</p><dl><dd>b</dd></dl><p>y</p>',
		tests.getHtmlWithSelection() );
} );

test( 'at the end of a list', function() {
	tests.setHtmlWithSelection( '<p>x</p><dl><dd>a</dd><dt>[]@</dt></dl><p>y</p>' );
	tests.editor.execCommand( 'enter' );
	assert.areSame( '<p>x</p><dl><dd>a</dd></dl><p>[]</p><p>y</p>', tests.getHtmlWithSelection() );
} );

test( 'at the beginning of a list', function() {
	tests.setHtmlWithSelection( '<p>x</p><dl><dt>[]@</dt><dd>a</dd></dl><p>y</p>' );
	tests.editor.execCommand( 'enter' );
	assert.areSame( '<p>x</p><p>[]</p><dl><dd>a</dd></dl><p>y</p>', tests.getHtmlWithSelection() );
} );