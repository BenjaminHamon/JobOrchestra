export class RunProvider {

	constructor(serviceUrl) {
		this.serviceUrl = serviceUrl;
	}

	async getStep(runIdentifier, stepIndex) {
		var url = new URL(this.serviceUrl + "/run/" + runIdentifier + "/step/" + stepIndex);

		var response = await fetch(url);
		if (response.ok == false) {
			throw new Error("HttpError: " + response.statusText + " " + "(" + response.status + ")");
		}

		return await response.json();
	}

	async getLogChunk(runIdentifier, stepIndex, cursor = 0, limit = null) {
		var url = new URL(this.serviceUrl + "/run/" + runIdentifier + "/step/" + stepIndex + "/log_chunk");
		if (limit != null)
			url.searchParams.set("limit", limit);

		var headers = { "X-Orchestra-FileCursor": cursor };

		var response = await fetch(url, { headers: headers });
		if (response.ok == false) {
			throw new Error("HttpError: " + response.statusText + " " + "(" + response.status + ")");
		}

		return { text: await response.text(), cursor: response.headers.get("X-Orchestra-FileCursor") };
	}

}