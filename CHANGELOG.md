# CHANGELOG


## v0.1.5 (2025-02-03)

### Bug Fixes

- **mesh**: Invert the z orientation
  ([`c3dacbb`](https://github.com/brendanjmeade/parsli/commit/c3dacbbda4a30f99a73f67b07c14d81d7e0ae4d3))


## v0.1.4 (2025-01-31)

### Bug Fixes

- **proj**: Allow to toggle projection
  ([`7d2ca55`](https://github.com/brendanjmeade/parsli/commit/7d2ca5546a09222edb9c4a3d7b9629cd348c38ae))


## v0.1.3 (2025-01-31)

### Bug Fixes

- **segment**: Proper location, depth and field association
  ([`63343cc`](https://github.com/brendanjmeade/parsli/commit/63343cc745b3567cb6515edfedd6a640b08d9525))

### Documentation

- **README**: Update url to picture
  ([`d2caf3a`](https://github.com/brendanjmeade/parsli/commit/d2caf3a960927309e36f1d4a5fe9d28c704d7f03))

- **README**: Use 1 line for badges
  ([`b014b71`](https://github.com/brendanjmeade/parsli/commit/b014b71374206a4ee1e30331d51d20fa6ab31510))


## v0.1.2 (2025-01-28)

### Bug Fixes

- **ci**: Publish to proper pypi
  ([`90db78c`](https://github.com/brendanjmeade/parsli/commit/90db78c03993010acc45b60af9a10594c29cb171))

### Continuous Integration

- Ignore changelog formatting
  ([`4eaf793`](https://github.com/brendanjmeade/parsli/commit/4eaf79347d658ab8ec91f588c1ed36e1f4d7f5a1))


## v0.1.1 (2025-01-28)

### Bug Fixes

- **segment**: Use fix depth for now
  ([`a68fb3b`](https://github.com/brendanjmeade/parsli/commit/a68fb3b3402e3a029caad5e2c0611f3608ab833b))

### Build System

- **deps**: Bump the actions group across 1 directory with 3 updates
  ([`984e640`](https://github.com/brendanjmeade/parsli/commit/984e640d422afe5cafa6947a0117462b23afebe6))

Bumps the actions group with 3 updates in the / directory:
  [codecov/codecov-action](https://github.com/codecov/codecov-action),
  [python-semantic-release/python-semantic-release](https://github.com/python-semantic-release/python-semantic-release)
  and [actions/attest-build-provenance](https://github.com/actions/attest-build-provenance).

Updates `codecov/codecov-action` from 5.1.2 to 5.3.1 - [Release
  notes](https://github.com/codecov/codecov-action/releases) -
  [Changelog](https://github.com/codecov/codecov-action/blob/main/CHANGELOG.md) -
  [Commits](https://github.com/codecov/codecov-action/compare/v5.1.2...v5.3.1)

Updates `python-semantic-release/python-semantic-release` from 9.15.2 to 9.17.0 - [Release
  notes](https://github.com/python-semantic-release/python-semantic-release/releases) -
  [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.rst)
  -
  [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.15.2...v9.17.0)

Updates `actions/attest-build-provenance` from 2.1.0 to 2.2.0 - [Release
  notes](https://github.com/actions/attest-build-provenance/releases) -
  [Changelog](https://github.com/actions/attest-build-provenance/blob/main/RELEASE.md) -
  [Commits](https://github.com/actions/attest-build-provenance/compare/v2.1.0...v2.2.0)

--- updated-dependencies: - dependency-name: codecov/codecov-action dependency-type:
  direct:production

update-type: version-update:semver-minor

dependency-group: actions

- dependency-name: python-semantic-release/python-semantic-release dependency-type:
  direct:production

- dependency-name: actions/attest-build-provenance dependency-type: direct:production

...

Signed-off-by: dependabot[bot] <support@github.com>

### Continuous Integration

- Test_and_release.yml add environment
  ([`09ede87`](https://github.com/brendanjmeade/parsli/commit/09ede87677b20f7a99cecacb5c67a7501650b6c2))

### Documentation

- **readme**: Add dev setup info
  ([`869786b`](https://github.com/brendanjmeade/parsli/commit/869786b072d0db08838082a87275d11a199f1d94))


## v0.1.0 (2025-01-22)

### Continuous Integration

- Remove pylint
  ([`0b21105`](https://github.com/brendanjmeade/parsli/commit/0b211053d3c3d6f87b334300eeca532dc7f44d77))

- Try to fix it
  ([`74ffc4d`](https://github.com/brendanjmeade/parsli/commit/74ffc4d477f0840e7f47c0f6071b4319a8844ace))

- Try to fix publication
  ([`7df722c`](https://github.com/brendanjmeade/parsli/commit/7df722c2b73795a9ab3225fcfde08987c4f5ced2))

- Try to simplify
  ([`3ef22c5`](https://github.com/brendanjmeade/parsli/commit/3ef22c5cc6cd30265e6a769835a7a7900dea4ac6))

- Update test matrix
  ([`906ac02`](https://github.com/brendanjmeade/parsli/commit/906ac02cd7ac55f55b10a0361ed21a90df98d0bb))

- Use vtk 9.4.1
  ([`b41bc0b`](https://github.com/brendanjmeade/parsli/commit/b41bc0bfb01843b253ea75bc031203e00c7ba339))

### Features

- **mesh**: Add mesh reader
  ([`391a819`](https://github.com/brendanjmeade/parsli/commit/391a8196190c327ac360968544befd94408a3d41))

- **quad**: First quad implementation
  ([`d6165fd`](https://github.com/brendanjmeade/parsli/commit/d6165fd808e1daa062a2f447d0ec2928ff7f260c))

- **segment**: Add initial segment reader
  ([`966e7bb`](https://github.com/brendanjmeade/parsli/commit/966e7bbb086cc72c10538f3dfd64c72155212a1a))

### Testing

- Fix package definition
  ([`eb593dc`](https://github.com/brendanjmeade/parsli/commit/eb593dc23b7d3c45b6265c34b0293437bbfa1d02))
