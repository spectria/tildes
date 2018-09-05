// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount('[data-js-comment-tag-button]', function() {
    $(this).click(function(event) {
        event.preventDefault();

        var $comment = $(this).parents('.comment').first();
        var user_tags = $comment.attr('data-comment-user-tags');

        // check if the tagging button div already exists and just remove it if so
        $tagButtons = $comment.find('.comment-itself:first').find('.comment-tag-buttons');
        if ($tagButtons.length > 0) {
            $tagButtons.remove();
            return;
        }

        var commentID = $comment.attr('data-comment-id36');
        var tagURL = '/api/web/comments/' + commentID + '/tags/';

        var tagtemplate = document.querySelector('#comment-tag-options');
        var clone = document.importNode(tagtemplate.content, true);
        var options = clone.querySelectorAll('a');

        for (i = 0; i < options.length; i++) {
            var tag = options[i];
            var tagName = tag.textContent;

            var tagOptionActive = false;
            if (user_tags.indexOf(tagName) !== -1) {
                tagOptionActive = true;
            }

            if (tagOptionActive) {
                tag.className += " btn btn-used";
                tag.setAttribute('data-ic-delete-from', tagURL + tagName);
                $(tag).on('after.success.ic', function(evt) {
                    Tildes.removeUserTag(commentID, evt.target.textContent);
                });
            } else {
                tag.setAttribute('data-ic-put-to', tagURL + tagName);
                $(tag).on('after.success.ic', function(evt) {
                    Tildes.addUserTag(commentID, evt.target.textContent);
                });
            }

            tag.setAttribute('data-ic-target', '#comment-' + commentID + ' .comment-itself:first');
        }

        // update Intercooler so it knows about these new elements
        Intercooler.processNodes(clone);

        $comment.find(".post-buttons").first().after(clone);
    });
});

Tildes.removeUserTag = function(commentID, tagName) {
    $comment = $("#comment-" + commentID);
    var user_tags = $comment.attr('data-comment-user-tags').split(" ");

    // if the tag isn't there, don't need to do anything
    tagIndex = user_tags.indexOf(tagName);
    if (tagIndex === -1) {
        return;
    }

    // remove the tag from the list and update the data attr
    user_tags.splice(tagIndex, 1);
    $comment.attr('data-comment-user-tags', user_tags.join(" "));
}

Tildes.addUserTag = function(commentID, tagName) {
    $comment = $("#comment-" + commentID);
    var user_tags = $comment.attr('data-comment-user-tags').split(" ");

    // don't add the tag again if it's already there
    tagIndex = user_tags.indexOf(tagName);
    if (tagIndex !== -1) {
        return;
    }

    // add the tag to the list and update the data attr
    user_tags.push(tagName);
    $comment.attr('data-comment-user-tags', user_tags.join(" "));
}
