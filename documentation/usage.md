# Usage

Job Orchestra is useful in delegating performing a series of commands to a remote worker machine. For example, an integration validation job could clone a git repository, run checks, build the application, run tests, and upload the resulting files to an artifact server.

By using jobs and workers smartly, it is possible to set up more advanced workflows.


## Merge validation

In a continuous integration context, Job Orchestra is useful to add automatic validation for merge requests to the development main branches.

Its strict implementation would look like that:
* Check for other runs for the same target branch, wait for them to complete
* Merge the source branch into the target.
* Run checks, build the project, run tests.
* If everything succeeds, push the merge to the remote.

For simplicity and better throughput, assuming branches are rebased and merged often, the validation is often performed on the source branch, prior to the merge, reducing the critical section to the merge itself.


## Controller

Sometimes, you need lightweight jobs to implement complex orchestration, or to oversee work running on another system, for which you have no direct control.

This is the idea behind a controller job. It is a job with a small workspace, or none at all, it will not clone a large git repository or similar, but it will execute scripts which communicate with another system or service, for example with the Orchestra to trigger other jobs or check their status, or with a remote host to perform some task.

Controller jobs should be assigned to dedicated controller workers, which would support a large number of concurrent runs per worker, so that they do not occupy the standard worker pool.


## Pipeline

Pipeline is the concept of running several jobs together based on various rules in order to split and distribute a workload.

A pipeline job triggers and monitors other jobs, defined as a list of arbitrary jobs with relationships which results in a dependency graph. It is useful to perform several job runs from a single trigger, with dependencies, and distributed to several workers. There is a specific executor implementation for this feature, but it is also possible to use a traditional job and its commands to perform a similar function.


## Multiprocessing

Assuming an application relying on several processes, it is possible to use Job Orchestra to start several runs and have them execute together.

For example, to test a multiplayer game, create a unique key, start several runs with it as a parameter, have the processes join a lobby using the key and run the test, then at the end aggregate results from all runs.
In the same way, for data processing, distribute data batches as runs for computing or mining, wait for them to complete and aggregate the results.

