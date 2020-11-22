import { RunProvider } from "/static/orchestra/modules/providers/runProvider.mjs"

window.onload = function() {
	var runProvider = new RunProvider(window.location.origin + "/service_proxy");

	var view = new RunLogView(runProvider, window.viewData.projectIdentifier, window.viewData.runIdentifier);

	view.statusIndicatorElement = document.getElementsByClassName("status-indicator")[0];
	view.statusTextElement = document.getElementsByClassName("status-text")[0];
	view.logTextElement = document.getElementById("log-text");

	view.refresh().then(
		_ => {
			if (view.isRunCompleted() == false) {
				view.resumeAutoRefresh();
			};
		}
	)
};

export class RunLogView {

	constructor(runProvider, projectIdentifier, runIdentifier) {
		this.runProvider = runProvider;
		this.projectIdentifier = projectIdentifier;
		this.runIdentifier = runIdentifier;
	
		this.runStatus = null;
		this.logText = null;
		this.logCursor = null;
		this.logChunkSize = 1024 * 1024;
		this.logLengthLimit = 1000 * 1000;

		this.isRefreshing = false;
		this.refreshInterval = null;

		this.statusIndicatorElement = null;
		this.statusTextElement = null;
		this.logTextElement = null;
	}

	resumeAutoRefresh() {
		if (this.refreshInterval == null) {
			this.refreshInterval = setInterval(this.refresh.bind(this), 5 * 1000);
		}
	}

	pauseAutoRefresh() {
		if (this.refreshInterval != null) {
			clearInterval(this.refreshInterval);
			this.refreshInterval = null;
		}
	}

	async refresh() {
		if (this.isRefreshing)
			return;

		this.isRefreshing = true;
		
		try {
			await this.refreshStatus();
			await this.refreshLog();

			if (this.isRunCompleted()) {
				this.pauseAutoRefresh();
			}
		}
		catch (error) {
			console.error("Refresh failed: " + error);
			this.pauseAutoRefresh();
		}

		this.isRefreshing = false;
	}

	async refreshStatus() {
		var run = await this.runProvider.getRun(this.projectIdentifier, this.runIdentifier);

		if (run.status != this.runStatus) {
			var oldStatus = this.runStatus;
			this.runStatus = run.status;
			this.statusIndicatorElement.classList.remove(oldStatus);
			this.statusIndicatorElement.classList.add(this.runStatus);
			this.statusTextElement.textContent = this.runStatus;
		}
	}

	async refreshLog() {
		if (this.logText == null)
			this.logText = "";

		if (this.logText.length > this.logLengthLimit)
			return;

		if (this.logText == "")
			this.logTextElement.textContent = "[...] (Loading)";

		var lastChunkSize = null;

		do {
			var logChunk = await this.runProvider.getLogChunk(this.projectIdentifier, this.runIdentifier, this.logCursor, this.logChunkSize);

			this.logText += logChunk.text;
			this.logCursor = logChunk.cursor;

			var logTextToDisplay = this.logText.substring(0, this.logLengthLimit);
			if (this.logText.length > this.logLengthLimit) {
				logTextToDisplay = (this.logText.substring(0, logTextToDisplay.lastIndexOf("\n")) + "\n\n[...] (Truncated)").trim();
			} else if (logChunk.text.length == this.logChunkSize) {
				logTextToDisplay = (this.logText.substring(0, logTextToDisplay.lastIndexOf("\n")) + "\n\n[...] (Loading)").trim();
			}

			this.logTextElement.textContent = logTextToDisplay;
			lastChunkSize = logChunk.text.length;

		} while ((this.logText.length <= this.logLengthLimit) && (lastChunkSize == this.logChunkSize));
	}

	isRunCompleted() {
		return this.runStatus == "succeeded"
			|| this.runStatus == "failed"
			|| this.runStatus == "aborted"
			|| this.runStatus == "exception";
	}

}
