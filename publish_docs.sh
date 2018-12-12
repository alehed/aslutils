#!/bin/sh

if git status | grep "Untracked" > /dev/null ; then
    echo "Untracked files present in repository, please remove or ignore them first."
    exit 1
fi

source env/bin/activate

git stash

sphinx-build -b html docs/source docs/build

COMMIT=`git rev-parse HEAD`

git checkout gh-pages

cp -rT docs/build/ .
git add -A
git commit -m "Documentation build for $COMMIT"
git push origin gh-pages

git checkout master
git stash pop
