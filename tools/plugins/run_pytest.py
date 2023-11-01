from checker import PipelinePlugin


class RunPytestPlugin(PipelinePlugin):
    name = "run_pytest"

    def __init__(self,