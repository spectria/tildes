$.onmount('[data-js-comment-collapse-button]', function() {
    $(this).click(function(event) {
        $this = $(this);
        $comment = $this.closest('.comment');

        $comment.toggleClass('is-comment-collapsed');

        if ($comment.hasClass('is-comment-collapsed')) {
            $this.text('+');
        } else {
            $this.html('&minus;');
        }

        $this.blur();
    });
});
