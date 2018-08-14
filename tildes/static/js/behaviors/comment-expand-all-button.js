$.onmount('[data-js-comment-expand-all-button]', function() {
    $(this).click(function(event) {
        $('.comment.is-comment-collapsed').each(
            function(idx, child) {
                $(child).find(
                    '[data-js-comment-collapse-button]:first').trigger('click');
            });

        $(this).blur();
    });
});
