$(document).ready(function(){
    console.log('Here');
    loadGallery(true, 'a.gallery-thumbnail');

    //This function disables buttons when needed
    function disableButtons(counter_max, counter_current){
        $('#show-previous-image, #show-next-image').show();
        if (counter_max == 1){
            $('#show-next-image').hide();
            $('#show-previous-image').hide();
        } else if(counter_max == counter_current){
            $('#show-next-image').hide();
        } else if (counter_current == 1){
            $('#show-previous-image').hide();
        }
    }

    /**
     *
     * @param setIDs        Sets IDs when DOM is loaded. If using a PHP counter, set to false.
     * @param setClickAttr  Sets the attribute for the click handler.
     */

    function loadGallery(setIDs, setClickAttr){
        var current_image,
            selector,
            counter = 0;

        $('#show-next-image, #show-previous-image').click(function(){
            if($(this).attr('id') == 'show-previous-image'){
                current_image--;
            } else {
                current_image++;
            }

            selector = $('[data-image-id="' + current_image + '"]');
            updateGallery(selector);
        });

        function updateGallery(selector) {
            console.log('Here');
            var $sel = selector;
            current_image = $sel.data('image-id');
            if($sel.data('caption') != null) {
                $('#image-gallery-caption').text($sel.data('caption'));
            } else {
                $('#image-gallery-caption').text('');
            }

            $('#image-gallery-title').text($sel.data('title'));
            $('#image-gallery-image').attr('src', $sel.data('image'));
            disableButtons(counter, $sel.data('image-id'));
        }

        if(setIDs == true){
            $('[data-image-id]').each(function(){
                counter++;
                $(this).attr('data-image-id',counter);
            });
        }
        $(setClickAttr).on('click',function(){
            updateGallery($(this));
        });
    }

    jQuery(function($) {
        $('img').one('load', function () {
            var $img = $(this);
            var tempImage1 = new Image();
            tempImage1.src = $img.attr('src');
            tempImage1.onload = function() {
                var ratio = tempImage1.width / tempImage1.height;
                if(!isNaN(ratio) && ratio < 1) $img.addClass('portrait');
            }
        }).each(function () {
            if (this.complete) $(this).load();
        });
    });

    //http://tablesorter.com/docs/
    jQuery("#sortTable").tablesorter();
});