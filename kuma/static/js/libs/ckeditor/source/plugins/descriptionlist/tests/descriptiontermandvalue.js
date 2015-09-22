'use strict';

suite( 'Description term - switch to dt' );

test( 'on a single dd', function() {
	tests.setHtmlWithSelection( '<dl><dd>x</dd><dd>[]foo</dd><dd>x</dd></dl>' );
	tests.editor.execCommand( 'descriptionTerm' );
	assert.areSame( '<dl><dd>x</dd><dt>[]foo</dt><dd>x</dd></dl>', tests.getHtmlWithSelection() );
} );

test( 'on a single dd with paragraphs inside', function() {
	tests.setHtmlWithSelection( '<dl><dd><p>[foo</p><p>bar]</p></dd></dl>' );
	tests.editor.execCommand( 'descriptionTerm' );
	assert.areSame( '<dl><dt><p>[foo</p><p>bar]</p></dt></dl>', tests.getHtmlWithSelection() );
} );

test( 'on two dd', function() {
	tests.setHtmlWithSelection( '<dl><dd>x</dd><dd>[foo</dd><dd>bar]</dd><dd>x</dd></dl>' );
	tests.editor.execCommand( 'descriptionTerm' );
	assert.areSame( '<dl><dd>x</dd><dt>[foo</dt><dt>bar]</dt><dd>x</dd></dl>', tests.getHtmlWithSelection() );
} );

test( 'on alternating dd and dt', function() {
	tests.setHtmlWithSelection( '<dl><dd>[foo</dd><dt>bar</dt><dd>bom]</dd></dl>' );
	tests.editor.execCommand( 'descriptionTerm' );
	assert.areSame( '<dl><dt>[foo</dt><dt>bar</dt><dt>bom]</dt></dl>', tests.getHtmlWithSelection() );
} );

suite( 'Description term - switch to dd' );

test( 'on a single dt', function() {
	tests.setHtmlWithSelection( '<dl><dt>x</dt><dt>[]foo</dt><dt>x</dt></dl>' );
	tests.editor.execCommand( 'descriptionTerm' );
	assert.areSame( '<dl><dt>x</dt><dd>[]foo</dd><dt>x</dt></dl>', tests.getHtmlWithSelection() );
} );

test( 'on alternating dd and dt', function() {
	tests.setHtmlWithSelection( '<dl><dt>[foo</dt><dd>bar</dd><dt>bom]</dt></dl>' );
	tests.editor.execCommand( 'descriptionTerm' );
	assert.areSame( '<dl><dd>[foo</dd><dd>bar</dd><dd>bom]</dd></dl>', tests.getHtmlWithSelection() );
} );

suite( 'Description value - switch to dd' );

test( 'on a single dt', function() {
	tests.setHtmlWithSelection( '<dl><dt>x</dt><dt>[]foo</dt><dt>x</dt></dl>' );
	tests.editor.execCommand( 'descriptionValue' );
	assert.areSame( '<dl><dt>x</dt><dd>[]foo</dd><dt>x</dt></dl>', tests.getHtmlWithSelection() );
} );

suite( 'Description value - switch to dt' );

test( 'on a single dd', function() {
	tests.setHtmlWithSelection( '<dl><dd>x</dd><dd>[]foo</dd><dd>x</dd></dl>' );
	tests.editor.execCommand( 'descriptionValue' );
	assert.areSame( '<dl><dd>x</dd><dt>[]foo</dt><dd>x</dd></dl>', tests.getHtmlWithSelection() );
} );