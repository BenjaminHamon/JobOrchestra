class PipelineViewBuilder: # pylint: disable = too-few-public-methods

	# Compute the data required to have a nice display for the pipeline.
	# Convert the pipeline definition to a graph and compute the maximum distance to each node.
	# Nodes are distributed over columns based on their distance, and over rows based on their identifier.
	# The further a node is from the start, the further to the right it is, and thus edges go from left to right.


	def __init__(self, pipeline):
		self.pipeline = pipeline

		self.all_nodes = []
		self.all_edges = []
		self.navigation = []

		self.cell_width = 280
		self.cell_height = 50
		self.cell_padding_horizontal = 40
		self.cell_padding_vertical = 20
		self.offset_multiplier = 2

		# self.colors = [ "black" ]
		self.colors = [ "red", "blue", "orange", "green", "purple" ] #, "yellow" ]


	def build(self):
		self._generate_graph()
		self._generate_node_layout()
		self._generate_navigation()

		if self.pipeline.get("inner_runs", None) is not None:
			for node in self.all_nodes:
				node["run"] = next(run for run in self.pipeline["inner_runs"] if run["element"] == node["identifier"])

		for index, path in enumerate(self.navigation):
			path["color"] = self.colors[index % len(self.colors)]

		for edge in self.all_edges:
			navigation_path = next(x for x in self.navigation if edge["start"] == x["source"] and edge["end"] == x["destination"])
			edge["path"] = self._generate_edge_path(edge, navigation_path)
			edge["path_svg"] = self._convert_path_to_svg(edge["path"])
			edge["color"] = navigation_path["color"]

		column_count = max((node["column"] for node in self.all_nodes), default = -1) + 1
		row_count = max((node["row"] for node in self.all_nodes), default = -1) + 1

 		# Add vertical space for edges
		if row_count != 0:
			row_count += 0.5

		return {
			"nodes": self.all_nodes,
			"edges": self.all_edges,
			"grid_width": int(self.cell_width * column_count),
			"grid_height": int(self.cell_height * row_count),
			"cell_width": self.cell_width,
			"cell_height": self.cell_height,
			"cell_padding_horizontal": self.cell_padding_horizontal,
			"cell_padding_vertical": self.cell_padding_vertical,
		}


	def _generate_graph(self):
		""" Instantiates data structures for the graph nodes and edges, based on the pipeline definition. """

		self.all_nodes = []
		self.all_edges = []

		for element in self.pipeline["elements"]:
			node = {
				"identifier": element["identifier"],
				"predecessors": [],
				"successors": [],
			}

			self.all_nodes.append(node)

		for element in self.pipeline["elements"]:
			for after_option in element.get("after", []):
				edge_start = next(node for node in self.all_nodes if node["identifier"] == after_option["element"])
				edge_end = next(node for node in self.all_nodes if node["identifier"] == element["identifier"])
				edge_start["successors"].append(edge_end)
				edge_end["predecessors"].append(edge_start)

				self.all_edges.append({ "start": edge_start, "end": edge_end })

		self.all_edges.sort(key = lambda x: (self.all_nodes.index(x["start"]), self.all_nodes.index(x["end"])))


	def _generate_node_layout(self):
		""" Create the graph layout for nodes by assigning each node a position in a grid. """

		all_distances = self._compute_maximum_distances()
		self.all_nodes.sort(key = lambda x: (all_distances[x["identifier"]], x["identifier"]))

		last_distance = 0
		current_row = 0

		for node in self.all_nodes:
			node_distance = all_distances[node["identifier"]]

			if node_distance != last_distance:
				current_row = 0
				last_distance = node_distance

			node["column"] = node_distance
			node["row"] = current_row

			current_row += 1


	def _compute_maximum_distances(self):
		""" Compute the maximum distances to a node from any previous node. """

		# Walk through the graph from all start nodes.
		# A node maximum distance is computed once all its predecessors have theirs.
		# Raise an exception if the loop is stuck (because of a cycle) or if some nodes were unreachable (isolated cycle).

		all_distances = { node["identifier"]: None for node in self.all_nodes }
		current_nodes = set(node["identifier"] for node in self.all_nodes if len(node["predecessors"]) == 0)

		while len(current_nodes) > 0:
			current_nodes_copy = set(current_nodes)

			for node_identifier in current_nodes_copy:
				node = next(node for node in self.all_nodes if node["identifier"] == node_identifier)

				# Wait for a node to have all its predecessors known to compute its distance
				if any(all_distances[predecessor["identifier"]] is None for predecessor in node["predecessors"]):
					continue

				all_distances[node_identifier] = max((all_distances[predecessor["identifier"]] for predecessor in node["predecessors"]), default = -1) + 1
				for successor in node["successors"]:
					current_nodes.add(successor["identifier"])
				current_nodes.remove(node_identifier)

			if current_nodes == current_nodes_copy:
				raise RuntimeError("Distance computation is stuck")

		if any(x is None for x in all_distances):
			raise RuntimeError("Distance computation could not reach some nodes")

		return all_distances


	def _generate_navigation(self): # pylint: disable = too-many-branches
		""" Create unique paths for the edges to use. """

		all_paths = []

		for node in self.all_nodes:
			for successor in node["successors"]:
				all_paths.append({ "source": node, "destination": successor })

		all_offsets = {}
		for path in all_paths:
			path["offsets"] = {}

		# Traversing, for multi-column paths
		for path in all_paths:
			path["is_multi_column"] = path["destination"]["column"] - path["source"]["column"] > 1

			if path["is_multi_column"]:
				path["row"] = max(path["source"]["row"], path["destination"]["row"]) + 0.5

				area = ("middle-row", None, path["row"])
				all_offsets[area] = (all_offsets.get(area, -1) + 1)
				path["offsets"]["middle-row"] = all_offsets[area]

		# Start points
		for path in sorted(all_paths, key = lambda x: (x["source"]["column"], x["source"]["row"], max(x.get("row", 0), x["source"]["row"], x["destination"]["row"]))):
			area = ("start", path["source"]["column"], path["source"]["row"])
			all_offsets[area] = all_offsets.get(area, -1) + 1
			path["offsets"]["start"] = all_offsets[area]

		# Column areas around start points
		for column in range(max((node["column"] for node in self.all_nodes), default = 0)):
			column_paths = [ path for path in all_paths if path["source"]["column"] == column or (path["is_multi_column"] and path["destination"]["column"] == column + 1) ]
			for path in sorted(column_paths, key = lambda x: (x["source"]["row"], - x["source"]["column"], abs(x.get("row", x["destination"]["row"]) - x["source"]["row"]))):
				area = ("start-column", column, None)
				all_offsets[area] = all_offsets.get(area, 0) + 1

				if path["source"]["column"] == column:
					path["offsets"]["start-column"] = all_offsets[area]
				if path["is_multi_column"] and path["destination"]["column"] == column + 1:
					path["offsets"]["middle-row-end-column"] = all_offsets[area]

		# Column areas around end points
		for column in range(max((node["column"] for node in self.all_nodes), default = 0)):
			column_paths = [ path for path in all_paths if path["destination"]["column"] == column + 1 or (path["is_multi_column"] and path["source"]["column"] == column) ]
			for path in sorted(column_paths, key = lambda x: (x["destination"]["row"], x["destination"]["column"], abs(x.get("row", x["source"]["row"]) - x["destination"]["row"]))):
				area = ("end-column", column, None)
				all_offsets[area] = all_offsets.get(area, 0) + 1

				if path["destination"]["column"] == column + 1:
					path["offsets"]["end-column"] = all_offsets[area]
				if path["is_multi_column"] and path["source"]["column"] == column:
					path["offsets"]["middle-row-start-column"] = all_offsets[area]

		# End points
		for path in sorted(all_paths, key = lambda x: (x["destination"]["column"], x["destination"]["row"], max(x.get("row", 0), x["source"]["row"], x["destination"]["row"]))):
			area = ("end", path["destination"]["column"], path["destination"]["row"])
			all_offsets[area] = all_offsets.get(area, -1) + 1
			path["offsets"]["end"] = all_offsets[area]

		self.navigation = all_paths


	def _generate_edge_path(self, edge, navigation_path):
		""" Generate the path for a single edge based on its navigation path. """

		path = []

		start_point = ((edge["start"]["column"] + 1) * self.cell_width - self.cell_padding_horizontal, int((edge["start"]["row"] + 0.5) * self.cell_height))
		end_point = ((edge["end"]["column"]) * self.cell_width + self.cell_padding_horizontal, int((edge["end"]["row"] + 0.5) * self.cell_height))

		start_position_offset = navigation_path["offsets"]["start"] * self.offset_multiplier
		start_column_offset = navigation_path["offsets"]["start-column"] * self.offset_multiplier
		end_column_offset = navigation_path["offsets"]["end-column"] * self.offset_multiplier
		end_position_offset = navigation_path["offsets"]["end"] * self.offset_multiplier

		path.append((start_point[0], start_point[1] + start_position_offset))
		path.append((start_point[0] + self.cell_padding_horizontal - start_column_offset, start_point[1] + start_position_offset))

		if navigation_path["is_multi_column"]:
			middle_row_start_column_offset = navigation_path["offsets"]["middle-row-start-column"] * self.offset_multiplier
			middle_row_offset = navigation_path["offsets"]["middle-row"] * self.offset_multiplier
			middle_row_end_column_offset = navigation_path["offsets"]["middle-row-end-column"] * self.offset_multiplier

			path.append(((edge["start"]["column"] + 1) * self.cell_width + middle_row_start_column_offset, int((navigation_path["row"] + 0.5) * self.cell_height + middle_row_offset)))
			path.append(((edge["end"]["column"]) * self.cell_width - middle_row_end_column_offset, int((navigation_path["row"] + 0.5) * self.cell_height + middle_row_offset)))

		path.append((end_point[0] - self.cell_padding_horizontal + end_column_offset, end_point[1] + end_position_offset))
		path.append((end_point[0], end_point[1] + end_position_offset))

		return path


	def _convert_path_to_svg(self, path): # pylint: disable = no-self-use
		""" Convert an edge path to its SVG representation. """

		svg_commands = []
		svg_commands.append("M %s %s" % path[0])
		for point in path[1:]:
			svg_commands.append("L %s %s" % point)

		return " ".join(svg_commands)



def build_pipeline_view(pipeline):
	return PipelineViewBuilder(pipeline).build()
