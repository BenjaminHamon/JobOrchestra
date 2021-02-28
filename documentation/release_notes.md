# Release Notes

This page lists changes included in the software releases.
For more details, see the project git history.


## [Release 3.0](https://github.com/BenjaminHamon/JobOrchestra/releases/tag/release%2F3.0)

_Revision 427b2ed35702e2e0b50e20ccddcbb799542ef959 (13 March 2021)_

This is a major update, with breaking changes on a lot of interfaces and with the database, as well as large changes to the internal implementation.
The main new features are support for SQL databases and pipeline jobs.
Jobs have been reworked to be simpler and allow multiple implementations.
There are a lot of internal changes, notably for worker, executor and data storage.

The project now only supports Python 3.7 and later.

* Drop support for Python 3.5 and 3.6 (4caa868533)
* Add support for SQL databases (44998005d0)
* Add pipeline executor (85f9a876a0, a3d6ba802c, edd8848c44, 29a4b72f4c, 9be3c17a98)
* Add pipeline display for website (1388090147, 817f72c0a3, a88e0f401d, f0ff49a2a3)
* Add database import-export (54db24e657)
* Add administration command to delete a user (50e54ba1d6, 4fcb16b73b)
* Sort pending runs by creation date in job scheduler (199bfc52a0)
* Make disabled users use the Default role instead of Anonymous so that they can manage their account (f54f433b93)
* Use a single log file for a run instead of one per step (920d6a05f2)
* Remove steps from run record (1320a8824c)
* Remove job and schedule listings from project index to make it cleaner (b2e3ef9bb3)
* Homogenize table columns (894996bd20)
* Set minimum width for status columns (f6339b1b83)
* Use new job property include_in_status to filter them for status in web view (cb90ef63e0)
* Set log filename for download (81a9605bf0)
* Update log display to always use JavaScript, truncate and show loading status (7a6f7e9658, 58e7a0b247)
* Handle executor failing to start (dfd58a7456)
* Ensure UTF-8 is used everywhere (b137a8e53e)
* Fix future handling for executor termination (760c7d7bdf)
* Fix encoding issue between worker and executor (6389d8b340)
* Fix synchronization race conditions (b02ffc5995, 68bab49a76)
* Fix database order by operations (4932ae28a4, 50a66dbbb8)
* Add product in package metadata variables (2337720854)
* Use a dedicated class for asyncio application logic (6cd20a521d, 3207f4c923, 0c1677acaa, 83bc3db7bf)
* Rework database client usage to properly manage connections (b18d16c3d8)
* Rework file storage for master and worker to add an interface and a in-memory implementation (085ce96992, aa4981c0b6, 852aed2055)
* Extract run identifier creation to a dedicated method (a0a65ff31c)
* Extract worker to master connection logic from Worker to new class MasterClient (44608305e2)
* Rework messenger usage to limit it to the worker itself and remove it from the supervisor (76eb88eac3)
* Use async in executor and change its logging (895f5de94d, b9747e0949, a4fc28d273)
* Rework executor and job definition to allow several execution implementations (561c58f38c)
* Add dedicated class for process watcher (9c8ae3c160, bb4bbb4063)
* Use SIGTERM instead of SIGINT for process termination (88cba39fbc)
* Add locks in json database client (07ad4e7e1c)
* Update type hints (d6cab3759d, 21433fe610)
* Update integration tests (de662bdc37, 8efe52068c, 7e1afc2a73, d763ce3b1a, ab7b7144d0, 5fbdba192a, fc7105410d, c063b1862c, 4a70573e67, 4d99282e76)
* Replace arbitrary delay in tests with periodic condition checks with timeouts (7d44de4fcb)


## [Release 2.1](https://github.com/BenjaminHamon/JobOrchestra/releases/tag/release%2F2.1)

_Revision 80c65f9d23192e6041dacc2be64753633ad2fea1 (23 May 2020)_

This is a bug fix update, notably for memory leaks from asyncio timeouts.

* Fix error handling for worker registration (9dcdc4ea49, 35ca28d402)
* Fix request cancellation in messenger dispose (8f702f4858, 68bbb1e437)
* Fix memory leak from timeouts on messenger receive (f705b050d4, 10841a585f)
* Fix memory leak from timeouts on watching executor stdout (7c29a5cc22, 91cb4bcad6)
* Revert to using the default max size for websocket messages (00dd953a39, a3558eab23)


## [Release 2.0](https://github.com/BenjaminHamon/JobOrchestra/releases/tag/release%2F2.0)

