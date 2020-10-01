"""
The tests here test the webapp by sending fake requests through a fake GH
object and checking that the right API calls were made.

Each fake request has just the API information currently needed by the webapp,
so if more API information is used, it will need to be added.

The GitHub API docs are useful:

- Pull request event (the main input to the webapp):
  https://developer.github.com/v3/activity/events/types/#pullrequestevent
- Pull request object (the 'pull_request' key to the pull request event):
  https://developer.github.com/v3/pulls/
- Commit objects (the output from the 'commits_url'):
  https://developer.github.com/v3/pulls/#list-commits-on-a-pull-request
- Comment objects (the output from the 'comments_url'):
  https://developer.github.com/v3/issues/comments/
- Contents objects (the output from the version_url):
  https://developer.github.com/v3/repos/contents/
- Statuses objects (the output from statuses_url):
  https://developer.github.com/v3/repos/statuses/

"""

import datetime
import base64
from subprocess import CalledProcessError
import os

from gidgethub import sansio

from ..webapp import router

# These are required for the tests to run properly
import pytest_aiohttp
pytest_aiohttp
import pytest_mock
pytest_mock

from pytest import mark, raises
parametrize = mark.parametrize

class FakeRateLimit:
    def __init__(self, *, remaining=5000, limit=5000, reset_datetime=None):
        self.remaining = remaining
        self.limit = limit
        now = datetime.datetime.now(datetime.timezone.utc)
        self.reset_datetime = reset_datetime or now + datetime.timedelta(hours=1)

class FakeGH:
    """
    Faked gh object

    Arguments:

    - getitem: dictionary mapping {url: result}, or None
    - getiter: dictionary mapping {url: result}, or None
    - rate_limit: FakeRateLimit object, or None
    - post: dictionary mapping {url: result}, or None
    - patch: dictionary mapping {url: result}, or None
    - delete: dictionary mapping {url: result}, or None

    The results are stored in the properties

    - getiter_urls: list of urls called with getiter
    - getitem_urls: list of urls called with getitem
    - post_urls: list of urls called with post
    - post_data: list of the data input for each post
    - patch_urls: list of urls called with patch
    - patch_data: list of the data input for each patch
    - delete_urls: list of urls called with delete
    - rate_limit: the FakeRateLimit object

    Note that GET requests are cached in the code and may be called multiple
    times.
    """
    def __init__(self, *, getitem=None, getiter=None, rate_limit=None,
        post=None, patch=None, delete=None):
        self._getitem_return = getitem
        self._getiter_return = getiter
        self._post_return = post
        self._patch_return = patch
        self._delete_return = delete
        self.getiter_urls = []
        self.getitem_urls = []
        self.post_urls = []
        self.post_data = []
        self.patch_urls = []
        self.patch_data = []
        self.delete_urls = []
        self.rate_limit = rate_limit or FakeRateLimit()

    async def getitem(self, url):
        self.getitem_urls.append(url)
        return self._getitem_return[url]

    async def getiter(self, url):
        self.getiter_urls.append(url)
        for item in self._getiter_return[url]:
            yield item

    async def post(self, url, *, data):
        self.post_urls.append(url)
        self.post_data.append(data)
        return self._post_return[url]

    async def patch(self, url, *, data):
        self.patch_urls.append(url)
        self.patch_data.append(data)
        return self._patch_return[url]

    async def delete(self, url):
        self.delete_urls.append(url)
        return self._delete_return[url]

def _assert_gh_is_empty(gh):
    assert gh._getitem_return == None
    assert gh._getiter_return == None
    assert gh._post_return == None
    assert gh.getiter_urls == []
    assert gh.getitem_urls == []
    assert gh.post_urls == []
    assert gh.post_data == []
    assert gh.patch_urls == []
    assert gh.patch_data == []
    assert gh.delete_urls == []

def _event(data):
    return sansio.Event(data, event='pull_request', delivery_id='1')

version = '1.2.1'
release_notes_file = 'Release-Notes-for-1.2.1.md'
comments_url = 'https://api.github.com/repos/sympy/sympy/pulls/1/comments'
commits_url = 'https://api.github.com/repos/sympy/sympy/pulls/1/commits'
contents_url = 'https://api.github.com/repos/sympy/sympy/contents/{+path}'
sha = 'a109f824f4cb2b1dd97cf832f329d59da00d609a'
commit_url_template = 'https://api.github.com/repos/sympy/sympy/commits/{sha}'
commit_url = commit_url_template.format(sha=sha)
version_url_template = 'https://api.github.com/repos/sympy/sympy/contents/sympy/release.py?ref={ref}'
version_url = version_url_template.format(ref='master')
html_url = "https://github.com/sympy/sympy"
wiki_url = "https://github.com/sympy/sympy.wiki"
comment_html_url = 'https://github.com/sympy/sympy/pulls/1#issuecomment-1'
comment_html_url2 = 'https://github.com/sympy/sympy/pulls/1#issuecomment-2'
statuses_url = "https://api.github.com/repos/sympy/sympy/statuses/4a09f9f253c7372ec857774b1fe114b1266013fe"
existing_comment_url = "https://api.github.com/repos/sympy/sympy/issues/comments/1"
existing_added_deleted_comment_url = "https://api.github.com/repos/sympy/sympy/issues/comments/2"
pr_number = 1

valid_PR_description = """
<!-- BEGIN RELEASE NOTES -->
* solvers
  * new trig solvers
<!-- END RELEASE NOTES -->
"""

valid_PR_description_no_entry = """
<!-- BEGIN RELEASE NOTES -->
NO ENTRY
<!-- END RELEASE NOTES -->
"""

invalid_PR_description = """
<!-- BEGIN RELEASE NOTES -->

<!-- END RELEASE NOTES -->
"""

