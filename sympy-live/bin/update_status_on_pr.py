"""
This script runs only on travis to create the status for the latest commit
in the PR.

Reference: https://developer.github.com/v3/repos/statuses/#create-a-status
"""
import os
import requests

GAE_PROJECT_NAME = 'sympy-live-hrd'
GITHUB_REPO = 'sympy/sympy-live'
GITHUB_API_URL = 'https://api.github.com'
GITHUB_API_REF_URL = "%s/repos/%s/git/matching-refs/heads/" % (GITHUB_API_URL, GITHUB_REPO)
GITHUB_API_UPDATE_STATUS_URL = "%s/repos/%s/statuses/" % (GITHUB_API_URL, GITHUB_REPO)
SYMPY_BOT_TOKEN_VAR = 'SYMPY_BOT_TOKEN'


def get_branch_commit_sha(branch_name):
    """Gets the SHA of the last commit of the given branch
    :param branch_name: str name of branch on Github
    :return: str SHA
    """
    response = requests.get(GITHUB_API_REF_URL + branch_name)
    response.raise_for_status()
    return response.json()[0]['object']['sha']


def update_pr_status_with_deployment(branch_name, commit_sha):
    """Updates the Status of the commit identified by commit SHA, which is reflected
    at the bottom of the PR, above merge button.
    :param branch_name: str name of branch on github
    :param commit_sha: str SHA
    :return: Response POST request to Github API
    """
    sympy_bot_token = os.environ.get(SYMPY_BOT_TOKEN_VAR)
    deployment_url = "https://%s-dot-%s.appspot.com" % (branch_name, GAE_PROJECT_NAME)
    payload = {
        "state": "success",
        "target_url": deployment_url,
        "description": "Deployed to version: %s" % branch_name,
        "context": "PR Deployment"
    }

    headers = {
        'Authorization': 'Bearer %s' % sympy_bot_token,
        'Content-Type': 'application/json'
    }

    update_status_url = GITHUB_API_UPDATE_STATUS_URL + commit_sha
    print "Update status URL: %s" % update_status_url
    response = requests.post(update_status_url, headers=headers, json=payload)
    print "Response: %s" % response.json()


def main():
    is_on_travis = os.environ.get('TRAVIS')
    if not is_on_travis:
        raise ValueError('This script run only on travis!')
    branch_name = os.environ.get('TRAVIS_BRANCH')
    commit_sha = get_branch_commit_sha(branch_name)
    print "Branch name: %s Commit SHA: %s" % (branch_name, commit_sha)
    print "Creating commit status ..."
    update_pr_status_with_deployment(branch_name, commit_sha)


if __name__ == '__main__':
    main()
