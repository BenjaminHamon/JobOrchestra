""" Unit tests for PipelineViewBuilder """

from bhamon_orchestra_website.pipeline_view import PipelineViewBuilder


def test_empty():
	""" Test generating a view for a pipeline with no jobs """

	pipeline = {
		"elements": [],
	}

	pipeline_view_builder = PipelineViewBuilder(pipeline)
	pipeline_view = pipeline_view_builder.build()

	assert pipeline_view is not None
	assert len(pipeline_view["nodes"]) == len(pipeline["elements"])
	assert len(pipeline_view["edges"]) == sum(len(element.get("after", [])) for element in pipeline["elements"])


def test_parallel():
	""" Test generating a view for a pipeline with parallel jobs """

	pipeline = {
		"elements": [
			{ "identifier": "stage_1_job_1", "job": "success" },
			{ "identifier": "stage_1_job_2", "job": "success" },
			{ "identifier": "stage_1_job_3", "job": "success" },
		],
	}

	pipeline_view_builder = PipelineViewBuilder(pipeline)
	pipeline_view = pipeline_view_builder.build()

	assert pipeline_view is not None
	assert len(pipeline_view["nodes"]) == len(pipeline["elements"])
	assert len(pipeline_view["edges"]) == sum(len(element.get("after", [])) for element in pipeline["elements"])


def test_sequential():
	""" Test generating a view for a pipeline with sequential jobs """

	pipeline = {
		"elements": [
			{ "identifier": "stage_1_job_1", "job": "success" },
			{ "identifier": "stage_2_job_1", "job": "success", "after": [ { "element": "stage_1_job_1", "status": [ "succeeded" ] } ] },
			{ "identifier": "stage_3_job_1", "job": "success", "after": [ { "element": "stage_2_job_1", "status": [ "succeeded" ] } ] },
		],
	}

	pipeline_view_builder = PipelineViewBuilder(pipeline)
	pipeline_view = pipeline_view_builder.build()

	assert pipeline_view is not None
	assert len(pipeline_view["nodes"]) == len(pipeline["elements"])
	assert len(pipeline_view["edges"]) == sum(len(element.get("after", [])) for element in pipeline["elements"])


def test_complex():
	""" Test generating a view for a pipeline with a complex set of jobs """

	pipeline = {
		"elements": [
			{ "identifier": "stage_1_job_1", "job": "success" },
			{ "identifier": "stage_1_job_2", "job": "success" },
			{ "identifier": "stage_1_job_3", "job": "success" },

			{ "identifier": "stage_2_job_1", "job": "success", "after": [ { "element": "stage_1_job_1", "status": [ "succeeded" ] } ] },
			{ "identifier": "stage_2_job_2", "job": "success", "after": [ { "element": "stage_1_job_2", "status": [ "succeeded" ] } ] },
			{ "identifier": "stage_2_job_3", "job": "success", "after": [ { "element": "stage_1_job_3", "status": [ "succeeded" ] } ] },

			{ "identifier": "stage_3_job_1", "job": "success", "after": [ { "element": "stage_2_job_1", "status": [ "succeeded" ] } ] },
			{ "identifier": "stage_3_job_2", "job": "success", "after": [ { "element": "stage_2_job_2", "status": [ "succeeded" ] } ] },
			{ "identifier": "stage_3_job_3", "job": "success", "after": [ { "element": "stage_2_job_3", "status": [ "succeeded" ] } ] },
		],
	}

	pipeline_view_builder = PipelineViewBuilder(pipeline)
	pipeline_view = pipeline_view_builder.build()

	assert pipeline_view is not None
	assert len(pipeline_view["nodes"]) == len(pipeline["elements"])
	assert len(pipeline_view["edges"]) == sum(len(element.get("after", [])) for element in pipeline["elements"])