release_notes_comment_body = """\
:white_check_mark:

Hi, I am the [SymPy bot](https://github.com/sympy/sympy-bot) (version not found!). I'm here to help you write a release notes entry. Please read the [guide on how to write release notes](https://github.com/sympy/sympy/wiki/Writing-Release-Notes).



Your release notes are in good order.

Here is what the release notes will look like:
* solvers
  * new trig solvers ([#1](https://github.com/sympy/sympy/pull/1) by [@asmeurer](https://github.com/asmeurer) and [@certik](https://github.com/certik))

This will be added to https://github.com/sympy/sympy/wiki/Release-Notes-for-1.2.1.

Note: This comment will be updated with the latest check if you edit the pull request. You need to reload the page to see it. <details><summary>Click here to see the pull request description that was parsed.</summary>


    <!-- BEGIN RELEASE NOTES -->
    * solvers
      * new trig solvers
    <!-- END RELEASE NOTES -->


</details><p>
"""

added_deleted_comment_body = """\
### \U0001f7e0

Hi, I am the [SymPy bot](https://github.com/sympy/sympy-bot) (version not found!). I've noticed that some of your commits add or delete files. Since this is sometimes done unintentionally, I wanted to alert you about it.

This is an experimental feature of SymPy Bot. If you have any feedback on it, please comment at https://github.com/sympy/sympy-bot/issues/75.

The following commits **add new files**:
* 174b8b37bc33e9eb29e710a233190d02a13bdb54:
  - `file1`

The following commits **delete files**:
* a109f824f4cb2b1dd97cf832f329d59da00d609a:
  - `file1`

If these files were added/deleted on purpose, you can ignore this message.
"""

@parametrize('action', ['closed', 'synchronize', 'edited'])
@parametrize('merged', [True, False])
async def test_no_action_on_closed_prs(action, merged):
    if action == 'closed' and merged == True:
        return
    gh = FakeGH()
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'closed',
            'merged': merged,
            },
        }
    event_data['action'] = action

    event = _event(event_data)

    res = await router.dispatch(event, gh)
    assert res is None
    _assert_gh_is_empty(gh)

@parametrize('action', ['opened', 'reopened', 'synchronize', 'edited'])
async def test_status_good_new_comment(action):
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': False,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
                'ref': 'master',
            },
            'body': valid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }


    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        {
            'author': {
                'login': 'certik',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        # Test commits without a login
        {
            'author': None,
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
    ]

    commit = {
        'files': [
            {
                'status': 'modified',
            },
        ],
        'parents': [
                {
                    "url": commit_url,
                    "sha": sha,
                },
        ],
    }

    # No comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'asmeurer',
            },
        },
        {
            'user': {
                'login': 'certik',
            },
        },
    ]

    version_file = {
        'content': base64.b64encode(b'__version__ = "1.2.1.dev"\n'),
        }

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        version_url: version_file,
        commit_url: commit,
    }
    post = {
        comments_url: {
            'html_url': comment_html_url,
        },
        statuses_url: {},
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    assert set(getiter_urls) == set(getiter)
    assert set(getitem_urls) == set(getitem)
    assert post_urls == [comments_url, statuses_url]
    assert len(post_data) == 2
    # Comments data
    assert post_data[0].keys() == {"body"}
    comment = post_data[0]["body"]
    assert ":white_check_mark:" in comment
    assert ":x:" not in comment
    assert "new trig solvers" in comment
    assert "error" not in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    for line in valid_PR_description:
        assert line in comment
    assert "good order" in comment
    # Statuses data
    assert post_data[1] == {
        "state": "success",
        "target_url": comment_html_url,
        "description": "The release notes look OK",
        "context": "sympy-bot/release-notes",
    }
    assert patch_urls == []
    assert patch_data == []


@parametrize('action', ['opened', 'reopened', 'synchronize', 'edited'])
async def test_status_good_existing_comment(action):
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': False,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
                'ref': 'master',
            },
            'body': valid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }

    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        {
            'author': {
                'login': 'certik',
                },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        # Test commits without a login
        {
            'author': None,
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
    ]

    commit = {
        'files': [
            {
                'status': 'modified',
            },
        ],
        'parents': [
                {
                    "url": commit_url,
                    "sha": sha,
                },
        ],
    }

    # Has comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'sympy-bot',
            },
            'url': existing_comment_url,
            'body': release_notes_comment_body,
        },
        {
            'user': {
                'login': 'asmeurer',
            },
            'body': "comment",
        },
        {
            'user': {
                'login': 'certik',
            },
            "body": "comment",
        },
    ]

    version_file = {
        'content': base64.b64encode(b'__version__ = "1.2.1.dev"\n'),
        }

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        version_url: version_file,
        commit_url: commit,
    }
    post = {
        statuses_url: {},
    }

    patch = {
        existing_comment_url: {
            'html_url': comment_html_url,
        },
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post, patch=patch)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    assert set(getiter_urls) == set(getiter)
    assert set(getitem_urls) == set(getitem)
    assert post_urls == [statuses_url]
    # Statuses data
    assert post_data == [{
        "state": "success",
        "target_url": comment_html_url,
        "description": "The release notes look OK",
        "context": "sympy-bot/release-notes",
    }]
    # Comments data
    assert patch_urls == [existing_comment_url]
    assert len(patch_data) == 1
    assert patch_data[0].keys() == {"body"}
    comment = patch_data[0]["body"]
    assert ":white_check_mark:" in comment
    assert ":x:" not in comment
    assert "new trig solvers" in comment
    assert "error" not in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    for line in valid_PR_description:
        assert line in comment
    assert "good order" in comment


