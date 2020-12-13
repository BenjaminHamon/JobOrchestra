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

		self.cell_width = 200
		self.cell_height = 50
		self.cell_padding = 20

		# self.colors = [ "black" ]
		self.colors = [ "red", "blue", "orange", "green", "purple" ] #, "yellow" ]


	def build(self):
		self._generate_graph()
		self._generate_node_layout()
		self._generate_navigation()

		for index, path in enumerate(self.navigation):
			path["color"] = self.colors[index % len(self.colors)]

		for edge in self.all_edges:
			navigation_path = next(x for x in self.navigation if edge["start"] in x["sources"] and edge["end"] == x["destination"])
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
			"cell_padding": self.cell_padding,
		}


	def _generate_graph(self):
		""" Instantiates data structures for the graph nodes and edges, based on the pipeline definition. """

		self.all_nodes = []
		self.all_edges = []

		for element in self.pipeline["elements"]:
			inner_run = next(run for run in self.pipeline["inner_runs"] if run["element"] == element["identifier"])

			node = {
				"identifier": element["identifier"],
				"predecessors": [],
				"successors": [],
				"run": inner_run,
			}

			self.all_nodes.append(node)

		for element in self.pipeline["elements"]:
			for after_option in element.get("after", []):
				edge_start = next(node for node in self.all_nodes if node["identifier"] == after_option["element"])
				edge_end = next(node for node in self.all_nodes if node["identifier"] == element["identifier"])
				edge_start["successors"].append(edge_end)
				edge_end["predecessors"].append(edge_start)

				self.all_edges.append({ "start": edge_start, "end": edge_end })


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


	def _generate_navigation(self):
		""" Create unique paths for the edges to use by regrouping them based on their destinations and adding offsets. """

		merged_paths = []

		for node in self.all_nodes:
			if len(node["predecessors"]) == 0:
				continue

			path = next((x for x in merged_paths if x["destination"] == node), None)

			if path is None:
				path = { "sources": [], "destination": node }
				merged_paths.append(path)

			path["sources"].extend(node["predecessors"])

		all_offsets = {}

		for path in merged_paths:
			# Select the row the path will use by going under all the path nodes
			path["row"] = max(x["row"] for x in path["sources"] + [ path["destination"] ])
			is_multi_column = path["destination"]["column"] - min(x["column"] for x in path["sources"]) > 1

			# Add an offset to go between the nodes
			if is_multi_column:
				path["row"] += 0.5

			path["offsets"] = {}

			# Path traversing row
			position = ("row", None, path["row"])
			area = ("row", None, path["row"])
			all_offsets[area] = (all_offsets.get(area, -1) + 1) if is_multi_column else 0
			path["offsets"][position] = all_offsets[position]

			for source in path["sources"]:
				# Start points
				position = ("start", source["column"], source["row"])
				area = ("start", source["column"], source["row"])
				all_offsets[area] = all_offsets.get(area, -1) + 1
				path["offsets"][position] = all_offsets[area]

				# Merging points into the path (column area around start points)
				position = ("merge", source["column"], source["row"])
				area = ("merge", source["column"], None)
				all_offsets[area] = all_offsets.get(area, 0) + 1
				path["offsets"][position] = all_offsets[area]

			# Last turn point into destination (column area around end point)
			position = ("last-turn", path["destination"]["column"], path["destination"]["row"])
			area = ("last-turn", path["destination"]["column"], None)
			all_offsets[area] = all_offsets.get(area, 0) + 1
			path["offsets"][position] = all_offsets[area]

		self.navigation = merged_paths


	def _generate_edge_path(self, edge, navigation_path):
		""" Generate the path for a single edge based on its navigation path. """

		path = []

		start_point = ((edge["start"]["column"] + 1) * self.cell_width - self.cell_padding, (edge["start"]["row"] + 0.5) * self.cell_height)
		end_point = ((edge["end"]["column"]) * self.cell_width + self.cell_padding, (edge["end"]["row"] + 0.5) * self.cell_height)

		offset_multiplier = 2
		start_position = ("start", edge["start"]["column"], edge["start"]["row"])
		start_position_offset = navigation_path["offsets"][start_position] * offset_multiplier
		merge_position = ("merge", edge["start"]["column"], edge["start"]["row"])
		merge_position_offset = navigation_path["offsets"][merge_position] * offset_multiplier
		last_turn_position = ("last-turn", edge["end"]["column"], edge["end"]["row"])
		last_turn_position_offset = navigation_path["offsets"][last_turn_position] * offset_multiplier
		row_position = ("row", None, navigation_path["row"])
		row_position_offset = navigation_path["offsets"][row_position] * offset_multiplier

		path.append((start_point[0], start_point[1] + start_position_offset))
		path.append((start_point[0] + self.cell_padding - merge_position_offset, start_point[1] + start_position_offset))
		path.append(((edge["start"]["column"] + 1) * self.cell_width - merge_position_offset, int((navigation_path["row"] + 0.5) * self.cell_height + row_position_offset)))
		path.append(((edge["end"]["column"]) * self.cell_width + last_turn_position_offset, int((navigation_path["row"] + 0.5) * self.cell_height + row_position_offset)))
		path.append((end_point[0] - self.cell_padding + last_turn_position_offset, end_point[1]))
		path.append(end_point)

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
