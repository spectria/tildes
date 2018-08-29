$.onmount('[data-js-comment-expand-all-button]', function() {
    $(this).click(function(event) {
        $('.is-comment-collapsed, .is-comment-collapsed-individual').each(
            function(idx, child) {
                $(child).find(
                    '[data-js-comment-collapse-button]:first').trigger('click');
            });

        $(this).blur();
    });
});