@parametrize('action', ['closed'])
async def test_closed_with_merging(mocker, action):
    # Based on test_status_good_existing_comment

    update_wiki_called_kwargs = {}
    def mocked_update_wiki(*args, **kwargs):
        nonlocal update_wiki_called_kwargs
        assert not args # All args are keyword-only
        update_wiki_called_kwargs = kwargs

    mocker.patch('sympy_bot.webapp.update_wiki', mocked_update_wiki)

    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': True,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
                'ref': 'master',
            },
            'body': valid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }


    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        {
            'author': {
                'login': 'certik',
                },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        # Test commits without a login
        {
            'author': None,
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
    ]

    # Has comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'sympy-bot',
            },
            'url': existing_comment_url,
            'body': release_notes_comment_body,
        },
        {
            'user': {
                'login': 'asmeurer',
            },
            'body': "comment",
        },
        {
            'user': {
                'login': 'certik',
            },
            'body': "comment",
        },
    ]

    version_file = {
        'content': base64.b64encode(b'__version__ = "1.2.1.dev"\n'),
        }

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        version_url: version_file,
    }
    post = {
        statuses_url: {},
    }

    patch = {
        existing_comment_url: {
            'html_url': comment_html_url,
            'body': release_notes_comment_body,
            'url': existing_comment_url,
        },
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post, patch=patch)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    assert set(getiter_urls) == set(getiter), getiter_urls
    assert set(getitem_urls) == set(getitem)
    assert post_urls == [statuses_url]
    # Statuses data
    assert post_data == [{
        "state": "success",
        "target_url": comment_html_url,
        "description": "The release notes look OK",
        "context": "sympy-bot/release-notes",
    }]
    # Comments data
    assert patch_urls == [existing_comment_url, existing_comment_url]
    assert len(patch_data) == 2
    assert patch_data[0].keys() == {"body"}
    comment = patch_data[0]["body"]
    assert comment == release_notes_comment_body
    assert ":white_check_mark:" in comment
    assert ":x:" not in comment
    assert "new trig solvers" in comment
    assert "error" not in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    for line in valid_PR_description:
        assert line in comment
    assert "good order" in comment
    updated_comment = patch_data[1]['body']
    assert updated_comment.startswith(comment)
    assert "have been updated" in updated_comment

    assert update_wiki_called_kwargs == {
        'wiki_url': wiki_url,
        'release_notes_file': release_notes_file,
        'changelogs': {'solvers': ['* new trig solvers']},
        'pr_number': pr_number,
        'authors': ['asmeurer', 'certik'],
    }



@parametrize('action', ['closed'])
async def test_closed_with_merging_no_entry(mocker, action):
    # Based on test_status_good_existing_comment

    update_wiki_called_kwargs = {}
    def mocked_update_wiki(*args, **kwargs):
        nonlocal update_wiki_called_kwargs
        assert not args # All args are keyword-only
        update_wiki_called_kwargs = kwargs

    mocker.patch('sympy_bot.webapp.update_wiki', mocked_update_wiki)

    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': True,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
                'ref': 'master',
            },
            'body': valid_PR_description_no_entry,
            'statuses_url': statuses_url,
        },
        'action': action,
    }

    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        {
            'author': {
                'login': 'certik',
                },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        # Test commits without a login
        {
            'author': None,
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
    ]

    # Has comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'sympy-bot',
            },
            'url': existing_comment_url,
            'body': release_notes_comment_body,
        },
        {
            'user': {
                'login': 'asmeurer',
            },
            'body': "comment",
        },
        {
            'user': {
                'login': 'certik',
            },
            'body': "comment",
        },
    ]

    version_file = {
        'content': base64.b64encode(b'__version__ = "1.2.1.dev"\n'),
        }

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        version_url: version_file,
    }
    post = {
        statuses_url: {},
    }

    patch = {
        existing_comment_url: {
            'html_url': comment_html_url,
            'body': release_notes_comment_body,
            'url': existing_comment_url,
        },
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post, patch=patch)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    assert set(getiter_urls) == set(getiter), getiter_urls
    assert set(getitem_urls) == set(getitem)
    assert post_urls == [statuses_url]
    # Statuses data
    assert post_data == [{
        "state": "success",
        "target_url": comment_html_url,
        "description": "The release notes look OK",
        "context": "sympy-bot/release-notes",
    }]
    # Comments data
    assert patch_urls == [existing_comment_url]
    assert len(patch_data) == 1
    assert patch_data[0].keys() == {"body"}
    comment = patch_data[0]["body"]
    assert "No release notes entry will be added for this pull request." in comment
    assert ":white_check_mark:" in comment
    assert ":x:" not in comment
    assert "error" not in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    for line in valid_PR_description:
        assert line in comment

    assert update_wiki_called_kwargs == {}

@parametrize('action', ['closed'])
@parametrize('exception', [RuntimeError('error message'),
                           CalledProcessError(1, 'cmd')])
