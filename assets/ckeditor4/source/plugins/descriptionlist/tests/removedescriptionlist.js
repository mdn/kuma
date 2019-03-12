'use strict';

suite( 'Description list - removing from a single list' );

test( 'on a list with single dt', function() {
	tests.setHtmlWithSelection( '<dl><dt>[]foo</dt></dl>' );
	tests.editor.execCommand( 'descriptionList' );
	assert.areSame( '<p>[]foo</p>', tests.getHtmlWithSelection() );
} );

test( 'on a list with single dd', function() {
	tests.setHtmlWithSelection( '<dl><dd>[]foo</dd></dl>' );
	tests.editor.execCommand( 'descriptionList' );
	assert.areSame( '<p>[]foo</p>', tests.getHtmlWithSelection() );
} );

test( 'on a dd preceded by dt', function() {
	tests.setHtmlWithSelection( '<dl><dt>x</dt><dd>[]foo</dd></dl>' );
	tests.editor.execCommand( 'descriptionList' );
	assert.areSame( '<dl><dt>x</dt></dl><p>[]foo</p>', tests.getHtmlWithSelection() );
} );

test( 'between items', function() {
	tests.setHtmlWithSelection( '<dl><dt>x</dt><dd>[]foo</dd><dt>y</dt></dl>' );
	tests.editor.execCommand( 'descriptionList' );
	assert.areSame( '<dl><dt>x</dt></dl><p>[]foo</p><dl><dt>y</dt></dl>', tests.getHtmlWithSelection() );
} );

test( 'on a multi-item list', function() {
	tests.setHtmlWithSelection( '<dl><dt>[x</dt><dd>foo</dd><dt>y]</dt></dl>' );
	tests.editor.execCommand( 'descriptionList' );
	assert.areSame( '<p>[x</p><p>foo</p><p>y]</p>', tests.getHtmlWithSelection() );
} );

test( 'on a part of multi-item list', function() {
	tests.setHtmlWithSelection( '<dl><dt>x</dt><dd>[foo</dd><dd>bar]</dd><dt>y</dt></dl>' );
	tests.editor.execCommand( 'descriptionList' );
	assert.areSame( '<dl><dt>x</dt></dl><p>[foo</p><p>bar]</p><dl><dt>y</dt></dl>', tests.getHtmlWithSelection() );
} );

test( 'on a selection ending outside of list', function() {
	tests.setHtmlWithSelection( '<dl><dt>x</dt><dd>[foo</dd></dl><p>y</p><ul><li>z]</li></ul>' );
	tests.editor.execCommand( 'descriptionList' );
	assert.areSame( '<dl><dt>x</dt></dl><p>[foo</p><p>y</p><ul><li>z]</li></ul>', tests.getHtmlWithSelection() );
} );

test( 'through an ordered list', function() {
	tests.setHtmlWithSelection( '<dl><dt>[x</dt></dl><ul class="foo"><li>a</li><li>b</li></ul><p>y]</p>' );
	tests.editor.execCommand( 'descriptionList' );
	assert.areSame( '<p>[x</p><ul class="foo"><li>a</li><li>b</li></ul><p>y]</p>', tests.getHtmlWithSelection() );
} );

test( 'on a selection starting ina single-item list ending outside the list', function() {
	tests.setHtmlWithSelection( '<p>x</p><dl><dt>foo[</dt></dl><p>y</p><p>bar]</p><p>z</p>' );
	tests.editor.execCommand( 'descriptionList' );
	assert.areSame( '<p>x</p><p>foo[</p><p>y</p><p>bar]</p><p>z</p>', tests.getHtmlWithSelection() );
} );

suite( 'Description list - removing from a multiple lists' );

test( 'start and end in different lists', function() {
	tests.setHtmlWithSelection( '<dl><dt>x</dt><dd>[foo</dd></dl><p>y</p><dl><dt>bar]</dt><dd>z</dd></dl>' );
	tests.editor.execCommand( 'descriptionList' );
	assert.areSame( '<dl><dt>x</dt></dl><p>[foo</p><p>y</p><p>bar]</p><dl><dd>z</dd></dl>', tests.getHtmlWithSelection() );
} );

test( 'start and end in different lists - full selection', function() {
	tests.setHtmlWithSelection( '<dl><dd>[foo</dd></dl><p>y</p><dl><dt>bar]</dt></dl>' );
	tests.editor.execCommand( 'descriptionList' );
	assert.areSame( '<p>[foo</p><p>y</p><p>bar]</p>', tests.getHtmlWithSelection() );
} );

test( 'two lists, ending in paragraph', function() {
	tests.setHtmlWithSelection( '<dl><dt>x</dt><dd>[foo</dd></dl><p>y</p><dl><dt>bar</dt></dl><p>z]</p>' );
	tests.editor.execCommand( 'descriptionList' );
	assert.areSame( '<dl><dt>x</dt></dl><p>[foo</p><p>y</p><p>bar</p><p>z]</p>', tests.getHtmlWithSelection() );
} );

suite( 'Description list - removing from list containing blocks' );

test( 'on a single item with h1 inside', function() {
	tests.setHtmlWithSelection( '<p>x</p><dl><dt><h1>[]foo</h1></dt><dd>bar</dd></dl><p>y</p>' );
	tests.editor.execCommand( 'descriptionList' );
	assert.areSame( '<p>x</p><h1>[]foo</h1><dl><dd>bar</dd></dl><p>y</p>', tests.getHtmlWithSelection() );
} );

test( 'on a list with multiple blocks inside', function() {
	tests.setHtmlWithSelection( '<dl><dt><h1>[foo</h1></dt><dd><p>b</p><p>c</p></dd><dd>bar]</dd></dl>' );
	tests.editor.execCommand( 'descriptionList' );
	assert.areSame( '<h1>[foo</h1><p>b</p><p>c</p><p>bar]</p>', tests.getHtmlWithSelection() );
} );

test( 'on selection contaning list with blocks', function() {
	tests.setHtmlWithSelection( '<dl><dt>[foo</dt></dl><p>x</p><dl><dd><h1>bar</h1></dd></dl><p>y]</p>' );
	tests.editor.execCommand( 'descriptionList' );
	assert.areSame( '<p>[foo</p><p>x</p><h1>bar</h1><p>y]</p>', tests.getHtmlWithSelection() );
} );

test( 'on a single item with three blocks inside - selection in middle one', function() {
	tests.setHtmlWithSelection( '<p>x</p><dl><dt><h1>foo</h1><h2>[]bar</h2><h3>bom</h3></dt></dl><p>y</p>' );
	tests.editor.execCommand( 'descriptionList' );
	assert.areSame( '<p>x</p><h1>foo</h1><h2>[]bar</h2><h3>bom</h3><p>y</p>', tests.getHtmlWithSelection() );
} );

test( 'on multiple, partially selected items with blocks', function() {
	tests.setHtmlWithSelection( '<dl><dt><h1>foo</h1><h2>[bar</h2></dt></dl><p>x</p><dl><dt><h3>bom]</h3><h4>baz</h4></dt></dl>' );
	tests.editor.execCommand( 'descriptionList' );
	assert.areSame( '<h1>foo</h1><h2>[bar</h2><p>x</p><h3>bom]</h3><h4>baz</h4>', tests.getHtmlWithSelection() );
} );