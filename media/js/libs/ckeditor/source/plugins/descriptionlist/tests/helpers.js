'use strict';

tests.setHtmlWithSelection = function( html ) {
	var editor = this.editor,
		editable = editor.editable(),
		range = editor.createRange();

	editable.setHtml(
		tests.encodeBogus( html )
			.replace( '[', '<span id="selectionStart"></span>' )
			.replace( ']', '<span id="selectionEnd"></span>' )
	);

	var startEl = editor.document.findOne( '#selectionStart' ),
		endEl = editor.document.findOne( '#selectionEnd' );

	range.setStartAt( startEl, CKEDITOR.POSITION_BEFORE_START );
	startEl.remove();
	range.setEndAt( endEl, CKEDITOR.POSITION_BEFORE_START );
	endEl.remove();

	editor.focus();
	editor.getSelection().selectRanges( [ range ] );
};

tests.getHtmlWithSelection = function() {
	var editor = this.editor,
		bm = editor.getSelection().getRanges()[ 0 ].createBookmark(),
		startText = editor.document.createText( '[' ),
		endText = editor.document.createText( ']' );

	startText.replace( bm.startNode );

	if ( !bm.collapsed ) {
		endText.replace( bm.endNode );
	} else {
		endText.insertAfter( startText );
	}

	return editor.getData().replace( /\u00a0/g, '&nbsp;' );
};

tests.encodeBogus = function( html ) {
	return html.replace( /@/g, CKEDITOR.env.needsBrFiller ? '<br />' : '' );
};

suite( 'Helpers' );

test( 'make collapsed selection', function( done ) {
	var editor = tests.editor;

	editor.setData( '', function() {
		tests.setHtmlWithSelection( '<p>foo[]bar</p>' );

		var range = editor.getSelection().getRanges()[ 0 ];

		assert.isTrue( range.collapsed, 'range is collapsed' );
		assert.areSame( 1, range.startOffset, 'range.startOffset' );
		assert.areSame( 'p', range.startContainer.getName(), 'range.startContainer' );
		assert.areSame( '<p>foobar</p>', editor.getData() );

		done();
	} );
} );

test( 'make non-collapsed selection', function( done ) {
	var editor = tests.editor;

	editor.setData( '', function() {
		tests.setHtmlWithSelection( '<h1>[foo</h1><p>bar]</p>' );

		var range = editor.getSelection().getRanges()[ 0 ];

		assert.isFalse( range.collapsed, 'range is not collapsed' );
		assert.areSame( 0, range.startOffset, 'range.startOffset' );
		assert.areSame( 1, range.endOffset, 'range.endOffset' );
		assert.areSame( 'h1', range.startContainer.getName(), 'range.startContainer' );
		assert.areSame( 'p', range.endContainer.getName(), 'range.startContainer' );
		assert.areSame( '<h1>foo</h1><p>bar</p>', editor.getData() );

		done();
	} );
} );

test( 'encode bogus br when making selection', function( done ) {
	var editor = tests.editor;

	editor.setData( '', function() {
		tests.setHtmlWithSelection( '<p>x[]x@</p>' );

		var range = editor.getSelection().getRanges()[ 0 ];

		assert.ok( editor.editable().findOne( 'p' ).getBogus() );

		done();
	} );
} );

test( 'get collapsed selection', function() {
	tests.setHtmlWithSelection( '<p>foo[]bar</p>' );

	var html = tests.getHtmlWithSelection();

	assert.areSame( '<p>foo[]bar</p>', html, 'html with selection' );
} );

test( 'get non-collapsed selection', function() {
	tests.setHtmlWithSelection( '<h1>[foo</h1><p>bar]</p>' );

	var html = tests.getHtmlWithSelection();

	assert.areSame( '<h1>[foo</h1><p>bar]</p>', html, 'html with selection' );
} );

test( 'encodeBogus', function() {
	assert.areSame( 'a', tests.encodeBogus( 'a' ), 'no @' );
	assert.areNotSame( 'a@b@', tests.encodeBogus( 'a@b@' ), '2 @' );
} )