async def test_closed_with_merging_update_wiki_error(mocker, action, exception):
    # Based on test_closed_with_merging

    update_wiki_called_kwargs = {}
    def mocked_update_wiki(*args, **kwargs):
        nonlocal update_wiki_called_kwargs
        assert not args # All args are keyword-only
        update_wiki_called_kwargs = kwargs
        raise exception

    mocker.patch('sympy_bot.webapp.update_wiki', mocked_update_wiki)
    mocker.patch.dict(os.environ, {"GH_AUTH": "TESTING TOKEN"})

    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': True,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
                'ref': 'master',
            },
            'body': valid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }


    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        {
            'author': {
                'login': 'certik',
                },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        # Test commits without a login
        {
            'author': None,
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
    ]

    # Has comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'sympy-bot',
            },
            'url': existing_comment_url,
            'body': release_notes_comment_body,
        },
        {
            'user': {
                'login': 'asmeurer',
            },
            'body': "comment",
        },
        {
            'user': {
                'login': 'certik',
            },
            'body': "comment",
        },
    ]

    version_file = {
        'content': base64.b64encode(b'__version__ = "1.2.1.dev"\n'),
        }

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        version_url: version_file,
    }
    post = {
        statuses_url: {},
        comments_url: {
            'html_url': comment_html_url,
        },
    }

    patch = {
        existing_comment_url: {
            'html_url': comment_html_url,
            'body': release_notes_comment_body,
            'url': existing_comment_url,
        },
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post, patch=patch)

    with raises(type(exception)):
        await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    assert set(getiter_urls) == set(getiter), getiter_urls
    assert set(getitem_urls) == set(getitem)
    assert post_urls == [statuses_url, comments_url, statuses_url]
    # Statuses data
    assert len(post_data) == 3
    assert post_data[0] == {
        "state": "success",
        "target_url": comment_html_url,
        "description": "The release notes look OK",
        "context": "sympy-bot/release-notes",
    }
    assert post_data[1].keys() == {'body'}
    error_message = post_data[1]['body']
    assert ':rotating_light:' in error_message
    assert 'ERROR' in error_message
    assert 'https://github.com/sympy/sympy-bot/issues' in error_message
    if isinstance(exception, RuntimeError):
        assert 'error message' in error_message
    else:
        assert "Command 'cmd' returned non-zero exit status 1." in error_message
    assert post_data[2] == {
        "state": "error",
        "target_url": comment_html_url,
        "description": "There was an error updating the release notes on the wiki.",
        "context": "sympy-bot/release-notes",
    }
    # Comments data
    assert patch_urls == [existing_comment_url]
    assert len(patch_data) == 1
    assert patch_data[0].keys() == {"body"}
    comment = patch_data[0]["body"]
    assert comment == release_notes_comment_body
    assert ":white_check_mark:" in comment
    assert ":x:" not in comment
    assert "new trig solvers" in comment
    assert "error" not in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    for line in valid_PR_description:
        assert line in comment
    assert "good order" in comment

    assert update_wiki_called_kwargs == {
        'wiki_url': wiki_url,
        'release_notes_file': release_notes_file,
        'changelogs': {'solvers': ['* new trig solvers']},
        'pr_number': pr_number,
        'authors': ['asmeurer', 'certik'],
    }



@parametrize('action', ['closed'])
async def test_closed_with_merging_bad_status_error(mocker, action):
    # Based on test_closed_with_merging

    update_wiki_called_kwargs = {}
    def mocked_update_wiki(*args, **kwargs):
        nonlocal update_wiki_called_kwargs
        assert not args # All args are keyword-only
        update_wiki_called_kwargs = kwargs

    mocker.patch('sympy_bot.webapp.update_wiki', mocked_update_wiki)
    mocker.patch.dict(os.environ, {"GH_AUTH": "TESTING TOKEN"})

    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': True,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
                'ref': 'master',
            },
            'body': invalid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }


    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        {
            'author': {
                'login': 'certik',
                },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        # Test commits without a login
        {
            'author': None,
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
    ]

    # Has comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'sympy-bot',
            },
            'url': existing_comment_url,
            'body': release_notes_comment_body,
        },
        {
            'user': {
                'login': 'asmeurer',
            },
            'body': "comment",
        },
        {
            'user': {
                'login': 'certik',
            },
            'body': "comment",
        },
    ]

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {}
    post = {
        statuses_url: {},
        comments_url: {
            'html_url': comment_html_url,
        },
    }

    patch = {
        existing_comment_url: {
            'html_url': comment_html_url,
            'body': release_notes_comment_body,
            'url': existing_comment_url,
        },
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post, patch=patch)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    assert set(getiter_urls) == set(getiter), getiter_urls
    assert set(getitem_urls) == set(getitem)
    assert post_urls == [statuses_url, comments_url, statuses_url]
    # Statuses data
    assert len(post_data) == 3
    assert post_data[0] == {
        "state": "failure",
        "target_url": comment_html_url,
        "description": "The release notes check failed",
        "context": "sympy-bot/release-notes",
    }
    assert post_data[1].keys() == {'body'}
    error_message = post_data[1]['body']
    assert ':rotating_light:' in error_message
    assert 'ERROR' in error_message
    assert 'https://github.com/sympy/sympy-bot/issues' in error_message
    assert "The pull request was merged even though the release notes bot had a failing status." in error_message

    assert post_data[2] == {
        "state": "error",
        "target_url": comment_html_url,
        "description": "There was an error updating the release notes on the wiki.",
        "context": "sympy-bot/release-notes",
    }
    # Comments data
    assert patch_urls == [existing_comment_url]
    assert len(patch_data) == 1
    assert patch_data[0].keys() == {"body"}
    comment = patch_data[0]["body"]
    assert ":white_check_mark:" not in comment
    assert ":x:" in comment
    assert "new trig solvers" not in comment
    assert "error" not in comment
    assert "There was an issue" in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    for line in invalid_PR_description:
        assert line in comment
    assert "good order" not in comment
    assert "No release notes were found" in comment, comment

    assert update_wiki_called_kwargs == {}


