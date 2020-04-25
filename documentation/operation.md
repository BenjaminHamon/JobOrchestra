# Operation

This page lists notes about operating a Job Orchestra instance.


## Usage

* Cancel and abort are different actions. Cancel will attempt to stop a pending run while abort will attempt to terminate a run during its execution.
* Abort sends a termination signal to the run subprocess, and kill it after a timeout. Your job scripts should listen to these signals to exit gracefully, to prevent data corruption and to avoid leaving active processes behind.
* Runs continue execution even if the connection with the master is down. Status, results and log files are always kept locally on the workers, and cleaned only when fully sent to the master.
* When a worker is going to be removed, disable it and wait for its runs to complete.


## Monitoring

* Logs from each application should be monitored for warnings and errors.
* Exception status should be investigated.
* A high number of failures on a single worker may indicate a issue with the host.
* Runs not starting may indicate a misconfiguration, the master being down, or, also if starting late, a shortage of workers. Pending runs get cancelled after the defined expiration time.
* Runs still executing after an abnormally long time may indicate a disconnected worker or an internal failure.