_Revision 9d4b6abb481f8589d72c761164932c3412463ff8 (3 May 2020)_

This release renames the project to Job Orchestra.

This is a major update, with breaking changes on a lot of interfaces and with the database, as well as large changes to the internal implementation.
New features include projects, project status, time based schedules, run source, automatic worker registration, real-time logs.
Master worker communication was reworked to be bidirectional and the task system was removed.
These changes make it so that the master is way more responsive, by assigning runs and receiving updates faster.

The project supports Python 3.5 and later. With Python 3.8, there are deprecation warnings related to asyncio.

* Rename the project, and rename build to run (85c6f35d54)
* Add project feature, move jobs and runs under it (c60eccb132, 1e5d471a55)
* Add project status using revision control (5db45978c0, 4091feee8e)
* Add service methods for project revision control (e6e1927112)
* Add time based schedules (9a5461d615)
* Add run source (e22d40e1cf)
* Add transformation for run results (e52f4b6f0c)
* Add automatic worker registration (2f498287d4)
* Add basic worker selector implementation (31b964a3f1)
* Add status for external services (bbcb7278b2)
* Add web page for run details (1ce0e75fdf)
* Add pagination links on top of collection pages (a30c387908)
* Add display names (8af57b8ef9)
* Add job scheduler to handle schedules, triggers and assignments (2f498287d4)
* Add Git client in worker, to be available to worker scripts (6757c97dde)
* Add real-time logs for runs (ca390967d1)
* Cancel runs which are pending for too long (71a20788dd)
* Replace worker shutdown with disconnect (824676f2b0)
* Track worker version (623f3798d6)
* Refresh website session every day instead of on every request (1f0f1ee0e2, bd0176a016)
* Show cancelling and aborting states in website (114d19896e)
* Show owner and dates in worker web page (ae21efb2ef)
* Make users visible to the viewer user role (4f1cb86c3f)
* Set focus in login web page (57f0343b08)
* Fix fonts not being included in the distribution (5d4348a99f)
* Add database administration (418e6e60d9, e7e1559074)
* Create runs with worker as none rather than omitting the field (2f1b31572b)
* Fix some updates passing the full object instead of only the data to update (2c0b71e174)
* Move database modules to their own directory (abce979d6d)
* Change mongo database client constructor (e7e1559074)
* Change file storage behavior for missing files (c66f74614a)
* Add datetime provider (22e09b42f8)
* Rework authorization implementation (4f1cb86c3f)
* Rework master worker communication implementation (666cfe19dd, 5585cab734, a0d30556ae, c8c3f6c2b6)
* Rework master shutdown implementation (84368174ab)
* Rework controller into a class (36c59cabd1)
* Move recovery and termination into the worker main async function (c39f7311af)
* Remove tasks (55cebeba9b, 114d19896e, 3b42319f85, 03ca09c9e8)
* Add service proxy route in the website (ca390967d1)
* Rename web routes to use module name and avoid name collisions (ea142d1ce3)
* Change checks in web page templates to be stricter (7df47b688d, 60cd6970f4, 952b387124)
* Cache the user in the request for the service (5ac36f5cfd)
* Strip command from run steps in database (824676f2b0)
* Add documentation pages (e356e1227e, 2aa41d813a)
* Add type hints and comments in model and master (b1d2fcf07c, 4313de87ab)
* Update test suite (30bf6027b7, 5ac36f5cfd, dd91663578, f607fd097b, 114d19896e, 4f1cb86c3f, e7e1559074, bdd118819e)

The following dependency requirements were changed:

* cron-descriptor (new: ~= 1.2, 9a5461d615)
* flask (~= 1.0 => ~= 1.1, 5668a21755)
* pycron (new: ~= 3.0, 9a5461d615)
* python-dateutil (new: ~= 2.8, 22e09b42f8)
* python2-secrets (none => ~= 1.0, 971201ed15)
* requests (~= 2.21 => ~= 2.23, 83b86a0db7)


## [Release 1.0](https://github.com/BenjaminHamon/JobOrchestra/releases/tag/release%2F1.0)

_Revision cf7ca580f86418fba25ccdb31ff5c4e49eb943da (10 November 2019)_

This is the first release for the project, so the release notes list features rather than changes.

* Applications for website, service, master and worker
* Support for MongoDB
* Master worker communication with websockets
* Worker executors
* Controller
* Task processor
* Run cancel
* Run abort
* Run recovery
* Run results
* Run parameters
* Run download as archive
* User management
* Password and token authentication
* User role authorizations
* Website pagination and filters
* Website session refresh
