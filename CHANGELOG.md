# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.4] - 2023-11-20
### Changed
- Update download progress info json.
- Logging.

## [1.4.3] - 2023-11-20
### Changed
- Improvement logging in `on_finish_callback` function.
### Fix
- Fixed empty file size in downloads.
### Added
- Field with human-readable value for file size.

## [1.4.2] - 2023-11-20
### Fix
- Improvement to handler from version `1.4.1`.

## [1.4.1] - 2023-11-20
### Fix
- Handler for `TimeoutError: The read operation timed out` exception when occurs when trying to save downloaded file to remote Deta storage.

## [1.4.0] - 2023-07-14
### Added
- Allow retrying failed download.

## [1.3.1] - 2023-07-11
### Changed
- Allow removing failed downloads.

## [1.3.0] - 2023-07-10
### Added
- Handler for situation when download fails for some reason.
 
## [1.2.4] - 2023-07-08
### Fix
- Do not execute on download finish callback when ffmpeg error occured

## [1.2.3] - 2023-07-08
### Changed
- Add stderr logging in case of exception raised by ffmpeg.

## [1.2.2] - 2023-07-01
### Fixed

- Changed `pytube` src package to quickfix `pytube.exceptions.RegexMatchError` error.
## [1.2.1] - 2023-06-23
### Changed

- Added error handler for `pytube.exceptions.RegexMatchError` error.

## [1.2.0] - 2023-06-13
### Added

- Exception handler for pytube's `AgeRestrictedError` error.

### Changed

- Bumped up pytube to version 15.0.0.
