# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.2] - 2024-09-10
### Fixed
- Changed version of pytube to https://github.com/Mohit-majumdar/pytube.git#master to fix issue with downloading videos.
- Fix for error 400 and get_throttiling_function_name https://github.com/pytube/pytube/pull/1990

## [1.6.1] - 2024-08-17
### Fixed
- FilenotFoundError when trying to remove file from local storage if it is not exists. Added flag to skip on error.

## [1.6.0] - 2024-08-17
### Fixed
 - Local media manager not removing files.
### Removed
- Deta storage repo code and tests.
- pdbpp from dev dependencies.
### Changed
- Updated yt-dlp from 2024.7.1 to version 2024.8.6.

## [1.5.2] - 2024-07-05
### Changed
- Bumped up version of yt-dlp from 2024.5.27 to 2024.7.1.

## [1.5.1] - 2024-06-22
### Changed
- Bumped up version of yt-dlp from 2023.12.30 to 2024.5.27.

## [1.5.0] - 2024-05-11
### Added
- Background task for cleaning up expired downloads.

## [1.4.13] - 2024-04-21
### Fixed
- Catch exception when trying to download private video and return 403.

## [1.4.13] - 2024-03-24
### Added
- Sorting downloads by date in descending order in Deta datasource.

## [1.4.12] - 2024-03-24
### Changed
- Updated ruff to version 0.3.4 and config, removed isort from dev group.

## [1.4.11] - 2024-02-25
### Changed
- Updated fastapi  from 0.98.0 to 0.109.1 and updated confz from 1.8.2 to 2.0.1. 

## [1.4.10] - 2024-02-11
### Changed
- Media type in response to GET /download endpoint.

## [1.4.9] - 2024-02-03
### Changed
- Make storage `get_download` return iterable object so media file can be returned as stream.

## [1.4.8] - 2024-01-27
### Fix
- Fixed error in API when downloading video that is part of playlist.

## [1.4.7] - 2024-01-24
### Changed
- Updated pytube version to 15.0.0.

## [1.4.6] - 2024-01-24
### Changed
- Updated dependencies and Python to version 3.11.

## [1.4.5] - 2024-01-11
### Fix
- Fix unit test for deletion endpoint.

## [1.4.4] - 2023-11-20
### Changed
- Update download progress info json.
- Logging.
### Add
- Added volume config for app.

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
- Do not execute on download finish callback when ffmpeg error occured.

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
