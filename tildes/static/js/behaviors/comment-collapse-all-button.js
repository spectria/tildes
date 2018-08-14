$.onmount('[data-js-comment-collapse-all-button]', function() {
    $(this).click(function(event) {
        $('.comment[data-comment-depth="1"]:not(.is-comment-collapsed)').each(
            function(idx, child) {
                $(child).find(
                    '[data-js-comment-collapse-button]:first').trigger('click');
            });

        $(this).blur();
    });
});
