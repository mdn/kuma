( function() {
	'use strict';

	function create( editor ) {
		if ( !editor ) {
			editor = tests.editor;
		}

		return CKEDITOR.plugins.descriptionList.createListContainer(
			editor, editor.document.getById( 'b' )
		);
	}

	suite( 'createListContainer' );

	test( 'single paragraph', function() {
		tests.editor.editable().setHtml( '<p id="b">foo</p>' );

		var dl = create();

		assert.areSame( 'dl', dl.getName() );
		assert.areSame( '<dl></dl>', tests.editor.getData() );
	} );

	test( 'paragraph between paragraphs', function() {
		tests.editor.editable().setHtml( '<p>x</p><p id="b">foo</p><p>y</p>' );
		create();
		assert.areSame( '<p>x</p><dl></dl><p>y</p>', tests.editor.getData() );
	} );

	test( 'list item', function() {
		tests.editor.editable().setHtml( '<p>x</p><ul><li id="b">foo</li></ul><p>y</p>' );
		create();
		assert.areSame( '<p>x</p><dl></dl><p>y</p>', tests.editor.getData() );
	} );

	test( 'paragraph inside list item', function() {
		tests.editor.editable().setHtml( '<p>x</p><ul><li><p id="b">foo</p></li></ul><p>y</p>' );
		create();
		assert.areSame( '<p>x</p><dl></dl><p>y</p>', tests.editor.getData() );
	} );


	test( 'paragraph inside list item between list items', function() {
		tests.editor.editable().setHtml( '<ul><li>x</li><li><p id="b">foo</p></li><li>y</li></ul>' );
		create();
		assert.areSame( '<ul><li>x</li></ul><dl></dl><ul><li>y</li></ul>', tests.editor.getData() );
	} );

	test( 'paragraph inside list item at the beginning of the list', function() {
		tests.editor.editable().setHtml( '<p>x</p><ul><li id="b">foo</li><li>bar</li></ul><p>y</p>' );
		create();
		assert.areSame( '<p>x</p><dl></dl><ul><li>bar</li></ul><p>y</p>', tests.editor.getData() );
	} );

	test( 'paragraph inside list item at the end of the list', function() {
		tests.editor.editable().setHtml( '<p>x</p><ul><li>bar</li><li id="b">foo</li></ul><p>y</p>' );
		create();
		assert.areSame( '<p>x</p><ul><li>bar</li></ul><dl></dl><p>y</p>', tests.editor.getData() );
	} );

	test( 'paragraph inside list item in the middle of the list', function() {
		tests.editor.editable().setHtml( '<p>x</p><ul><li>bar</li><li id="b">foo</li><li>bom</li></ul><p>y</p>' );
		create();
		assert.areSame( '<p>x</p><ul><li>bar</li></ul><dl></dl><ul><li>bom</li></ul><p>y</p>',tests.editor.getData() );
	} );

} )();