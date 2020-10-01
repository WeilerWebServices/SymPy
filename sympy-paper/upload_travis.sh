set +x
if [ "${GH_TOKEN}" = "" ]; then
    echo "PDF not uploading because this is a PR from a fork"
    exit 0
fi
set -x

export commit_id=`git log -1 --pretty=format:"%H"`

git config --global push.default simple
git config --global user.name "Isuru Fernando"
git config --global user.email "isuruf@gmail.com"

set +x
git clone "https://${GH_TOKEN}@github.com/isuruf-bot/sympy-paper.git" upload -q
set -x

cd upload
#git checkout -b pdfs --track origin/pdfs;

if [ "${TRAVIS_PULL_REQUEST}" = "false" ]; then
    export name=paper-${TRAVIS_BRANCH}.pdf
    export namesupplement=paper-${TRAVIS_BRANCH}-supplement.pdf
    export namediff=paper-diff-${TRAVIS_BRANCH}.pdf
    export namediffsupplement=paper-diff-${TRAVIS_BRANCH}-supplement.pdf
    export msg="Upload for branch ${TRAVIS_BRANCH} - ${commit_id}"
else
    export name=paper-${TRAVIS_PULL_REQUEST}.pdf
    export namesupplement=paper-${TRAVIS_PULL_REQUEST}-supplement.pdf
    export namediff=paper-diff-${TRAVIS_PULL_REQUEST}.pdf
    export namediffsupplement=paper-diff-${TRAVIS_PULL_REQUEST}-supplement.pdf
    export msg="Upload for sympy/sympy-paper#${TRAVIS_PULL_REQUEST} - ${commit_id}"
fi

mv ../paper.pdf ${name}
mv ../supplement.pdf ${namesupplement}
mv ../paper-diff.pdf ${namediff}
mv ../supplement-diff.pdf ${namediffsupplement}
git add ${name}
git add ${namesupplement}
git add ${namediff}
git add ${namediffsupplement}
git commit -m "${msg} - [skip ci]."

PUSH_COUNTER=0
until git push -q > /dev/null 2>&1
do
    git fetch origin pdfs > /dev/null 2>&1
    git reset --hard origin/pdfs > /dev/null 2>&1
    mv ../paper.pdf ${name}
    git add ${name}
    git commit -m "${msg} - [skip ci]."

    PUSH_COUNTER=$((PUSH_COUNTER + 1))
    if [ "$PUSH_COUNTER" -gt 3 ]; then
        echo "Push failed, aborting."
        exit 1
    fi
done

#export payload='{"state":"success","target_url":"https://github.com/isuruf-bot/sympy-paper/blob/pdfs/'${name}'","description":"Pdf uploading succeeded!","context":"continuous-integration/latex-pdf"}'

#set +x
#curl -X POST -H "Content-Type: application/json" -d '$payload' https://api.github.com/repos/sympy/sympy-paper/statuses/${commit_id}?access_token=${GH_TOKEN}
#set -x
