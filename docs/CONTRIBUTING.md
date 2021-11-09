# Contributing Guide

## How to contribute

In order to contribute effectively we provide guidelines to address common case for contributions. Presently we have guides for the following type of changes.

* Request For Change (RFC) / Feature Request: These are suggestions / requests for features this library currently does not have. The team evaluates these requests for adequacy / relevance / capacity and overall architectural consistency.
* Bug Reports: This are reports of non compliant behavior with this library's specification and other blatantly wrong behavior.

In addition to contributing in the form of Bug Reports and RFCs it is also possible to contribute directly in code with a Pull Request (PR). In the case of a Pull Request you should also indicate the nature of the Pull Request (Feature/Bug/etc.) to help the team asses the Pull Request. If you are enthusiastic about a particular Feature being added or a bug being fixed, a PR is often the quickest way to promote your change as the team does not have to allocate as much resources to process the contribution.

In the case of PRs it is often best to consult with the owner team before embarking on a PR, specially if it's a beefy one. Spending time on a PR that might later be rejected because major discrepancies with vision or competing contributions is an uncomfortable outcome for all involved people.

## Request For Change / Feature Request

Generally speaking an RFC is needed when you want to add a new component or change an existing one in an incompatible way that might result in a major version bump.

Though it seems a little bureaucratic, the process is in place in order to avoid frustration of a potential contributor by making the discussions take place before any code is written. Once the design and direction is fully agreed then the contributor can work peacefully knowing that their change will be committed.

As of this moment all you need to do is create an issue and use the [Feature Request Template](https://github.com/mercadolibre/ubatch/blob/master/.github/ISSUE_TEMPLATE/feature_request.md).

Please prepend your issue title with `[RFC]` so that's easier to filter.

## Bug Reports

Bugs are a reality in software. We can't fix what we don't know about, so please report liberally. If you're not sure if something is a bug or not, feel free to file it anyway.

Before reporting a bug, please search existing issues and pull requests, as it's possible that someone else has already reported your error. In the off case that you find your issue as fixed/closed, please add a reference to it on your new one.

Your issue should contain a title and a clear description of the issue. You should also include as much relevant information as possible and a code sample that demonstrates the issue. The goal of a bug report is to make it easy for yourself - and others - to replicate the bug and develop a fix.

Opening an issue is as easy as following [this link](https://github.com/mercadolibre/ubatch/issues/new) and filling out the given template.

Bug reports may also be sent in the form of a [pull request](#pull-request) containing a failing test.

## Pull Request

We use the "fork and pull" model [described here](https://help.github.com/articles/about-collaborative-development-models/), where contributors push changes to their personal fork and create pull requests to bring those changes into the source repository.

Your basic steps to get going:

* Fork this repository and create a branch from master for the issue you are working on.
* Commit as you go following our git conventions.
* Include tests that cover all non-trivial code. The existing tests should provide a template on how to test correctly.
* Make sure every test passes.
* Push your commits to GitHub and create a pull request against the corresponding component master branch.

If taking too much time to deliver code, **always** [rebase](https://git-scm.com/docs/git-rebase) towards `master` before asking for a review, and avoid reverse merge commits. We **HATE** reverse merge commits (they make git history tree a mess) and will reject contributions that have them.

### Installation

Install poetry

```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```

Clone repository

```bash
git clone git@github.com:mercadolibre/ubatch.git
```

Start shell and install dependencies

```bash
cd ubatch
poetry shell
poetry install
```

Run tests

```bash
pytest
```

Building docs

```bash
cd ubatch/docs
poetry shell
make html
```
