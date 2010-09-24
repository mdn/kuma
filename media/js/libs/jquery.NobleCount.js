/******************************************************************************************************

	jQuery.NobleCount

	Author Jeremy Horn
	Version 1.0
	Date: 3/21/2010

	Copyright (c) 2010 Jeremy Horn- jeremydhorn(at)gmail(dot)c0m | http://tpgblog.com
	Dual licensed under MIT and GPL.

	DESCRIPTION
		NobleCount... for a more 'proper' count of the characters remaining.
		
		NobleCount is a customizable jQuery plugin for a more the improved counting of the remaining 
		characters, and resulting behaviors, of a text entry object, e.g. input textfield, textarea.

		As text is entered into the target text area an object for the purposes of tracking
		the total number of characters remaining, defined as the maximum number of characters
		minus the current total number of characters within the text entry object, and storing
		that information visually and/or within the DOM as an HTML 5 compliant data-* attribute.
		
		Events and CSS Class alterations, if defined, are triggered based on current user 
		interaction with the target text entry object as well as the current state (positive or 
		negative) of the character remaining value.

		NobleCount supports pre-existing text within the text object.
		NobleCount supports jQuery chaining.

		Within NobleCount context...
			NEGATIVE is defined as Integers < 0
			POSITIVE is defined as Integers >= 0		[on_positive will fire when char_rem == 0]

		BY DEFAULT
		 - maximum characters EQUAL 140 characters
		 - no events defined
		 - no class changes defined
		 - no DOM attributes are created/altered
		 - user permitted to type past the maximum number of characters limit, resulting in
		   negative number of characters remaining
	
	IMPLEMENTATION

		$('#textarea1').NobleCount('#characters_remaining1');
		$('#textfield2').NobleCount('#characters_remaining2', { / * OPTIONS * / });
		
	COMPATIBILITY

		Tested in FF3.5, IE7
		With jQuery 1.3.x, 1.4.x

	METHOD(S)
		To properly intialize, both the text entry object and the object that will store the
		total number of characters remaining must exist and be passed to NobleCount.
		
			$(TEXT_ENTRY_OBJECT).NobleCount(CHARACTERS_REMAINING_OBJECT);
		
		Any callback functions assigned to any of the availale events are passed the following
		parameters: t_obj, char_area, c_settings, char_rem
		
			t_obj			text entry object
			
			char_area		selection of the characters remaining object
			
			c_settings		result of the options passed into NobleCount at time of 
							initialization merged with the default options
							
							** this is a GREAT way to pass in and remember other state
							information that will be needed upon the triggering of
							NobleCount events **
			
			char_rem		integer representation of the total number of characters
							remaining resulting from the calculated difference between
							the target maximum number of characters and the current
							number of characters currently within t_obj
		
		Both TEXT_ENTRY_OBJECT and CHARACTERS_REMAINING_OBJECT must be specified and valid.
		
		Upon successful initialization, all appropriate events and classes are applied to
		the CHARACTERS_REMAINING_OBJECT, including the storage (if not disabled) visually
		or only in the DOM (if enabled) of the integer representing the number of characters
		remaining.
		
		The target maximum number of characters (max_chars) are determined by the following 
		precedence rules....
		
				if max_chars passed via constructor
					max_chars = max_chars passed
				else if number exists within characters_remaining object and number > 0
					max_chars = number within the text() of characters_remaining object
				else use the NobleCount's default max_chars
		
	CUSTOMIZATION

		NobleCount(c_obj, <OPTIONS>)
		e.g. $(t_obj).NobleCount(c_obj, {max_chars:100px});


		on_negative				class (STRING) or FUNCTION that is applied/called 
								when characters remaining is negative IF DEFINED
									
		on_positive				class (STRING) or FUNCTION that is applied/called 
								when characters remaining is positive IF DEFINED
									
		on_update				FUNCTION that is called when characters remaining changes
								
		max_chars				target maximum number of characters
		
		block_negative			if TRUE, then all attempts are made to block entering 
									more than max_characters; not effective against user
									pasting in blocks of text that exceed the max_chars value
								otherwise, text area will let individual entering the text
									to exceed max_chars limit (characters remaining becomes
									negative)
								
		cloak: false,			if TRUE, then no visual updates of characters remaining 
									object (c_obj) will occur; this does not have any effect
									on the char_rem value returned via any event callbacks
								otherwise, the text within c_obj is constantly updated to
									represent the total number of characters remaining until
									the max_chars limit has been reached
								  
		in_dom: false			if TRUE and cloak is ALSO TRUE, then the number of characters
									remaining are stored as the attribute of c_obj
									named 'data-noblecount'
									
									!NOTE: if enabled, due to constant updating of a DOM element
										attribute user experience can appear sluggish while
										the individual is modifying the text entry object (t_obj)
								

		EXAMPLE	OPTIONS = 
			{
				on_negative: 'go_red',
				on_positive: 'go_green',
				max_chars: 25,
				on_update: function(t_obj, char_area, c_settings, char_rem){
					if ((char_rem % 10) == 0) {
						char_area.css('font-weight', 'bold');
						char_area.css('font-size', '300%');
					} else {
						char_area.css('font-weight', 'normal');
						char_area.css('font-size', '100%');
					}
				}
			};

	MORE

		For more details about NobleCount, its implementation, usage, and examples, go to:
		http://tpgblog.com/noblecount/

******************************************************************************************************/

