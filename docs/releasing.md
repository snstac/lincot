# Releasing

Releases are built and published by `.github/workflows/ci.yml` when a tag is
pushed. The same workflow can be run by hand as a **dry run**.

## What a tag push does

| Job | Runs on | Publishes |
|-----|---------|-----------|
| `test` | every push, PR, dispatch | no |
| `build-dist` (sdist + wheel, `twine check --strict`, VERSION check) | every push, PR, dispatch | no |
| `package-deb`, `package-rpm` | tag push, dispatch | no |
| `package-pypi` | **tag push only** | PyPI |
| `release` (GitHub Release with `.deb`/`.rpm`) | **tag push only** | GitHub Releases |

On a tag push `build-dist` fails if the tag (minus a leading `v`) does not
match `src/lincot/VERSION`, so a mismatched tag never reaches PyPI.

## Dry run

Actions → **CI** → **Run workflow**, pick a branch or tag. The run tests,
builds the sdist, wheel, `.deb` and `.rpm`, uploads them as workflow artifacts
and lists them in the run summary. Nothing is published:

- the publishing jobs are gated on `github.event_name == 'push'` as well as a
  tag ref, so a dispatch started *from a tag* still skips them;
- the workflow token is `contents: read` by default; only the two publishing
  jobs are granted `id-token: write` / `contents: write`.

`tests/test_ci_workflow.py` enforces both rules.

## PyPI trusted publishing (one-time setup)

`package-pypi` authenticates to PyPI with OIDC trusted publishing; there is no
API token in the repository. PyPI accepts the upload only if the `lincot`
project has a trusted publisher whose claims match the workflow exactly:

| PyPI field | Value |
|------------|-------|
| Owner | `snstac` |
| Repository name | `lincot` |
| Workflow name | `ci.yml` |
| Environment name | `pypi` |

A PyPI owner of `lincot` adds this under *Your projects → lincot → Publishing
→ Add a new publisher → GitHub*. The repository also needs a GitHub
environment named `pypi` (Settings → Environments).

Without that registration the job fails with:

```
Trusted publishing exchange failure ... `invalid-publisher`: valid token,
but no corresponding publisher (Publisher with matching claims was not found)
```

That is why every tag from v1.2.0 to v1.3.9 failed in *Publish to PyPI*
while tests, the `.deb`/`.rpm` builds and the GitHub Release all succeeded, and
why PyPI still shows 1.0.3. Renaming `ci.yml` or the `pypi` environment
reintroduces this failure.

After the publisher is registered, re-run the failed **Publish to PyPI** job
on the existing tag run; no new tag is needed.

## Cutting a release

1. Update `src/lincot/VERSION` and `CHANGELOG.md` on `main`.
2. Optionally run the dry run on `main` and inspect the artifacts.
3. Tag the commit `vX.Y.Z` (matching VERSION) and push the tag.
