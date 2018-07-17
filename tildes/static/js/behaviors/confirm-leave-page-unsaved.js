$.onmount('[data-js-confirm-leave-page-unsaved]', function() {
    $form = $(this);
    $form.areYouSure();

    // Fixes a strange interaction between Intercooler and AreYouSure, where
    // submitting a form by using the keyboard to push the submit button would
    // trigger a confirmation prompt before leaving the page.
    $form.on('success.ic', function() {
        $form.removeClass('dirty');
    });
});
