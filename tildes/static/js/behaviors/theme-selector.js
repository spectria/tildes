$.onmount('[data-js-theme-selector]', function() {
    $(this).change(function(event) {
        event.preventDefault();

        var new_theme = $(this).val();

        // persist the new theme for the user in their cookie
        document.cookie = 'theme=' + new_theme + ';' +
            'path=/;max-age=315360000;secure';

        // remove any theme classes currently on the body
        $body = $('body').first();
        var bodyClasses = $body[0].className.split(' ');
        for (i = 0; i < bodyClasses.length; i++) {
            cls = bodyClasses[i];
            if (cls.indexOf('theme-') === 0) {
                $body.removeClass(cls);
            }
        }

        // if a non-default theme was chosen, add the class to the body
        if (new_theme) {
            $body.addClass('theme-' + new_theme);
        }
    });
});
