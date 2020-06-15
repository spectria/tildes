// Copyright (c) 2020 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-comment-reply-form]", function() {
    var $this = $(this);

    // the parent comment's Reply button (that was clicked to create this form)
    var $replyButton = $this
        .closest(".comment")
        .find(".btn-post-action[name=reply]")
        .first();

    // disable click/hover events on the reply button to prevent opening multiple forms
    $replyButton.css("pointer-events", "none");

    // have the Cancel button re-enable click/hover events on the reply button
    $this.find("[data-js-cancel-button]").click(function() {
        $replyButton.css("pointer-events", "auto");
    });

    var $textarea = $this.find("textarea").first();

    // If the user has text selected inside a comment when the reply form is created,
    // populate the textbox with that text inside a blockquote
    if (window.getSelection) {
        var selectedText = "";

        // only capture the selected text if it's all from the same comment
        var selection = window.getSelection();
        var $start = $(selection.anchorNode).closest(".comment-text");
        var $end = $(selection.focusNode).closest(".comment-text");
        if ($start.is($end)) {
            selectedText = selection.toString();
        }

        if (selectedText.length > 0) {
            selectedText = selectedText.replace(/\s+$/g, "");
            selectedText = selectedText.replace(/^/gm, "> ");

            $textarea.val(selectedText + "\n\n");
            $textarea.scrollTop($textarea.prop("scrollHeight"));
        }
    }

    $textarea.focus();
});
