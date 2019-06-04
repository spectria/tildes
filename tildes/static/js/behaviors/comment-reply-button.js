// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-comment-reply-button]", function() {
    $(this).click(function(event) {
        event.preventDefault();

        // disable click/hover events on the reply button
        $(this).css("pointer-events", "none");

        var $comment = $(this)
            .parents(".comment")
            .first();

        // get the replies list, or create one if it doesn't already exist
        var $replies = $comment.children(".comment-tree-replies");
        if (!$replies.length) {
            var repliesList = document.createElement("ol");
            repliesList.setAttribute("class", "comment-tree comment-tree-replies");
            $comment.append(repliesList);
            $replies = $(repliesList);
        }

        var $parentComment = $(this).parents("article.comment:first");
        var parentCommentID = $parentComment.attr("data-comment-id36");
        var postURL = "/api/web/comments/" + parentCommentID + "/replies";
        var markdownID = "markdown-reply-" + parentCommentID;
        var previewID = markdownID + "-preview";

        if ($("#" + markdownID).length > 0) {
            $("#" + markdownID).focus();
            return;
        }

        // clone and populate the 'comment-reply' template
        var template = document.getElementById("comment-reply");
        var clone = document.importNode(template.content, true);

        clone.querySelector("form").setAttribute("data-ic-post-to", postURL);
        var textarea = clone.querySelector("textarea");
        textarea.setAttribute("id", markdownID);

        var preview = clone.querySelector(".form-markdown-preview");
        preview.setAttribute("id", previewID);

        clone
            .querySelector("[data-js-markdown-preview-tab] .btn")
            .setAttribute("data-ic-target", "#" + previewID);

        var cancelButton = clone.querySelector("[data-js-cancel-button]");
        $(cancelButton).on("click", function() {
            // re-enable click/hover events on the reply button
            $(this)
                .parents(".comment")
                .first()
                .find(".btn-post-action[name=reply]")
                .first()
                .css("pointer-events", "auto");
        });

        // If the user has text selected inside a comment when they click the reply
        // button, start the comment form off with that text inside a blockquote
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
                textarea.value = selectedText + "\n\n";
                textarea.scrollTop = textarea.scrollHeight;
            }
        }

        // update Intercooler so it knows about this new form
        Intercooler.processNodes(clone);

        $replies.prepend(clone);
        $.onmount();
    });
});
