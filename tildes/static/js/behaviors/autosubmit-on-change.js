$.onmount('[data-js-autosubmit-on-change]', function() {
    $(this).change(function(event) {
        $(this).closest('form').submit();
    });
});