(function($) {

	/**********************************************************************************

		FUNCTION
			NobleCount

		DESCRIPTION
			NobleCount method constructor
			
			allows for customization of maximum length and related update/length
			behaviors
			
				e.g. $(text_obj).NobleCount(characters_remaining_obj);

			REQUIRED: c_obj
			OPTIONAL: options

	**********************************************************************************/

	$.fn.NobleCount = function(c_obj, options) {
		var c_settings;
		var mc_passed = false;

		// if c_obj is not specified, then nothing to do here
		if (typeof c_obj == 'string') {
			// check for new & valid options
			c_settings = $.extend({}, $.fn.NobleCount.settings, options);

			// was max_chars passed via options parameter? 
			if (typeof options != 'undefined') {
				mc_passed = ((typeof options.max_chars == 'number') ? true : false);
			}

			// process all provided objects
			return this.each(function(){
				var $this = $(this);

				// attach events to c_obj
				attach_nobility($this, c_obj, c_settings, mc_passed);
			});
		}
		
		return this;
	};


	/**********************************************************************************

		FUNCTION
			NobleCount.settings

		DESCRIPTION
			publically accessible data stucture containing the max_chars and 
			event handling specifications for NobleCount
			
			can be directly accessed by	'$.fn.NobleCount.settings = ... ;'

	**********************************************************************************/
	$.fn.NobleCount.settings = {

		on_negative: null,		// class (STRING) or FUNCTION that is applied/called 
								// 		when characters remaining is negative
		on_positive: null,		// class (STRING) or FUNCTION that is applied/called 
								// 		when characters remaining is positive
		on_update: null,		// FUNCTION that is called when characters remaining 
								// 		changes
		max_chars: 140,			// maximum number of characters
		block_negative: false,  // if true, then all attempts are made to block entering 
								//		more than max_characters
		cloak: false,			// if true, then no visual updates of characters 
								// 		remaining (c_obj) occur
		in_dom: false			// if true and cloak == true, then number of characters
								//		remaining are stored as the attribute
								//		'data-noblecount' of c_obj
				
	};


	//////////////////////////////////////////////////////////////////////////////////

	// private functions and settings

	/**********************************************************************************

		FUNCTION
			attach_nobility
	
		DESCRIPTION
			performs all initialization routines and display initiation
			
			assigns both the keyup and keydown events to the target text entry
			object; both keyup and keydown are used to provide the smoothest
			user experience
	
				if max_chars_passed via constructor
					max_chars = max_chars_passed
				else if number exists within counting_object (and number > 0)
					max_chars = counting_object.number
				else use default max_chars
	
		PRE
			t_obj and c_obj EXIST
			c_settings and mc_passed initialized
			
		POST
			maximum number of characters for t_obj calculated and stored in max_char
			key events attached to t_obj
	
	**********************************************************************************/

	function attach_nobility(t_obj, c_obj, c_settings, mc_passed){
		var max_char 	= c_settings.max_chars;
		var char_area	= $(c_obj);

		// first determine if max_char needs adjustment
		if (!mc_passed) {
			var tmp_num = char_area.text();
			var isPosNumber = (/^[1-9]\d*$/).test(tmp_num);

			if (isPosNumber) {
				max_char = tmp_num;
			}
		}

		// initialize display of characters remaining
		// * note: initializing should not trigger on_update
		event_internals(t_obj, char_area, c_settings, max_char, true);

		// then attach the events -- seem to work better than keypress
		$(t_obj).keydown(function(e) {
			event_internals(t_obj, char_area, c_settings, max_char, false);

			// to block text entry, return false
			if (check_block_negative(e, t_obj, c_settings, max_char) == false) {
				return false;
			} 
		});

		$(t_obj).keyup(function(e) {
			event_internals(t_obj, char_area, c_settings, max_char, false);
			
			// to block text entry, return false
			if (check_block_negative(e, t_obj, c_settings, max_char) == false) {
				return false;
			} 
		});
	}


	/**********************************************************************************

		FUNCTION
			check_block_negative
	
		DESCRIPTION
			determines whether or not text entry within t_obj should be prevented
			
		PRE
			e EXISTS
			t_obj VALID
			c_settings and max_char initialized / calculated
			
		POST
			if t_obj text entry should be prevented FALSE is returned
				otherwise TRUE returned
	
		TODO
			improve selection detection and permissible behaviors experience
			ALSO
				doesnt CURRENTLY block from the pasting of large chunks of text that 
				exceed max_char
		
	**********************************************************************************/

	function check_block_negative(e, t_obj, c_settings, max_char){
		if (c_settings.block_negative) {
			var char_code = e.which;
			var selected;

			// goofy handling required to work in both IE and FF
			if (typeof document.selection != 'undefined') {
				selected = (document.selection.createRange().text.length > 0);
			} else {
				selected = (t_obj[0].selectionStart != t_obj[0].selectionEnd);
			}

			//return false if can't write more  
			if ((!((find_remaining(t_obj, max_char) < 1) &&
				(char_code > 47 || char_code == 32 || char_code == 0 || char_code == 13) &&
				!e.ctrlKey &&
				!e.altKey &&
				!selected)) == false) {
				
				// block text entry
				return false;
			}
		}
		
		// allow text entry
		return true;
	}


	/**********************************************************************************

		FUNCTION
			find_remaining
	
		DESCRIPTION
			determines of the number of characters permitted (max_char), the number of 
			characters remaining until that limit has been reached  
	
		PRE
			t_obj and max_char EXIST and are VALID
			
		POST
			returns integer of the difference between max_char and total number of
			characters within the text entry object (t_obj)
	
	**********************************************************************************/

	function find_remaining(t_obj, max_char){
		return max_char - ($(t_obj).val()).length;
	}


	/**********************************************************************************

		FUNCTION
			event_internals
	
		DESCRIPTION
			primarily used for the calculation of appropriate behavior resulting from
			any event attached to the text entry object (t_obj)
	
			whenever the char_rem and related display and/or DOM information needs
			updating this function is called

			if cloaking is being used, then no visual representation of the characters
			remaining, nor attempt by this plugin to change any of its visual 
			characteristics will occur
			
			if cloaking and in_dom are both TRUE, then the number of characters 
			remaining are stored within the HTML 5 compliant attribute of the
			character count remaining object (c_obj) labeled 'data-noblecount'
			
		PRE
			c_settings, init_disp initialized
			
		POST
			performs all updates to the DOM visual and otherwise required
			performs all relevant function calls
	
	**********************************************************************************/

	function event_internals(t_obj, char_area, c_settings, max_char, init_disp) {
		var char_rem	= find_remaining(t_obj, max_char);

		// is chararacters remaining positive or negative
		if (char_rem < 0) {
			toggle_states(c_settings.on_negative, c_settings.on_positive, t_obj, char_area, c_settings, char_rem);
		} else {
			toggle_states(c_settings.on_positive, c_settings.on_negative, t_obj, char_area, c_settings, char_rem);
		}
	
		// determine whether or not to update the text of the char_area (or c_obj)
		if (c_settings.cloak) {
			// this slows stuff down quite a bit; TODO: implement better method of publically accessible data storage
			if (c_settings.in_dom) {
				char_area.attr('data-noblecount', char_rem);
			}
		} else {
			// show the numbers of characters remaining 
			char_area.text(char_rem);
		}

		// if event_internals isn't being called for initialization purposes and
		// on_update is a properly defined function then call it on this update
		if (!init_disp && jQuery.isFunction(c_settings.on_update)) {
			c_settings.on_update(t_obj, char_area, c_settings, char_rem);
		} 
	}


	/**********************************************************************************

		FUNCTION
			toggle_states
	
		DESCRIPTION
			performs the toggling operations between the watched positive and negative
			characteristics
			
			first, enables/triggers/executes the toggle_on behavior/class
			second, disables the trigger_off class
	
		PRE
			toggle_on, toggle_off
				IF DEFINED, 
					must be a string representation of a VALID class
					OR
					must be a VALID function 
			
		POST
			toggle_on objects have been applied/executed
			toggle_off class has been removed (if it is a class)
	
	**********************************************************************************/

	function toggle_states(toggle_on, toggle_off, t_obj, char_area, c_settings, char_rem){
		if (toggle_on != null) {
			if (typeof toggle_on == 'string') {
				char_area.addClass(toggle_on);				
			} else if (jQuery.isFunction(toggle_on)) {
				toggle_on(t_obj, char_area, c_settings, char_rem);
			}
		}
		
		if (toggle_off != null) {
			if (typeof toggle_off == 'string') {
				char_area.removeClass(toggle_off);				
			}
		}		
	}
})(jQuery);
