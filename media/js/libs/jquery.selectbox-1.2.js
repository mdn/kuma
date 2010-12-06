/*
 * jQuery selectbox plugin
 *
 * Copyright (c) 2007 Sadri Sahraoui (brainfault.com)
 * Licensed under the GPL license and MIT:
 *   http://www.opensource.org/licenses/GPL-license.php
 *   http://www.opensource.org/licenses/mit-license.php
 *
 * The code is inspired from Autocomplete plugin (http://www.dyve.net/jquery/?autocomplete)
 *
 * Revision: $Id$
 * Version: 1.2
 * 
 * Changelog :
 *  Version 1.2 By Guillaume Vergnolle (web-opensource.com)
 *  - Add optgroup support
 *  - possibility to choose between span or input as replacement of the select box
 *  - support for jquery change event
 *  - add a max height option for drop down list
 *  Version 1.1 
 *  - Fix IE bug
 *  Version 1.0
 *  - Support jQuery noConflict option
 *  - Add callback for onChange event, thanks to Jason
 *  - Fix IE8 support
 *  - Fix auto width support
 *  - Fix focus on firefox dont show the carret
 *  Version 0.6
 *  - Fix IE scrolling problem
 *  Version 0.5 
 *  - separate css style for current selected element and hover element which solve the highlight issue 
 *  Version 0.4
 *  - Fix width when the select is in a hidden div   @Pawel Maziarz
 *  - Add a unique id for generated li to avoid conflict with other selects and empty values @Pawel Maziarz
 */
jQuery.fn.extend({
	selectbox: function(options) {
		return this.each(function() {
			new jQuery.SelectBox(this, options);
		});
	}
});


/* pawel maziarz: work around for ie logging */
if (!window.console) {
	var console = {
		log: function(msg) { 
	 	}
	}
}
/* */

