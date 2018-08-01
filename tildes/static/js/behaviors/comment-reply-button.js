$.onmount('[data-js-comment-reply-button]', function() {
    $(this).click(function(event) {
        event.preventDefault();

        // disable click/hover events on the reply button
        $(this).css('pointer-events', 'none');

        var $comment = $(this).parents('.comment').first();

        // get the replies div, or create one if it doesn't already exist
        var $replies = $comment.children('.comment-replies');
        if (!$replies.length) {
            var repliesDiv = document.createElement('div');
            repliesDiv.setAttribute('class', 'comment-replies');
            $comment.append(repliesDiv);
            $replies = $(repliesDiv);
        }

        var $parentComment = $(this).parents('article.comment:first');
        var parentCommentID = $parentComment.attr('data-comment-id36');
        var parentCommentAuthor = $parentComment.find('header:first .link-user').text();
        var postURL = '/api/web/comments/' + parentCommentID + '/replies';
        var markdownID = 'markdown-reply-' + parentCommentID;

        var replyForm = document.createElement('form');
        replyForm.setAttribute('method', 'post');
        replyForm.setAttribute('autocomplete', 'off');
        replyForm.setAttribute('data-ic-post-to', postURL);
        replyForm.setAttribute('data-ic-replace-target', 'true');
        replyForm.setAttribute('data-js-confirm-cancel', 'Discard your reply?');
        replyForm.setAttribute('data-js-prevent-double-submit', '');
        replyForm.setAttribute('data-js-confirm-leave-page-unsaved', '');

        var label = document.createElement('label');
        label.setAttribute('class', 'form-label');
        label.setAttribute('for', markdownID);
        label.innerHTML = '<span>Replying to ' + parentCommentAuthor + '</span>' +
            '<a href="https://docs.tildes.net/text-formatting" target="_blank">' +
            'Formatting help</a>';

        var textarea = document.createElement('textarea');
        textarea.setAttribute('id', markdownID);
        textarea.setAttribute('name', 'markdown');
        textarea.setAttribute('class', 'form-input');
        textarea.setAttribute('placeholder', 'Comment text (Markdown)');
        textarea.setAttribute('data-js-ctrl-enter-submit-form', '');
        textarea.setAttribute('data-js-auto-focus', '');

        var buttonDiv = document.createElement('div');
        buttonDiv.setAttribute('class', 'form-buttons');

        var postButton = document.createElement('button');
        postButton.setAttribute('type', 'submit');
        postButton.setAttribute('class', 'btn btn-primary');
        postButton.innerHTML = 'Post comment';
        buttonDiv.appendChild(postButton);

        var cancelButton = document.createElement('button');
        cancelButton.setAttribute('type', 'button');
        cancelButton.setAttribute('class', 'btn btn-link');
        cancelButton.setAttribute('data-js-cancel-button', '');
        cancelButton.innerHTML = 'Cancel';

        $(cancelButton).on('click', function (event) {
            // re-enable click/hover events on the reply button
            $(this).parents('.comment').first()
                .find('.post-button[name=reply]').first()
                .css('pointer-events', 'auto');
        });
        buttonDiv.appendChild(cancelButton);

        replyForm.appendChild(label);
        replyForm.appendChild(textarea);
        replyForm.appendChild(buttonDiv);

        // update Intercooler so it knows about this new form
        Intercooler.processNodes(replyForm);

        $replies.prepend(replyForm);
        $.onmount();
    });
});
