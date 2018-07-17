$.onmount('[data-js-autoselect-input]', function() {
    $(this).click(function(event) {
        $(this).select();
    });
});
