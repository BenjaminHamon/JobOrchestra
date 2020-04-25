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

A job pipeline is a concept where jobs are executed in sequence or parallel, so that from a single trigger several runs are scheduled, with dependencies, and distributed to several workers. Job Orchestra does not support pipelines by themselves but it includes the necessary features to set them up.

The idea is to have controller jobs which role is to trigger other jobs then wait for them and check their status. The project includes a basic Controller class which is enough to create pipelines with stages. More complex logic would likely require a custom implementation.

An example, for a build pipeline:
* Controller job triggers a check job
* Controller job waits for the check job to complete
* Controller job triggers several build jobs
* Controller job waits for all build jobs to complete
* Controller job triggers several test jobs
* Controller job waits for all test jobs to complete


## Multiprocessing

Assuming an application relying on several processes, it is possible to use Job Orchestra to start several runs and have them execute together.

For example, to test a multiplayer game, create a unique key, start several runs with it as a parameter, have the processes join a lobby using the key and run the test, then at the end aggregate results from all runs.
In the same way, for data processing, distribute data batches as runs for computing or mining, wait for them to complete and aggregate the results.

