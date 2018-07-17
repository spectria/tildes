$.onmount('[data-js-remove-on-click]', function() {
    $(this).on('click', function() {
        $(this).remove();
    });
});
