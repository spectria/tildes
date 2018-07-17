$.onmount('[data-js-hide-sidebar-if-open]', function() {
    $(this).on('click', function(event) {
        if ($('#sidebar').hasClass('is-sidebar-displayed')) {
            event.preventDefault();
            event.stopPropagation();
            $('#sidebar').removeClass('is-sidebar-displayed');
        }
    });
});
