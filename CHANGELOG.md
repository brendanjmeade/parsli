# CHANGELOG


## v0.9.3 (2025-02-13)

### Bug Fixes

- **wasm**: Camera handling
  ([`5aafa4b`](https://github.com/brendanjmeade/parsli/commit/5aafa4bd65e2a05ddf6823f2b1723a6ac8a55f22))


## v0.9.2 (2025-02-11)

### Bug Fixes

- **Rycroft**: Enable new color preset
  ([`a292056`](https://github.com/brendanjmeade/parsli/commit/a2920562f0315c1c9c4c45cda50b86cbeec38144))

### Chores

- Explore new file structure with time
  ([`2e8af97`](https://github.com/brendanjmeade/parsli/commit/2e8af97f7a398c370eb2ab6591e1e57aae815dac))


## v0.9.1 (2025-02-11)

### Bug Fixes

- **bundle**: Properly add all python files
  ([`9f3b048`](https://github.com/brendanjmeade/parsli/commit/9f3b04875e58573833849b4eeddb8d622b4d37ce))

### Build System

- **deps**: Bump python-semantic-release/python-semantic-release
  ([`d54f03f`](https://github.com/brendanjmeade/parsli/commit/d54f03feb2e4997efaa51e4d9f1ba776e92f05f7))

Bumps the actions group with 1 update:
  [python-semantic-release/python-semantic-release](https://github.com/python-semantic-release/python-semantic-release).

Updates `python-semantic-release/python-semantic-release` from 9.17.0 to 9.19.0 - [Release
  notes](https://github.com/python-semantic-release/python-semantic-release/releases) -
  [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.rst)
  -
  [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.17.0...v9.19.0)

--- updated-dependencies: - dependency-name: python-semantic-release/python-semantic-release
  dependency-type: direct:production

update-type: version-update:semver-minor

dependency-group: actions ...

Signed-off-by: dependabot[bot] <support@github.com>

### Continuous Integration

- Don't publish if no release
  ([`c2e5eab`](https://github.com/brendanjmeade/parsli/commit/c2e5eabdc4ed0708ae152a7763f2efce85abc396))

### Documentation

- **img**: Update app thumbnail
  ([`1fb5bfa`](https://github.com/brendanjmeade/parsli/commit/1fb5bfaafdb8aa3725096f8a8f45802fd68aad62))


## v0.9.0 (2025-02-08)

### Features

- **earth**: Add background earth core
  ([`2dd6151`](https://github.com/brendanjmeade/parsli/commit/2dd61515fb11ea49cc8429ecabef20f6dea9f70d))


## v0.8.0 (2025-02-08)

### Features

- **gui**: Major gui cleanup
  ([`a77d3b2`](https://github.com/brendanjmeade/parsli/commit/a77d3b2ccee596987266ecae10054907ff97b80f))


## v0.7.2 (2025-02-08)

### Bug Fixes

- **ui**: White bg, zoom bounds mock
  ([`1a7f7dd`](https://github.com/brendanjmeade/parsli/commit/1a7f7ddc2f82b7bc30e0a635ddb51c516e6b49df))


## v0.7.1 (2025-02-08)

### Bug Fixes

- **crop**: Fix latitude comparison
  ([`ee71d26`](https://github.com/brendanjmeade/parsli/commit/ee71d261606244636a9032b0097ac8c90943e5e2))


## v0.7.0 (2025-02-08)

### Features

- View toolbar, contours, color range
  ([`3148245`](https://github.com/brendanjmeade/parsli/commit/3148245168f1208c8cf71567ade63c0a7d63ae1a))


## v0.6.1 (2025-02-08)

### Bug Fixes

- **contour**: Use band contour
  ([`d77a6e1`](https://github.com/brendanjmeade/parsli/commit/d77a6e1c08fd7245384dcfe4eaae1792f5077755))


## v0.6.0 (2025-02-07)

### Chores

- Add asset files
  ([`dbce589`](https://github.com/brendanjmeade/parsli/commit/dbce589079367d9ebb29b6d905bb4d434169d3fe))

### Features

- **coast**: Add coast line selection
  ([`4175a91`](https://github.com/brendanjmeade/parsli/commit/4175a9193fcd814df554a2c5d7f26b2962a51273))


## v0.5.0 (2025-02-07)

### Bug Fixes

- **scale**: For lines in euclidean proj
  ([`14e9e1b`](https://github.com/brendanjmeade/parsli/commit/14e9e1b3092865fa520e361454dd4e1a363ab783))

### Features

- **contours**: Add contour pipeline
  ([`b03abdf`](https://github.com/brendanjmeade/parsli/commit/b03abdf839b8c4f761a5be053b65fefda52d3890))


## v0.4.0 (2025-02-07)

### Bug Fixes

- **wasm**: Reset to mesh (partially)
  ([`72a4560`](https://github.com/brendanjmeade/parsli/commit/72a4560833eb0645e61b4a48a2a637461ec3b4ff))

### Continuous Integration

- Disable artifact attestation
  ([`f16f42c`](https://github.com/brendanjmeade/parsli/commit/f16f42ca0869721b612c3d6ad4254f5a3209cb55))

### Documentation

- **README**: Update readme for simple install
  ([`825702d`](https://github.com/brendanjmeade/parsli/commit/825702d43cca977e2c9d471c85d513e8dd541454))

### Features

- **crop**: Add lat/lon cropping
  ([`88f8a19`](https://github.com/brendanjmeade/parsli/commit/88f8a19606deb4599bbdc7ed4b8801fc0d5507f7))


## v0.3.0 (2025-02-06)

### Features

- **rendering**: Allow to use wasm for local rendering
  ([`96f2369`](https://github.com/brendanjmeade/parsli/commit/96f2369189c271da16e46b967e31e37e11c8b080))

To use local rendering run the application with --wasm Also increased image quality

fix #11


## v0.2.0 (2025-02-05)

### Bug Fixes

- **fields**: Typo in refactor
  ([`f484f90`](https://github.com/brendanjmeade/parsli/commit/f484f90814d836cfce1ea52abce41e3e53b33957))

### Features

- **segment**: Add fields on segments
  ([`201701b`](https://github.com/brendanjmeade/parsli/commit/201701b149634957b792417e969183930e4304b5))


## v0.1.6 (2025-02-04)

### Bug Fixes

- **segment**: Ignore quad when col[36] is true
  ([`8de82da`](https://github.com/brendanjmeade/parsli/commit/8de82da693cd7de5b0d92e21dd8d58e30f166e8e))

fix #2


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

dependency-group: actions ...

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
