# codeforlife-package-python

This repo contains CFL's python package. This will be installed into all backend services.

## LICENCE

In accordance with the [Terms of Use](https://www.codeforlife.education/terms#terms)
of the Code for Life website, all copyright, trademarks, and other
intellectual property rights in and relating to Code for Life (including all
content of the Code for Life website, the Rapid Router application, the
Kurono application, related software (including any drawn and/or animated
avatars, whether such avatars have any modifications) and any other games,
applications or any other content that we make available from time to time) are
owned by Ocado Innovation Limited.

The source code of the Code for Life portal, the Rapid Router application
and the Kurono/aimmo application are [licensed under the GNU Affero General
Public License](https://github.com/codeforlife-education/codeforlife-workspace/blob/main/LICENSE.md).
All other assets including images, logos, sounds etc., are not covered by
this licence and no-one may copy, modify, distribute, show in public or
create any derivative work from these assets.

## Installation

To install this package, do one of the following options.

Make sure to:

1. install the package with the required python version.
1. replace the [package version number](https://pypi.org/project/codeforlife/#history) ("0.0.0") with the same value for both the production and development dependencies or you'll get conflict errors.

**Option 1:** Run both `pipenv install` commands:

```bash
# Install as a production dependency.
pipenv install codeforlife==0.0.0

# Install as a development dependency.
pipenv install --dev codeforlife[dev]==0.0.0
```

**Option 2:** Add a row to `[packages]` and `[dev-packages]` in `Pipfile`:

```toml
[packages]
codeforlife = "==0.0.0"

[dev-packages]
codeforlife = {version = "==0.0.0", extras = ["dev"]}
```

### Installing a GitHub Branch

You may wish to install and integrate your changes into a CFL backend before it's been peer-reviewed.

Make sure to:

1. replace the branch name ("BRANCH_HERE") with the same value for both the production and development dependencies or you'll get conflict errors.
1. replace the organization name ("ORG_HERE") with the same value for both the production and development dependencies or you'll get conflict errors.

```toml
[packages]
codeforlife = {ref = "BRANCH_HERE", git = "https://github.com/ORG_HERE/codeforlife-package-python.git"}

[dev-packages]
codeforlife = {ref = "BRANCH_HERE", git = "https://github.com/ORG_HERE/codeforlife-package-python.git", extras = ["dev"]}
```

## Version Release

New versions of this package are automatically created by [this](.github/workflows/main.yml) GitHub Actions workflow.

Versions are determined using the [semantic-release commit message format](https://semantic-release.gitbook.io/semantic-release/#commit-message-format).

If a new version is successfully released, it will create:

1. A new tag [on GitHub](https://github.com/codeforlife-education/codeforlife-package-python/tags).
1. A new release [on GitHub](https://github.com/codeforlife-education/codeforlife-package-python/releases).
1. A new release [on PyPI](https://pypi.org/project/codeforlife/#history).