jQuery.SelectBox = function(selectobj, options) {
	
	var opt = options || {};
	opt.inputType = opt.inputType || "input";
	opt.inputClass = opt.inputClass || "selectbox";
	opt.containerClass = opt.containerClass || "selectbox-wrapper";
	opt.hoverClass = opt.hoverClass || "current";
	opt.currentClass = opt.currentClass || "selected";
	opt.groupClass = opt.groupClass || "groupname"; //css class for group
	opt.maxHeight = opt.maxHeight || 200; // max height of dropdown list
	opt.loopnoStep = opt.loopnoStep || false; // to remove the step in list moves loop
	opt.onChangeCallback = opt.onChangeCallback || false;
	opt.onChangeParams = opt.onChangeParams || false;
	opt.debug = opt.debug || false;
	
	var elm_id = selectobj.id;
	var active = 0;
	var inFocus = false;
	var hasfocus = 0;
	//jquery object for select element
	var $select = jQuery(selectobj);
	// jquery container object
	var $container = setupContainer(opt);
	//jquery input object 
	var $input = setupInput(opt);
	// hide select and append newly created elements
	$select.hide().before($input).before($container);
	
	
	init();
	
	$input
	.click(function(){
		if (!inFocus) {
			$container.toggle();
		}
	})
	.focus(function(){
		if ($container.not(':visible')) {
			inFocus = true;
			$container.show();
		}
	})
	.keydown(function(event) {	   
		switch(event.keyCode) {
			case 38: // up
				event.preventDefault();
				moveSelect(-1);
				break;
			case 40: // down
				event.preventDefault();
				moveSelect(1);
				break;
			//case 9:  // tab 
			case 13: // return
				event.preventDefault(); // seems not working in mac !
				$('li.'+opt.hoverClass).trigger('click');
				break;
			case 27: //escape
			  hideMe();
			  break;
		}
	})
	.blur(function() {
		if ($container.is(':visible') && hasfocus > 0 ) {
			if(opt.debug) console.log('container visible and has focus')
		} else {
			// Workaround for ie scroll - thanks to Bernd Matzner
			if((jQuery.browser.msie && jQuery.browser.version.substr(0,1) < 8) /* Note(rlr): This is causing error in Safari (doesn't implement activeElement) and works fine without it. -> || jQuery.browser.safari*/){
				if(document.activeElement.getAttribute('id').indexOf('_container')==-1){
					hideMe();
				} else {
					$input.focus();
				}
			} else {
				hideMe();
			}
		}
	});

	function hideMe() { 
		hasfocus = 0;
		$container.hide(); 
	}
	
	function init() {
		$container.append(getSelectOptions($input.attr('id'))).hide();
		var width = $input.css('width');
		if($container.height() > opt.maxHeight){
			//rlr $container.width(parseInt(width)+parseInt($input.css('paddingRight'))+parseInt($input.css('paddingLeft')));
			$container.height(opt.maxHeight);
		} //rlr else $container.width(width);
	}
	
	function setupContainer(options) {
		var container = document.createElement("div");
		$container = jQuery(container);
		$container.attr('id', elm_id+'_container');
		$container.addClass(options.containerClass);
        	$container.css('display', 'none');
		
		return $container;
	}
	
	function setupInput(options) {
		if(opt.inputType == "span"){
			var input = document.createElement("span");
			var $input = jQuery(input);
			$input.attr("id", elm_id+"_input");
			$input.addClass(options.inputClass);
			$input.attr("tabIndex", $select.attr("tabindex"));
		} else {
			var input = document.createElement("input");
			var $input = jQuery(input);
			$input.attr("id", elm_id+"_input");
			$input.attr("type", "text");
			$input.addClass(options.inputClass);
			$input.attr("autocomplete", "off");
			$input.attr("readonly", "readonly");
			$input.attr("tabIndex", $select.attr("tabindex")); // "I" capital is important for ie
			$input.css("width", $select.css("width"));
        	}
		return $input;	
	}
	
	function moveSelect(step) {
		var lis = jQuery("li", $container);
		if (!lis || lis.length == 0) return false;
		// find the first non-group (first option)
		firstchoice = 0;
		while($(lis[firstchoice]).hasClass(opt.groupClass)) firstchoice++;
		active += step;
    		// if we are on a group step one more time
    		if($(lis[active]).hasClass(opt.groupClass)) active += step;
		//loop through list from the first possible option
		if (active < firstchoice) {
			(opt.loopnoStep ? active = lis.size()-1 : active = lis.size() );
		} else if (opt.loopnoStep && active > lis.size()-1) {
			active = firstchoice;
		} else if (active > lis.size()) {
			active = firstchoice;
		}
        	scroll(lis, active);
		lis.removeClass(opt.hoverClass);

		jQuery(lis[active]).addClass(opt.hoverClass);
	}
	
	function scroll(list, active) {
      		var el = jQuery(list[active]).get(0);
      		var list = $container.get(0);
      
		if (el.offsetTop + el.offsetHeight > list.scrollTop + list.clientHeight) {
			list.scrollTop = el.offsetTop + el.offsetHeight - list.clientHeight;      
		} else if(el.offsetTop < list.scrollTop) {
			list.scrollTop = el.offsetTop;
		}
	}
	
	function setCurrent() {	
		var li = jQuery("li."+opt.currentClass, $container).get(0);
		var ar = (''+li.id).split('_');
		var el = ar[ar.length-1];
		if (opt.onChangeCallback){
        		$select.get(0).selectedIndex = $('li', $container).index(li);
        		opt.onChangeParams = { selectedVal : $select.val() };
			opt.onChangeCallback(opt.onChangeParams);
		} else {
			$select.val(el);
			$select.change();
		}
		if(opt.inputType == 'span') $input.html($(li).html());
		else $input.val($(li).html());
		return true;
	}
	
	// select value
	function getCurrentSelected() {
		return $select.val();
	}
	
	// input value
	function getCurrentValue() {
		return $input.val();
	}
	
	function getSelectOptions(parentid) {
		var select_options = new Array();
		var ul = document.createElement('ul');
		select_options = $select.find('option'); //rlr $select.children('option');
		if(select_options.length == 0) {
			var select_optgroups = new Array();
			select_optgroups = $select.children('optgroup');
			for(x=0;x<select_optgroups.length;x++){
				select_options = $("#"+select_optgroups[x].id).children('option');
				var li = document.createElement('li');
				li.setAttribute('id', parentid + '_' + $(this).val());
				li.innerHTML = $("#"+select_optgroups[x].id).attr('label');
				li.className = opt.groupClass;
				ul.appendChild(li);
				select_options.each(function() {
					var li = document.createElement('li');
					li.setAttribute('id', parentid + '_' + $(this).val());
					li.innerHTML = $(this).html();
					if ($(this).is(':selected')) {
						$input.html($(this).html());
						$(li).addClass(opt.currentClass);
					}
					ul.appendChild(li);
					$(li)
					.mouseover(function(event) {
						hasfocus = 1;
						if (opt.debug) console.log('over on : '+this.id);
						jQuery(event.target, $container).addClass(opt.hoverClass);
					})
					.mouseout(function(event) {
						hasfocus = -1;
						if (opt.debug) console.log('out on : '+this.id);
						jQuery(event.target, $container).removeClass(opt.hoverClass);
					})
					.click(function(event) {
						var fl = $('li.'+opt.hoverClass, $container).get(0);
						if (opt.debug) console.log('click on :'+this.id);
						$('li.'+opt.currentClass, $container).removeClass(opt.currentClass); 
						$(this).addClass(opt.currentClass);
						setCurrent();
						$select.get(0).blur();
						hideMe();
					});
				});
			}
		} else select_options.each(function() {
			var li = document.createElement('li');
			li.setAttribute('id', parentid + '_' + $(this).val());
			li.innerHTML = $(this).html();
			if ($(this).is(':selected')) {
				$input.val($(this).html());
				$(li).addClass(opt.currentClass);
			}
			ul.appendChild(li);
			$(li)
			.mouseover(function(event) {
				hasfocus = 1;
				if (opt.debug) console.log('over on : '+this.id);
				jQuery(event.target, $container).addClass(opt.hoverClass);
			})
			.mouseout(function(event) {
				hasfocus = -1;
				if (opt.debug) console.log('out on : '+this.id);
				jQuery(event.target, $container).removeClass(opt.hoverClass);
			})
			.click(function(event) {
			  	var fl = $('li.'+opt.hoverClass, $container).get(0);
				if (opt.debug) console.log('click on :'+this.id);
				$('li.'+opt.currentClass, $container).removeClass(opt.currentClass); 
				$(this).addClass(opt.currentClass);
				setCurrent();
				$select.get(0).blur();
				hideMe();
			});
		});
		return ul;
	}
	
	
	
};
