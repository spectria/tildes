$.onmount('[data-js-fadeout-parent-on-success]', function() {
    $(this).on('after.success.ic', function() {
        $(this).parent().fadeOut('fast');
    });
});