@parametrize('action', ['opened', 'reopened', 'synchronize', 'edited'])
async def test_status_bad_new_comment(action):
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': False,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
                'ref': 'master',
            },
            'body': invalid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }


    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        {
            'author': {
                'login': 'certik',
                },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        # Test commits without a login
        {
            'author': None,
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
    ]

    commit = {
        'files': [
            {
                'status': 'modified',
            },
        ],
        'parents': [
                {
                    "url": commit_url,
                    "sha": sha,
                },
        ],
    }

    # No comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'asmeurer',
            },
            'body': "comment",
        },
        {
            'user': {
                'login': 'certik',
            },
            'body': "comment",
        },
    ]

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        commit_url: commit,
    }
    post = {
        comments_url: {
            'html_url': comment_html_url,
        },
        statuses_url: {},
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    assert set(getiter_urls) == set(getiter)
    assert set(getitem_urls) == set(getitem)
    assert post_urls == [comments_url, statuses_url]
    assert len(post_data) == 2
    # Comments data
    assert post_data[0].keys() == {"body"}
    comment = post_data[0]["body"]
    assert ":white_check_mark:" not in comment
    assert ":x:" in comment
    assert "new trig solvers" not in comment
    assert "error" not in comment
    assert "There was an issue" in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    for line in invalid_PR_description:
        assert line in comment
    assert "good order" not in comment
    assert "No release notes were found" in comment
    # Statuses data
    assert post_data[1] == {
        "state": "failure",
        "target_url": comment_html_url,
        "description": "The release notes check failed",
        "context": "sympy-bot/release-notes",
    }
    assert patch_urls == []
    assert patch_data == []


@parametrize('action', ['opened', 'reopened', 'synchronize', 'edited'])
async def test_status_bad_existing_comment(action):
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': False,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
                'ref': 'master',
            },
            'body': invalid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }


    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        {
            'author': {
                'login': 'certik',
                },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        # Test commits without a login
        {
            'author': None,
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
    ]

    commit = {
        'files': [
            {
                'status': 'modified',
            },
        ],
        'parents': [
                {
                    "url": commit_url,
                    "sha": sha,
                },
        ],
    }

    # Has comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'sympy-bot',
            },
            'url': existing_comment_url,
            'body': release_notes_comment_body,
        },
        {
            'user': {
                'login': 'asmeurer',
            },
            'body': "comment",
        },
        {
            'user': {
                'login': 'certik',
            },
            'body': "comment",
        },
    ]

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        commit_url: commit,
    }
    post = {
        statuses_url: {},
    }

    patch = {
        existing_comment_url: {
            'html_url': comment_html_url,
        },
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post, patch=patch)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    assert set(getiter_urls) == set(getiter)
    assert set(getitem_urls) == set(getitem)
    assert post_urls == [statuses_url]
    # Statuses data
    assert post_data == [{
        "state": "failure",
        "target_url": comment_html_url,
        "description": "The release notes check failed",
        "context": "sympy-bot/release-notes",
    }]
    # Comments data
    assert patch_urls == [existing_comment_url]
    assert len(patch_data) == 1
    assert patch_data[0].keys() == {"body"}
    comment = patch_data[0]["body"]
    assert ":white_check_mark:" not in comment
    assert ":x:" in comment
    assert "new trig solvers" not in comment
    assert "error" not in comment
    assert "There was an issue" in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    for line in invalid_PR_description:
        assert line in comment
    assert "good order" not in comment
    assert "No release notes were found" in comment, comment


@parametrize('action', ['opened', 'reopened', 'synchronize', 'edited'])
async def test_rate_limit_comment(action):
    # Based on test_status_good_new_comment
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': False,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
                'ref': 'master',
            },
            'body': valid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }


    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        {
            'author': {
                'login': 'certik',
                },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        # Test commits without a login
        {
            'author': None,
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
    ]

    commit = {
        'files': [
            {
                'status': 'modified',
            },
        ],
        'parents': [
                {
                    "url": commit_url,
                    "sha": sha,
                },
        ],
    }

    # No comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'asmeurer',
            },
            'body': "comment",
        },
        {
            'user': {
                'login': 'certik',
            },
            "body": "comment",
        },
    ]

    version_file = {
        'content': base64.b64encode(b'__version__ = "1.2.1.dev"\n'),
        }

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        version_url: version_file,
        commit_url: commit,
    }
    post = {
        comments_url: {
            'html_url': comment_html_url,
        },
        statuses_url: {},
    }

    event = _event(event_data)

    now = datetime.datetime.now(datetime.timezone.utc)
    reset_datetime = now + datetime.timedelta(hours=1)
    rate_limit = FakeRateLimit(remaining=5, limit=1000, reset_datetime=reset_datetime)
    gh = FakeGH(getiter=getiter, getitem=getitem, post=post, rate_limit=rate_limit)

    await router.dispatch(event, gh)

    # Everything else is already tested in test_status_good_new_comment()
    # above
    post_urls = gh.post_urls
    post_data = gh.post_data
    assert post_urls == [comments_url, statuses_url, comments_url]
    assert len(post_data) == 3
    assert post_data[2].keys() == {"body"}
    comment = post_data[2]["body"]
    assert ":warning:" in comment
    assert "5" in comment
    assert "1000" in comment
    assert str(reset_datetime) in comment


@parametrize('action', ['opened', 'reopened', 'synchronize', 'edited'])
async def test_header_in_message(action):
    # Based on test_status_good_new_comment
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': False,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
                'ref': 'master',
            },
            'body': valid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }

    sha_1 = '174b8b37bc33e9eb29e710a233190d02a13bdb54'
    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': """
<!-- BEGIN RELEASE NOTES -->
* solvers
  * solver change
