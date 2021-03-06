$(document).ready(function() {

    var setClickLocationAttr = $('a.location-link');
    var setClickDescAttr = $('a.description-link');

    function updateLocModal(selector) {
        var $sel = selector;
        $('#location-title').text($sel.data('short_name'));
        $('#location-full_name').text($sel.data('full_name'));
        $('#location-address').text($sel.data('address'));
        if ($sel.data('map_url') != "") {
            $('#location-map').attr('src', $sel.data('map_url'));
            $('#location-map').attr('style', 'border:2px solid black;');
            $('#location-map').attr('width', '100%;');
            $('#location-map').attr('height', '300px;');
        }
        else {
            $('#location-map').attr('src', '');
            $('#location-map').attr('style', 'border:none;');
            $('#location-map').attr('width', '0%;');
            $('#location-map').attr('height', '0px;');
        }
        ;
    }

    function updateDescModal(selector) {
        var $sel = selector;
        $('#description-title').text($sel.data('title'));
        $('#description-text').text($sel.data('description'));
        $('#block_info-text').text($sel.data('blockinfo'));
        $('#cost-text').text($sel.data('costinfo'));
        $('#location').text($sel.data('location'));
        $('#location-address').text($sel.data('address'));
        $('#spaces-text').text($sel.data('spaces'));
    }

    $(setClickLocationAttr).on('click',function(){
        updateLocModal($(this));
    });

    $(setClickDescAttr).on('click',function(){
        updateDescModal($(this));
    });
});