$.onmount('[data-js-external-links-new-tabs]', function() {
    // Open external links in topic, comment, and message text in new tabs
    $(this).find('a').each(function() {
        if (this.host !== window.location.host) {
          $(this).attr('target', '_blank');
        }
    });
});