<!-- END RELEASE NOTES -->
"""
            },
            'sha': sha_1,
            'url': commit_url_template.format(sha=sha_1)
        },
        {
            'author': {
                'login': 'certik',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        # Test commits without a login
        {
            'author': None,
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
    ]

    commit = {
        'files': [
            {
                'status': 'modified',
            },
        ],
        'parents': [
                {
                    "url": commit_url,
                    "sha": sha,
                },
        ],
    }

    # No comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'asmeurer',
            },
            'body': "comment",
        },
        {
            'user': {
                'login': 'certik',
            },
            'body': "comment",
        },
    ]

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        commit_url: commit,
        commit_url_template.format(sha=sha_1): commit,
    }
    post = {
        comments_url: {
            'html_url': comment_html_url,
        },
        statuses_url: {},
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    # The rest is already tested in test_status_good_new_comment
    assert set(getiter_urls) == set(getiter)
    assert set(getitem_urls) == set(getitem)
    assert post_urls == [comments_url, statuses_url]
    assert len(post_data) == 2
    # Comments data
    assert post_data[0].keys() == {"body"}
    comment = post_data[0]["body"]
    assert ":white_check_mark:" not in comment
    assert ":x:" in comment
    assert "error" not in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    assert "good order" not in comment
    assert sha_1 in comment
    assert "<!-- BEGIN RELEASE NOTES -->" in comment
    assert "<!-- END RELEASE NOTES -->" in comment
    # Statuses data
    assert post_data[1] == {
        "state": "failure",
        "target_url": comment_html_url,
        "description": "The release notes check failed",
        "context": "sympy-bot/release-notes",
    }
    assert patch_urls == []
    assert patch_data == []


@parametrize('action', ['opened', 'reopened', 'synchronize', 'edited'])
async def test_bad_version_file(action):
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': False,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
                'ref': 'master',
            },
            'body': valid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }


    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        {
            'author': {
                'login': 'certik',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        # Test commits without a login
        {
            'author': None,
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
    ]

    commit = {
        'files': [
            {
                'status': 'modified',
            },
        ],
        'parents': [
                {
                    "url": commit_url,
                    "sha": sha,
                },
        ],
    }

    # No comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'asmeurer',
            },
        },
        {
            'user': {
                'login': 'certik',
            },
        },
    ]

    version_file = {
        'content': base64.b64encode(b'\n'),
        }

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        version_url: version_file,
        commit_url: commit,
    }
    post = {
        comments_url: {
            'html_url': comment_html_url,
        },
        statuses_url: {},
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    assert set(getiter_urls) == set(getiter)
    assert set(getitem_urls) == set(getitem)
    assert post_urls == [comments_url, statuses_url]
    assert len(post_data) == 2
    # Comments data
    assert post_data[0].keys() == {"body"}
    comment = post_data[0]["body"]
    assert ":white_check_mark:" not in comment
    assert ":x:" in comment
    assert "error" in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    assert "sympy/release.py" in comment
    assert "There was an error getting the version" in comment
    assert "https://github.com/sympy/sympy-bot/issues" in comment
    for line in valid_PR_description:
        assert line in comment
    assert "good order" not in comment
    # Statuses data
    assert post_data[1] == {
        "state": "error",
        "target_url": comment_html_url,
        "description": "The release notes check failed",
        "context": "sympy-bot/release-notes",
    }
    assert patch_urls == []
    assert patch_data == []


@parametrize('action', ['opened', 'reopened', 'synchronize', 'edited'])
@parametrize('include_extra', [True, False])
async def test_no_user_logins_in_commits(action, include_extra):
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': False,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
                'ref': 'master',
            },
            'body': valid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }


    commits = [
        {
            'author': None,
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
    ]

    commit = {
        'files': [
            {
                'status': 'modified',
            },
        ],
        'parents': [
                {
                    "url": commit_url,
                    "sha": sha,
                },
        ],
    }

    if include_extra:
        commits += [
            {
                'author': {
                    'login': 'certik',
                },
                'commit': {
                    'message': "A good commit",
                },
                'sha': sha,
                'url': commit_url,
            },
        ]

    # No comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'asmeurer',
            },
            'body': "comment",
        },
        {
            'user': {
                'login': 'certik',
            },
            'body': "comment",
        },
    ]

    version_file = {
        'content': base64.b64encode(b'__version__ = "1.2.1.dev"\n'),
        }

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        version_url: version_file,
        commit_url: commit,
    }
    post = {
        comments_url: {
            'html_url': comment_html_url,
        },
        statuses_url: {},
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    assert set(getiter_urls) == set(getiter)
    assert set(getitem_urls) == set(getitem)
    assert post_urls == [comments_url, statuses_url]
    assert len(post_data) == 2
    # Comments data
    assert post_data[0].keys() == {"body"}
    comment = post_data[0]["body"]
    assert ":white_check_mark:" in comment
    assert ":x:" not in comment
    assert "new trig solvers" in comment
    assert "error" not in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    for line in valid_PR_description:
        assert line in comment
    assert "good order" in comment
    assert "@asmeurer" in comment
    if include_extra:
        assert "@certik" in comment
    # Statuses data
    assert post_data[1] == {
        "state": "success",
        "target_url": comment_html_url,
        "description": "The release notes look OK",
        "context": "sympy-bot/release-notes",
    }
    assert patch_urls == []
    assert patch_data == []

@parametrize('action', ['opened', 'reopened', 'synchronize', 'edited'])
async def test_status_good_new_comment_other_base(action):
    # Based on test_status_good_new_comment
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': False,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
                'ref': '1.4',
            },
            'body': valid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }


    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        {
            'author': {
                'login': 'certik',
            },
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
        # Test commits without a login
        {
            'author': None,
            'commit': {
                'message': "A good commit",
            },
            'sha': sha,
            'url': commit_url,
        },
    ]

    commit = {
        'files': [
            {
                'status': 'modified',
            },
        ],
        'parents': [
                {
                    "url": commit_url,
                    "sha": sha,
                },
        ],
    }

    # No comment from sympy-bot
    comments = [
        {
            'user': {
                'login': 'asmeurer',
            },
        },
        {
            'user': {
                'login': 'certik',
            },
        },
    ]

    version_file = {
        'content': base64.b64encode(b'__version__ = "1.4rc1"\n'),
        }

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        version_url_template.format(ref='1.4'): version_file,
        commit_url: commit,
    }
    post = {
        comments_url: {
            'html_url': comment_html_url,
        },
        statuses_url: {},
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    assert set(getiter_urls) == set(getiter)
    assert set(getitem_urls) == set(getitem)
    assert post_urls == [comments_url, statuses_url]
    assert len(post_data) == 2
    # Comments data
    assert post_data[0].keys() == {"body"}
    comment = post_data[0]["body"]
    assert ":white_check_mark:" in comment
    assert ":x:" not in comment
    assert "new trig solvers" in comment
    assert "error" not in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    assert '1.2.1' not in comment
    assert '1.4' in comment
    for line in valid_PR_description:
        assert line in comment
    assert "good order" in comment
    # Statuses data
    assert post_data[1] == {
        "state": "success",
        "target_url": comment_html_url,
        "description": "The release notes look OK",
        "context": "sympy-bot/release-notes",
    }
    assert patch_urls == []
    assert patch_data == []

@parametrize('action', ['opened', 'reopened', 'synchronize', 'edited'])
async def test_added_deleted_new_comment(action):
    # Based on test_status_good_existing_comment
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': False,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
                'ref': 'master',
            },
            'body': valid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }

    sha_merge = '61697bd7249381b27a4b5d449a8061086effd381'
    sha_1 = '174b8b37bc33e9eb29e710a233190d02a13bdb54'
    sha_2 = 'aef484a1d46bb5389f1709d78e39126d9cb8599f'
    sha_3 = sha

    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "Merge"
            },
            'sha': sha_merge,
            'url': commit_url_template.format(sha=sha_merge)
        },
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "Adds file1"
            },
            'sha': sha_1,
            'url': commit_url_template.format(sha=sha_1)
        },
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "Modifies file1",
            },
            'sha': sha_2,
            'url': commit_url_template.format(sha=sha_2),
        },
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "Deletes file1",
            },
            'sha': sha_3,
            'url': commit_url_template.format(sha=sha_3),
        },
    ]

    commit_merge = {
        'sha': sha_1,
        'files': [
            {
                'filename': 'file1',
                'status': 'added',
            },
            {
                'filename': 'file2',
                'status': 'deleted',
            },
        ],
        'parents': [
                {
                    "url": commit_url,
                    "sha": sha_2,
                },
                {
                    "url": commit_url,
                    "sha": sha,
                },
        ],
    }

    commit_add = {
        'sha': sha_1,
        'files': [
            {
                'filename': 'file1',
                'status': 'added',
            },
        ],
        'parents': [
                {
                    "url": commit_url,
                    "sha": sha,
                },
        ],
    }

    commit_modify = {
        'sha': sha_2,
        'files': [
            {
                'filename': 'file1',
                'status': 'modified',
            },
        ],
        'parents': [
                {
                    "url": commit_url,
                    "sha": sha,
                },
        ],
    }

    commit_delete = {
        'sha': sha_3,
        'files': [
            {
                'filename': 'file1',
                'status': 'removed',
            },
        ],
        'parents': [
                {
                    "url": commit_url,
                    "sha": sha,
                },
        ],
    }

    comments = [
        {
            'user': {
                'login': 'sympy-bot',
            },
            'url': existing_comment_url,
            'body': release_notes_comment_body,
        },
        {
            'user': {
                'login': 'asmeurer',
            },
            'body': "comment",
        },
        {
            'user': {
                'login': 'certik',
            },
            'body': "comment",
        },
    ]

    version_file = {
        'content': base64.b64encode(b'__version__ = "1.2.1.dev"\n'),
    }

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        commit_url_template.format(sha=sha_merge): commit_merge,
        commit_url_template.format(sha=sha_1): commit_add,
        commit_url_template.format(sha=sha_2): commit_modify,
        commit_url_template.format(sha=sha_3): commit_delete,
        version_url: version_file,
    }
    post = {
        comments_url: {
            'html_url': comment_html_url,
        },
        statuses_url: {},
    }
    patch = {
        existing_comment_url: {
            'html_url': comment_html_url,
        },
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post, patch=patch)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls

    # The rest is already tested in test_status_good_new_comment
    assert set(getiter_urls) == set(getiter)
    assert set(getitem_urls) == set(getitem)
    assert post_urls == [statuses_url, comments_url]
    assert patch_urls == [existing_comment_url]
    assert len(post_data) == 2
    # Comments data
    assert post_data[1].keys() == {"body"}
    comment = post_data[1]["body"]
    assert ":white_check_mark:" not in comment
    assert ":x:" not in comment
    assert "\U0001f7e0" in comment
    assert "error" not in comment
    assert "add new files" in comment
    assert "delete files" in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    assert sha_1 in comment
    assert sha_2 not in comment
    assert sha_3 in comment
    assert sha_merge not in comment
    assert "`file1`" in comment
    assert "<!-- BEGIN RELEASE NOTES -->" not in comment
    assert "<!-- END RELEASE NOTES -->" not in comment


@parametrize('action', ['opened', 'reopened', 'synchronize', 'edited'])
async def test_added_deleted_existing_comment(action):
    # Based on test_status_good_existing_comment
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': False,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
                'ref': 'master',
            },
            'body': valid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }

    sha_merge = '61697bd7249381b27a4b5d449a8061086effd381'
    sha_1 = '174b8b37bc33e9eb29e710a233190d02a13bdb54'
    sha_2 = 'aef484a1d46bb5389f1709d78e39126d9cb8599f'
    sha_3 = sha

    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "Merge"
            },
            'sha': sha_merge,
            'url': commit_url_template.format(sha=sha_merge)
        },
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "Adds file1"
            },
            'sha': sha_1,
            'url': commit_url_template.format(sha=sha_1)
        },
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "Modifies file1",
            },
            'sha': sha_2,
            'url': commit_url_template.format(sha=sha_2),
        },
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "Deletes file1",
            },
            'sha': sha_3,
            'url': commit_url_template.format(sha=sha_3),
        },
    ]

    commit_merge = {
        'sha': sha_1,
        'files': [
            {
                'filename': 'file1',
                'status': 'added',
            },
            {
                'filename': 'file2',
                'status': 'deleted',
            },
        ],
        'parents': [
                {
                    "url": commit_url,
                    "sha": sha_2,
                },
                {
                    "url": commit_url,
                    "sha": sha,
                },
        ],
    }

    commit_add = {
        'sha': sha_1,
        'files': [
            {
                'filename': 'file1',
                'status': 'added',
            },
        ],
        'parents': [
                {
                    "url": commit_url,
                    "sha": sha,
                },
        ],
    }

    commit_modify = {
        'sha': sha_2,
        'files': [
            {
                'filename': 'file1',
                'status': 'modified',
            },
        ],
        'parents': [
                {
                    "url": commit_url,
                    "sha": sha,
                },
        ],
    }

    commit_delete = {
        'sha': sha_3,
        'files': [
            {
                'filename': 'file1',
                'status': 'removed',
            },
        ],
        'parents': [
                {
                    "url": commit_url,
                    "sha": sha,
                },
        ],
    }

    comments = [
        {
            'user': {
                'login': 'sympy-bot',
            },
            'url': existing_comment_url,
            'body': release_notes_comment_body,
        },
        {
            'user': {
                'login': 'sympy-bot',
            },
            'url': existing_added_deleted_comment_url,
            'body': added_deleted_comment_body,
        },
        {
            'user': {
                'login': 'asmeurer',
            },
            'body': "comment",
        },
        {
            'user': {
                'login': 'certik',
            },
            'body': "comment",
        },
    ]

    version_file = {
        'content': base64.b64encode(b'__version__ = "1.2.1.dev"\n'),
    }

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        commit_url_template.format(sha=sha_merge): commit_merge,
        commit_url_template.format(sha=sha_1): commit_add,
        commit_url_template.format(sha=sha_2): commit_modify,
        commit_url_template.format(sha=sha_3): commit_delete,
        version_url: version_file,
    }
    post = {
        comments_url: {
            'html_url': comment_html_url,
        },
        statuses_url: {},
    }
    patch = {
        existing_comment_url: {
            'html_url': comment_html_url,
        },
        existing_added_deleted_comment_url: {
            'html_url': comment_html_url2,
        },
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post, patch=patch)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data

    assert set(getiter_urls) == set(getiter)
    assert set(getitem_urls) == set(getitem)
    assert post_urls == [statuses_url]
    assert patch_urls == list(patch)
    assert len(post_data) == 1
    assert len(patch_data) == 2
    # Comments data.
    assert patch_data[1].keys() == {"body"}
    comment = patch_data[1]["body"]
    assert ":white_check_mark:" not in comment
    assert ":x:" not in comment
    assert "\U0001f7e0" in comment
    assert "error" not in comment
    assert "add new files" in comment
    assert "delete files" in comment
    assert "https://github.com/sympy/sympy-bot" in comment
    assert sha_1 in comment
    assert sha_2 not in comment
    assert sha_3 in comment
    assert sha_merge not in comment
    assert "`file1`" in comment
    assert "<!-- BEGIN RELEASE NOTES -->" not in comment
    assert "<!-- END RELEASE NOTES -->" not in comment

@parametrize('action', ['opened', 'reopened', 'synchronize', 'edited'])
async def test_added_deleted_remove_existing_comment(action):
    # Based on test_status_good_existing_comment
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'open',
            'merged': False,
            'comments_url': comments_url,
            'commits_url': commits_url,
            'head': {
                'user': {
                    'login': 'asmeurer',
                    },
            },
            'base': {
                'repo': {
                    'contents_url': contents_url,
                    'html_url': html_url,
                },
                'ref': 'master',
            },
            'body': valid_PR_description,
            'statuses_url': statuses_url,
        },
        'action': action,
    }

    commits = [
        {
            'author': {
                'login': 'asmeurer',
            },
            'commit': {
                'message': "Modifies file1"
            },
            'sha': sha,
            'url': commit_url,
        },
    ]

    commit = {
        'sha': sha,
        'files': [
            {
                'filename': 'file1',
                'status': 'modified',
            },
        ],
        'parents': [
                {
                    "url": commit_url,
                    "sha": sha,
                },
        ],
    }

    comments = [
        {
            'user': {
                'login': 'sympy-bot',
            },
            'url': existing_comment_url,
            'body': release_notes_comment_body,
        },
        {
            'user': {
                'login': 'sympy-bot',
            },
            'url': existing_added_deleted_comment_url,
            'body': added_deleted_comment_body,
        },
        {
            'user': {
                'login': 'asmeurer',
            },
            'body': "comment",
        },
        {
            'user': {
                'login': 'certik',
            },
            'body': "comment",
        },
    ]

    version_file = {
        'content': base64.b64encode(b'__version__ = "1.2.1.dev"\n'),
    }

    getiter = {
        commits_url: commits,
        comments_url: comments,
    }

    getitem = {
        commit_url: commit,
        version_url: version_file,
    }
    post = {
        comments_url: {
            'html_url': comment_html_url,
        },
        statuses_url: {},
    }
    patch = {
        existing_comment_url: {
            'html_url': comment_html_url,
        },
    }
    delete = {
        existing_added_deleted_comment_url: {
            'html_url': comment_html_url2,
        },
    }

    event = _event(event_data)

    gh = FakeGH(getiter=getiter, getitem=getitem, post=post, patch=patch, delete=delete)

    await router.dispatch(event, gh)

    getitem_urls = gh.getitem_urls
    getiter_urls = gh.getiter_urls
    post_urls = gh.post_urls
    post_data = gh.post_data
    patch_urls = gh.patch_urls
    patch_data = gh.patch_data
    delete_urls = gh.delete_urls

    assert set(getiter_urls) == set(getiter)
    assert set(getitem_urls) == set(getitem)
    assert post_urls == [statuses_url]
    assert patch_urls == list(patch)
    assert delete_urls == list(delete)
    assert len(post_data) == 1
    assert len(patch_data) == 1
    # Comments data
    assert patch_data[0].keys() == {"body"}
    comment = patch_data[0]["body"]
    assert "release notes" in comment
    assert "\U0001f7e0" not in comment
    assert "add new files" not in comment
    assert "delete files" not in comment
    assert sha not in comment
    assert "`file1`" not in comment
