## [1.0.1](https://github.com/Pasithea0/siri-cli/compare/v1.0.0...v1.0.1) (2026-08-21)


### Bug Fixes

* Homebrew formula installs python deps via sdist resources ([a0a6e39](https://github.com/Pasithea0/siri-cli/commit/a0a6e39c6fcf0e0ba24a5f49d87f63144517ad8d))

# 1.0.0 (2026-08-21)


### Bug Fixes

* correct Siri summon hotkey for this machine (double-Command) ([ddeb459](https://github.com/Pasithea0/siri-cli/commit/ddeb45973b182032e2376934a4690f3f9cc215a0))
* ensure Siri AI is windowed before querying; recover from windowless state ([8e4ae56](https://github.com/Pasithea0/siri-cli/commit/8e4ae56a7f9cf8019d1f4aa11897e5cfac12dfe5))
* launch Siri AI with open -gj so cold-start never steals focus ([4d91593](https://github.com/Pasithea0/siri-cli/commit/4d9159304fce72d51623743e7acec94777c2ce0a))
* release pipeline — push tags, attach artifacts, correct formula sha ([416de25](https://github.com/Pasithea0/siri-cli/commit/416de25845f12ed66c54ab70d840975ab711699a))


### Features

* background-first mode — Siri answers without stealing focus ([9cec0ab](https://github.com/Pasithea0/siri-cli/commit/9cec0abd47def6643e49988fb3a89c68cf98ed28))
* bare 'siri query' CLI, robust macOS27 Siri AI backend, full docs ([ca643e2](https://github.com/Pasithea0/siri-cli/commit/ca643e2bc39e2dfe280acee73fc28a707bd28f8e))
* OCR capture path + Vision OCR module ([0293e40](https://github.com/Pasithea0/siri-cli/commit/0293e40780d2bff292abdf3e373dbb75e8bf38ec))
* scaffold siribridge package + permission/status checks ([d8ada9e](https://github.com/Pasithea0/siri-cli/commit/d8ada9efdc75a524cc6346d3ab71a355f332b5aa))
* Type-to-Siri backend + AX capture + settle-detect ([fdddcab](https://github.com/Pasithea0/siri-cli/commit/fdddcabe98c2c072f9fdf913dc2da11a2042bd06))

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Generated automatically by [semantic-release](https://semantic-release.gitbook.io/).
