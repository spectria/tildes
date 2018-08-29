$.onmount('[data-js-comment-collapse-all-button]', function() {
    $(this).click(function(event) {
        // first uncollapse any individually collapsed comments
        $('.is-comment-collapsed-individual').each(
            function(idx, child) {
                $(child).find(
                    '[data-js-comment-collapse-button]:first').trigger('click');
            });

        // then collapse all first-level replies
        $('.comment[data-comment-depth="1"]:not(.is-comment-collapsed)').each(
            function(idx, child) {
                $(child).find(
                    '[data-js-comment-collapse-button]:first').trigger('click');
            });

        $(this).blur();
    });
});
