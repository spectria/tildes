# Contributing to Tildes development

Outside of actual code changes, there are several other ways to contribute to Tildes development:

* Known issues and plans for upcoming changes are [tracked on GitLab](https://gitlab.com/tildes/tildes/issues). If you've found a bug/problem on the site or have a suggestion, please feel free to submit an issue for it (if one doesn't already exist). If you have a Tildes account, you can also post in [the ~tildes group](https://tildes.net/~tildes) with issues, suggestions, or questions.
* The [Tildes Docs site](https://docs.tildes.net) is also open-source and accepts contributions. It has a separate repository, also on GitLab: https://gitlab.com/tildes/tildes-static-sites
* [Donating to Tildes](https://docs.tildes.net/donate) supports its development directly by enabling Deimos to continue working on it full-time. Tildes is a non-profit with no investors and no advertising. Its operation and development relies on donations.

## License

Please take note that Tildes uses [the AGPLv3 license](https://www.gnu.org/licenses/why-affero-gpl.html). This means that if you use the Tildes code to run your own instance of the site, you *must* also open-source the code for your site, including any changes that you've made. If you are not able to open-source the code for your instance, you can not use the Tildes code to run it.

All code contributions must be made under the same license as the project's main license (i.e. *AGPL-3.0-or-later* for [Tildes code](https://gitlab.com/tildes/tildes) and *MIT* for code handling [Tildes documentation](https://gitlab.com/tildes/tildes-static-sites)) and all documentation contributions under the same license as the main license of the documentation (i.e. *CC-BY-SA-4.0*).

## Setting up a development version

Please see this page on the Tildes Docs for instructions to set up a development version: https://docs.tildes.net/development-setup

## General development information

This page on the Tildes docs contains information about many aspects of Tildes development: https://docs.tildes.net/development

## Contributing code

**Please do not work on significant changes or features without first ensuring that the changes are desired.** If there isn't already an issue related to the change you're intending to make, please [create one first](https://gitlab.com/tildes/tildes/issues/new) to discuss your plans. Similarly, even when there *is* already an issue, if the specifics of how it should work aren't clear, please try to sort that out first (by posting comments on the issue) before doing the work.

In general, anything beyond straightforward fixes and adjustments should have an associated issue. This is for everyone's benefit—it ensures that you don't waste effort working on changes that won't be accepted, and makes it easier for other contributors to see what's already being worked on.

### Choosing what to work on

If you look at [the list of issues](https://gitlab.com/tildes/tildes/issues), there are a few indicators you can use to find a good contribution to work on:

* Make sure the issue isn't already being worked on by someone else. Check the comments on it, and whether it's set as "assigned to" someone. If someone else was working on it but there hasn't been any activity in a while, please post a comment first to check if they're still making progress.
* Issues with the "high priority" label are ones that are needed soon, and contributions for these will probably be most appreciated. However, they may also be more complex than many other issues, and might not be the best place for a newer contributor to start.
* Check the "Weight" field on the issue. If set, this is an estimate of how complex it will be to address, ranging from 1 (extremely simple, very small changes) to 9 (major changes, possibly requiring days or even weeks of work).

Once you've selected an issue to work on, please leave a comment saying so. This will allow other people to see that they shouldn't also start on that issue.

### Before submitting a merge request

After you've finished making your changes, there are a few things to check before proposing your changes as a merge request.

First, ensure that all the checks (tests, mypy and code-style) pass successfully. Merge requests that fail any of the checks will not be accepted. For more information, see this section of the development docs: https://docs.tildes.net/development#running-checks-on-your-code

Squash your changes into logical commits. For many changes there should only be a single commit, but some can be broken into multiple logical sections. The commit messages should follow [the formatting described in this article](https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html), with the summary line written in the imperative form. The summary line should make sense if you were to use it in a sentence like "If applied, this commit will \_\_\_\_\_\_\_\_". For example, "Add a new X", "Fix a bug with Y", and so on.

### Merge request and code review

Once your code is ready, you can [submit a new merge request on GitLab](https://gitlab.com/tildes/tildes/merge_requests/new).

After creating the merge request, if you need to make any further changes to your code (whether in response to code review or not), please add the changes as new commits. Do not modify the existing commits, this makes it far simpler for other people to follow what changes you're making. Once the merge request is approved, a final pass can be done to squash the commits down, make updates to commit messages, etc. before it's actually merged.
