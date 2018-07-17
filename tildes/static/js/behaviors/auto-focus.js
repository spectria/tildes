$.onmount('[data-js-auto-focus]', function() {
    $input = $(this);

    // just calling .focus() will place the cursor at the start of the field,
    // so un-setting and re-setting the value moves the cursor to the end
    var original_val = $input.val();
    $input.focus().val('').val(original_val);
});
