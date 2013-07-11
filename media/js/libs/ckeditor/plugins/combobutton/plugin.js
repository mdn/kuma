/*
Copyright (c) 2003-2010, CKSource - Frederico Knabben. All rights reserved.
For licensing, see LICENSE.html or http://ckeditor.com/license
*/

CKEDITOR.plugins.add( 'combobutton',
{
	requires : [ 'richcombo' ],

	onLoad : function()
	{
		CKEDITOR.ui.comboButton = CKEDITOR.tools.createClass(
		{
			base : CKEDITOR.ui.richCombo,

			$ : function( definition )
			{
				this.base( definition );
			},

			statics :
			{
				handler :
				{
					create : function( definition )
					{
						return new CKEDITOR.ui.comboButton( definition );
					}
				}
			},

			proto :
			{
				canGroup : true,

				onClose : function()
				{
					this.setState( this._.previousState );
				},

				render : function( editor, output )
				{
					var env = CKEDITOR.env;

					var id = 'cke_' + this.id;
					var clickFn = CKEDITOR.tools.addFunction( function( $element )
						{
							var _ = this._;

							if ( _.state == CKEDITOR.TRISTATE_DISABLED )
								return;

							if ( !_.on )
							{
								_.previousState = _.state;
							}

							this.createPanel( editor );

							if ( _.on )
							{
								_.panel.hide();
								return;
							}

							this.commit();

							var value = this.getValue();
							if ( value )
								_.list.mark( value );
							else
								_.list.unmarkAll();

							_.panel.showBlock( this.id, new CKEDITOR.dom.element( $element ), 4 );
						},
						this );

					var instance = {
						id : id,
						combo : this,
						focus : function()
						{
							var element = CKEDITOR.document.getById( id );
							element.focus();
						},
						clickFn : clickFn
					};

					editor.on( 'mode', function()
						{
							this.setState( this.modes[ editor.mode ] ? CKEDITOR.TRISTATE_OFF : CKEDITOR.TRISTATE_DISABLED );
							this.setValue( '' );
						},
						this );

					var keyDownFn = CKEDITOR.tools.addFunction( function( ev, element )
						{
							ev = new CKEDITOR.dom.event( ev );

							var keystroke = ev.getKeystroke();
							switch ( keystroke )
							{
								case 13 :	// ENTER
								case 32 :	// SPACE
								case 40 :	// ARROW-DOWN
									// Show panel
									CKEDITOR.tools.callFunction( clickFn, element );
									break;
								default :
									// Delegate the default behavior to toolbar button key handling.
									instance.onkey( instance,  keystroke );
							}

							// Avoid subsequent focus grab on editor document.
							ev.preventDefault();
						});

					// For clean up
					instance.keyDownFn = keyDownFn;

					var classes = '';

					if ( this.className )
						classes += this.className;

					classes += ' cke_off';

					output.push(
						'<span class="cke_button' + ( this.icon && this.icon.indexOf( '.png' ) == -1 ? ' cke_noalphafix' : '' ) + '">',
						'<a id="', id, '"' +
							' class="', classes, '"',
							env.gecko && env.version >= 10900 && !env.hc  ? '' : '" href="javascript:void(\'' + ( this.title || '' ).replace( "'", '' ) + '\')"',
							' title="', this.title, '"' +
							' tabindex="-1"' +
							' hidefocus="true"' +
							' role="button"' +
							' aria-labelledby="' + id + '_label"' +
							' aria-haspopup="true"' );

					// Some browsers don't cancel key events in the keydown but in the
					// keypress.
					// TODO: Check if really needed for Gecko+Mac.
					if ( env.opera || ( env.gecko && env.mac ) )
					{
						output.push(
							' onkeypress="return false;"' );
					}

					// With Firefox, we need to force the button to redraw, otherwise it
					// will remain in the focus state.
					if ( env.gecko )
					{
						output.push(
							' onblur="this.style.cssText = this.style.cssText;"' );
					}

					output.push(
							' onkeydown="CKEDITOR.tools.callFunction( ', keyDownFn, ', event, this );"' +
		//					' onfocus="return CKEDITOR.ui.button._.focus(', index, ', event);"' +
							' onclick="CKEDITOR.tools.callFunction(', clickFn, ', this); return false;">' +
								'<span class="cke_icon"' );

					if ( this.icon )
					{
						var offset = ( this.iconOffset || 0 ) * -16;
						output.push( ' style="background-image:url(', CKEDITOR.getUrl( this.icon ), ');background-position:0 ' + offset + 'px;"' );
					}

					output.push(
								'>&nbsp;</span>' +
								'<span id="', id, '_label" class="cke_label">', this.label, '</span>' );

					output.push(
							'<span class="cke_buttonarrow">'
							// BLACK DOWN-POINTING TRIANGLE
							+ ( CKEDITOR.env.hc ? '&#9660;' : '&nbsp;' )
							+ '</span>' );

					output.push(
						'</a>',
						'</span>' );

					if ( this.onRender )
						this.onRender();

					return instance;
				},

				setValue : function( value, text )
				{
					this._.value = value;
				}
			}
		} );
	},

	init : function( editor )
	{
		editor.ui.addHandler( CKEDITOR.UI_COMBOBUTTON, CKEDITOR.ui.comboButton.handler );
	}
});

/**
 * UI element.
 * @constant
 * @example
 */
CKEDITOR.UI_COMBOBUTTON = 92;


CKEDITOR.ui.prototype.addComboButton = function( name, definition )
{
	this.add( name, CKEDITOR.UI_COMBOBUTTON, definition );
};
