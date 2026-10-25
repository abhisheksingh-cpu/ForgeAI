import os


class LLMRouter:
    """
    Selects the LLM model based on the type of engineering work.

    Model names are configured through environment variables so that
    the routing layer does not need to be rewritten when the provider
    or available models change.
    """

    def __init__(self):
        self.simple_model = os.getenv(
            "FORGEAI_SIMPLE_MODEL",
            os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
        )

        self.complex_model = os.getenv(
            "FORGEAI_COMPLEX_MODEL",
            self.simple_model,
        )

        self.repair_model = os.getenv(
            "FORGEAI_REPAIR_MODEL",
            self.complex_model,
        )

    def route(self, task: str) -> dict[str, str]:
        """
        Route an engineering task to an appropriate model category.

        Categories:

        simple
            Normal implementation and straightforward modifications.

        complex
            Architecture-heavy or system-design-heavy work.

        repair
            Debugging, failures, errors, and repair tasks.
        """

        if not task or not task.strip():
            return {
                "category": "simple",
                "model": self.simple_model,
            }

        normalized_task = task.lower()

        if self._is_repair_task(normalized_task):

            return {
                "category": "repair",
                "model": self.repair_model,
            }

        if self._is_complex_task(normalized_task):

            return {
                "category": "complex",
                "model": self.complex_model,
            }

        return {
            "category": "simple",
            "model": self.simple_model,
        }

    @staticmethod
    def _is_repair_task(task: str) -> bool:
        """
        Detect tasks primarily concerned with debugging or repair.
        """

        repair_terms = (
            "fix",
            "repair",
            "debug",
            "debugging",
            "bug",
            "error",
            "exception",
            "failure",
            "failing",
            "broken",
            "not working",
            "doesn't work",
            "does not work",
            "crash",
            "crashing",
            "regression",
            "test failed",
            "tests failed",
        )

        return any(
            term in task
            for term in repair_terms
        )

    @staticmethod
    def _is_complex_task(task: str) -> bool:
        """
        Detect tasks that are likely to require deeper reasoning.
        """

        complex_terms = (
            "architecture",
            "system design",
            "distributed",
            "microservices",
            "event driven",
            "event-driven",
            "scalability",
            "scalable",
            "high availability",
            "fault tolerance",
            "concurrent",
            "concurrency",
            "multi service",
            "multi-service",
            "production architecture",
            "database architecture",
        )

        return any(
            term in task
            for term in complex_terms
        )