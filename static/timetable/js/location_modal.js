$(document).ready(function() {

    var setClickAttr = $('a.location-link');

    function updateModal(selector) {
            var $sel = selector;
            $('#location-title').text($sel.data('full_name'));
            $('#location-address').text($sel.data('address'));
            $('#location-map').attr('src', $sel.data('map_url'));
        }

    $(setClickAttr).on('click',function(){
        updateModal($(this));
    });
});