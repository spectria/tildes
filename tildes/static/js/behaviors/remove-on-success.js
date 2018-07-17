$.onmount('[data-js-remove-on-success]', function() {
    $(this).on('after.success.ic', function() {
        $(this).remove();
    });
});
