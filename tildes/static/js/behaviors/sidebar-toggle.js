$.onmount('[data-js-sidebar-toggle]', function() {
    $(this).click(function(event) {
        event.preventDefault();
        event.stopPropagation();

        $('#sidebar').toggleClass('is-sidebar-displayed');
    });
});
