// Copyright (c) 2019 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount('[data-js-back-to-top-buffer]', function() {
    // Uses the Intersection Observer API to observe when the div with ID
    // back-to-top-buffer has been scrolled entirely out of the viewport,
    // and adds the btn-back-to-top-visible class to the "Back to top" button
    // at that point. If the buffer is scrolled back into the viewport, it
    // removes the class, hiding the button again.
    var callback = function(entries, observer) {
        if (entries[0].isIntersecting) {
            $(".btn-back-to-top").removeClass("btn-back-to-top-visible");
        } else {
            $(".btn-back-to-top").addClass("btn-back-to-top-visible");
        }
    };

    this.intersectionObserver = new IntersectionObserver(callback);
    this.intersectionObserver.observe(document.querySelector('#back-to-top-buffer'));
});
