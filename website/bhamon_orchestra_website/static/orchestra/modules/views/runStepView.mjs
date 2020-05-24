import { RunProvider } from "/static/orchestra/modules/providers/runProvider.mjs"

window.onload = function() {
	var runProvider = new RunProvider(window.location.origin + "/service_proxy");

	var view = new RunStepView(runProvider, window.viewData.projectIdentifier, window.viewData.runIdentifier, window.viewData.stepIndex);

	view.statusIndicatorElement = document.getElementsByClassName("status-indicator")[0];
	view.statusTextElement = document.getElementsByClassName("status-text")[0];
	view.logTextElement = document.getElementById("log-text");

	view.refresh().then(
		_ => {
			if (view.isStepCompleted(view.stepStatus) == false) {
				view.resumeAutoRefresh();
			};
		}
	)
};

export class RunStepView {

	constructor(runProvider, projectIdentifier, runIdentifier, stepIndex) {
		this.runProvider = runProvider;
		this.projectIdentifier = projectIdentifier;
		this.runIdentifier = runIdentifier;
		this.stepIndex = stepIndex;
	
		this.stepStatus = null;
		this.logText = null;
		this.logCursor = null;
		this.logChunkSize = 1024 * 1024;
		this.logLengthLimit = 1000 * 1000;
		this.refreshInterval = null;
		this.isRefreshing = false;

		this.statusIndicatorElement = null;
		this.statusTextElement = null;
		this.logTextElement = null;
	}

	resumeAutoRefresh() {
		if (this.refreshStepViewInterval == null) {
			this.refreshStepViewInterval = setInterval(this.refresh.bind(this), 5 * 1000);
		}
	}

	pauseAutoRefresh() {
		if (this.refreshStepViewInterval != null) {
			clearInterval(this.refreshStepViewInterval);
			this.refreshStepViewInterval = null;
		}
	}

	async refresh() {
		if (this.isRefreshing)
			return;

		this.isRefreshing = true;
		
		try {
			await this.refreshStatus();
			await this.refreshLog();

			if (this.isStepCompleted(this.stepStatus)) {
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
		var step = await this.runProvider.getStep(this.projectIdentifier, this.runIdentifier, this.stepIndex);

		if (step.status != this.stepStatus) {
			var oldStatus = this.stepStatus;
			this.stepStatus = step.status;
			this.statusIndicatorElement.classList.remove(oldStatus);
			this.statusIndicatorElement.classList.add(this.stepStatus);
			this.statusTextElement.textContent = this.stepStatus;
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
			var logChunk = await this.runProvider.getLogChunk(this.projectIdentifier, this.runIdentifier, this.stepIndex, this.logCursor, this.logChunkSize);

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

	isStepCompleted(status) {
		return status == "succeeded"
			|| status == "failed"
			|| status == "aborted"
			|| status == "exception"
			|| status == "skipped";
	}

}
