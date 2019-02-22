'use strict';

suite( 'Description list, term and value - states outside list' );

test( 'in a paragraph', function() {
	tests.setHtmlWithSelection( '<p>[]foo</p>' );
	assert.areSame( CKEDITOR.TRISTATE_OFF, tests.editor.getCommand( 'descriptionList' ).state, 'DL' );
	assert.areSame( CKEDITOR.TRISTATE_DISABLED, tests.editor.getCommand( 'descriptionTerm' ).state, 'DT' );
	assert.areSame( CKEDITOR.TRISTATE_DISABLED, tests.editor.getCommand( 'descriptionValue' ).state, 'DD' );
} );

test( 'in an ordered list', function() {
	tests.setHtmlWithSelection( '<ul><li>[]foo</li></ul>' );
	assert.areSame( CKEDITOR.TRISTATE_OFF, tests.editor.getCommand( 'descriptionList' ).state, 'DL' );
	assert.areSame( CKEDITOR.TRISTATE_DISABLED, tests.editor.getCommand( 'descriptionTerm' ).state, 'DT' );
	assert.areSame( CKEDITOR.TRISTATE_DISABLED, tests.editor.getCommand( 'descriptionValue' ).state, 'DD' );
} );

test( 'starting in paragraph, ending in description list', function() {
	tests.setHtmlWithSelection( '<p>[foo</p><dl><dt>foo]</dt></dl>' );
	assert.areSame( CKEDITOR.TRISTATE_OFF, tests.editor.getCommand( 'descriptionList' ).state, 'DL' );
	assert.areSame( CKEDITOR.TRISTATE_DISABLED, tests.editor.getCommand( 'descriptionTerm' ).state, 'DT' );
	assert.areSame( CKEDITOR.TRISTATE_DISABLED, tests.editor.getCommand( 'descriptionValue' ).state, 'DD' );
} );

test( 'starting at the end of paragraph, ending in description list', function() {
	tests.setHtmlWithSelection( '<p>foo[</p><dl><dt>foo]</dt></dl>' );
	assert.areSame( CKEDITOR.TRISTATE_OFF, tests.editor.getCommand( 'descriptionList' ).state, 'DL' );
	assert.areSame( CKEDITOR.TRISTATE_DISABLED, tests.editor.getCommand( 'descriptionTerm' ).state, 'DT' );
	assert.areSame( CKEDITOR.TRISTATE_DISABLED, tests.editor.getCommand( 'descriptionValue' ).state, 'DD' );
} );

suite( 'Description list - states (ON)' );

test( 'in a description term', function() {
	tests.setHtmlWithSelection( '<dl><dt>[]foo</dt></dl>' );
	assert.areSame( CKEDITOR.TRISTATE_ON, tests.editor.getCommand( 'descriptionList' ).state );
} );

test( 'in a description value', function() {
	tests.setHtmlWithSelection( '<dl><dd>[]foo</dd></dl>' );
	assert.areSame( CKEDITOR.TRISTATE_ON, tests.editor.getCommand( 'descriptionList' ).state );
} );

test( 'in a description list, ending in paragraph', function() {
	tests.setHtmlWithSelection( '<dl><dt>[foo</dt></dl><p>bar]</p>' );
	assert.areSame( CKEDITOR.TRISTATE_ON, tests.editor.getCommand( 'descriptionList' ).state );
} );

test( 'in a description list, inside an inline element', function() {
	tests.setHtmlWithSelection( '<dl><dt><strong>[]foo</strong></dt></dl>' );
	assert.areSame( CKEDITOR.TRISTATE_ON, tests.editor.getCommand( 'descriptionList' ).state );
} );

test( 'in a description value, inside a paragraph', function() {
	tests.setHtmlWithSelection( '<dl><dd><p>[]foo</p></dd></dl>' );
	assert.areSame( CKEDITOR.TRISTATE_ON, tests.editor.getCommand( 'descriptionList' ).state );
} );

suite( 'Description term and value - states (ON/OFF)' );

test( 'in a description term', function() {
	tests.setHtmlWithSelection( '<dl><dt>[]foo</dt></dl>' );
	assert.areSame( CKEDITOR.TRISTATE_ON, tests.editor.getCommand( 'descriptionTerm' ).state );
	assert.areSame( CKEDITOR.TRISTATE_OFF, tests.editor.getCommand( 'descriptionValue' ).state );
} );

test( 'in a description value', function() {
	tests.setHtmlWithSelection( '<dl><dd>[]foo</dd></dl>' );
	assert.areSame( CKEDITOR.TRISTATE_OFF, tests.editor.getCommand( 'descriptionTerm' ).state );
	assert.areSame( CKEDITOR.TRISTATE_ON, tests.editor.getCommand( 'descriptionValue' ).state );
} );