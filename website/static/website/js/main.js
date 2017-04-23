jQuery(function($) {'use strict',

	//#main-slider
	$(function(){
		$('#main-slider.carousel').carousel({
			interval: 8000
		});
	});

	//Initiat WOW JS
	new WOW().init();

	// gallery filter
	$(window).load(function(){

		var $gallery_selectors = $('.gallery-filter >li>a');
		var $gallery = $('.gallery-items');
		$gallery.isotope({
			itemSelector : '.gallery-item',
			layoutMode : 'masonry'
		});

		$gallery_selectors.on('click', function(){
			$gallery_selectors.removeClass('active');
			$(this).addClass('active');
			var selector = $(this).attr('data-filter');
			$gallery.isotope({ filter: selector });
			return false;
		});
	});

});