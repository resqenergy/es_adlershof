
run:
	uv run -m scripts.preprocess_cops
	uv run -m scripts.prepare_technikkatalog
	uv run -m scripts.preprocess_capacity_costs
	uv run oemof-pipe blueprint -f adlershof
	uv run oemof-pipe scenario -f adlershof 2035_mean_rcp85
