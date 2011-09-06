/**
 * jQuery gMap
 *
 * @url		http://gmap.nurtext.de/
 * @author	Cedric Kastner <cedric@nur-text.de>
 * @version	1.1.0
 */
(function($)
{
	// Main plugin function
	$.fn.gMap = function(options)
	{
		// Check if the browser is compatible
		if (!window.GBrowserIsCompatible || !GBrowserIsCompatible()) return this;
		
		// Build main options before element iteration
		var opts = $.extend({}, $.fn.gMap.defaults, options);
    	
		// Iterate through each element
		return this.each(function()
		{
			// Create map and set initial options
			$gmap = new GMap2(this);
			
			// Create new object to geocode addresses
			$geocoder = new GClientGeocoder();
			
			// Check for address to center on
			if (opts.address)
			{ 
				// Get coordinates for given address and center the map
				$geocoder.getLatLng(opts.address, function(gpoint){ $gmap.setCenter(gpoint, opts.zoom); });
				
			}
			else
			{
				// Check for coordinates to center on
				if (opts.latitude && opts.longitude)
				{
					// Center map to coordinates given by option
					$gmap.setCenter(new GLatLng(opts.latitude, opts.longitude), opts.zoom);
					
				}
				else
				{
					// Check for a marker to center on (if no coordinates given)
					if ($.isArray(opts.markers) && opts.markers.length > 0)
					{
						// Check if the marker has an address
						if (opts.markers[0].address)
						{
							// Get the coordinates for given marker address and center
							$geocoder.getLatLng(opts.markers[0].address, function(gpoint){ $gmap.setCenter(gpoint, opts.zoom); });
							
						}
						else
						{
							// Center the map to coordinates given by marker
							$gmap.setCenter(new GLatLng(opts.markers[0].latitude, opts.markers[0].longitude), opts.zoom);
							
						}
						
						
					}
					else
					{
						// Revert back to world view
						$gmap.setCenter(new GLatLng(34.885931, 9.84375), opts.zoom);
						
					}
					
				}
				
			}
						
			// Set the preferred map type
			$gmap.setMapType(opts.maptype);
			
			// Check for map controls
			if (opts.controls.length == 0)
			{
				// Default map controls
				$gmap.setUIToDefault();
				
			}
			else
			{
				// Add custom map controls
				for (var i = 0; i < opts.controls.length; i++)
				{
					// Eval is evil
					eval('$gmap.addControl(new ' + opts.controls[i] + '());');
					
				}
				
			}
						
			// Check if scrollwheel should be enabled
			if (opts.scrollwheel == true && opts.controls.length != 0) { $gmap.enableScrollWheelZoom(); }
									
			// Loop through marker array
			for (var j = 0; j < opts.markers.length; j++)
			{
				// Get the options from current marker
				marker = opts.markers[j];
								
				// Create new icon
				gicon = new GIcon();
				
				// Set icon properties from global options
				gicon.image = opts.icon.image;
				gicon.shadow = opts.icon.shadow;
				gicon.iconSize = ($.isArray(opts.icon.iconsize)) ? new GSize(opts.icon.iconsize[0], opts.icon.iconsize[1]) : opts.icon.iconsize;
				gicon.shadowSize = ($.isArray(opts.icon.shadowsize)) ? new GSize(opts.icon.shadowsize[0], opts.icon.shadowsize[1]) : opts.icon.shadowsize;
				gicon.iconAnchor = ($.isArray(opts.icon.iconanchor)) ? new GPoint(opts.icon.iconanchor[0], opts.icon.iconanchor[1]) : opts.icon.iconanchor;
				gicon.infoWindowAnchor = ($.isArray(opts.icon.infowindowanchor)) ? new GPoint(opts.icon.infowindowanchor[0], opts.icon.infowindowanchor[1]) : opts.icon.infowindowanchor;
				
				if (marker.icon)
				{
					// Overwrite global options
					gicon.image = marker.icon.image;
					gicon.shadow = marker.icon.shadow;
					gicon.iconSize = ($.isArray(marker.icon.iconsize)) ? new GSize(marker.icon.iconsize[0], marker.icon.iconsize[1]) : marker.icon.iconsize;
					gicon.shadowSize = ($.isArray(marker.icon.shadowsize)) ? new GSize(marker.icon.shadowsize[0], marker.icon.shadowsize[1]) : marker.icon.shadowsize;
					gicon.iconAnchor = ($.isArray(marker.icon.iconanchor)) ? new GPoint(marker.icon.iconanchor[0], marker.icon.iconanchor[1]) : marker.icon.iconanchor;
					gicon.infoWindowAnchor = ($.isArray(marker.icon.infowindowanchor)) ? new GPoint(marker.icon.infowindowanchor[0], marker.icon.infowindowanchor[1]) : marker.icon.infowindowanchor;
					
				}
				
				// Check if address is available
				if (marker.address)
				{
					// Check for reference to the marker's address
					if (marker.html == '_address') { marker.html = marker.address; }
					
					// Get the point for given address
					$geocoder.getLatLng(marker.address, function(gicon, marker)
					{
						// Since we're in a loop, we need a closure when dealing with event handlers, return functions, etc.
						// See <http://www.mennovanslooten.nl/blog/post/62> for more information about closures
						return function(gpoint)
						{
							// Create marker
							gmarker = new GMarker(gpoint, gicon);
							
							// Set HTML and check if info window should be opened
							if (marker.html) { gmarker.bindInfoWindowHtml(opts.html_prepend + marker.html + opts.html_append); }
							if (marker.html && marker.popup) { gmarker.openInfoWindowHtml(opts.html_prepend + marker.html + opts.html_append); }
							
							// Add marker to map
							if (gmarker) { $gmap.addOverlay(gmarker); }
						}
						
					}(gicon, marker));
					
				}
				else
				{
					// Check for reference to the marker's latitude/longitude
					if (marker.html == '_latlng') { marker.html = marker.latitude + ', ' + marker.longitude; }
					
					// Create marker
					gmarker = new GMarker(new GPoint(marker.longitude, marker.latitude), gicon);
					
					// Set HTML and check if info window should be opened
					if (marker.html) { gmarker.bindInfoWindowHtml(opts.html_prepend + marker.html + opts.html_append); }
					if (marker.html && marker.popup) { gmarker.openInfoWindowHtml(opts.html_prepend + marker.html + opts.html_append); }
						
					// Add marker to map
					if (gmarker) { $gmap.addOverlay(gmarker); }
					
				}
				
			}
			
		});
		
	}
		
	// Default settings
	$.fn.gMap.defaults =
	{
		address:				'',
		latitude:				0,
		longitude:				0,
		zoom:					1,
		markers:				[],
		controls:				[],
		scrollwheel:			true,
		maptype:				G_NORMAL_MAP,
		html_prepend:			'<div class="gmap_marker">',
		html_append:			'</div>',
		icon:
		{
			image:				"http://www.google.com/mapfiles/marker.png",
			shadow:				"http://www.google.com/mapfiles/shadow50.png",
			iconsize:			[20, 34],
			shadowsize:			[37, 34],
			iconanchor:			[9, 34],
			infowindowanchor:	[9, 2]
			
		}
		
	}
	
})(jQuery);