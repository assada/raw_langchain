import logging
from typing import Any, Dict, List, Optional, Union

import llm_guard
from langchain.callbacks.manager import AsyncCallbackManagerForChainRun, CallbackManagerForChainRun
from langchain.chains.base import Chain
from langchain.schema.messages import BaseMessage, HumanMessage
from pydantic import ConfigDict, model_validator

logger = logging.getLogger(__name__)


class LLMGuardPromptException(Exception):
    """Exception to raise when llm-guard marks prompt invalid."""


class LLMGuardPromptChain(Chain):
    input_key: str = "input"
    output_key: str = "history"

    scanners: Dict[str, Dict] = {}
    """The scanners to use."""
    scanners_ignore_errors: List[str] = []
    """The scanners to ignore if they throw errors."""
    vault: Optional[llm_guard.vault.Vault] = None
    """The scanners to ignore errors from."""
    raise_error: bool = True
    """Whether to raise an error if the LLMGuard marks the prompt invalid."""

    initialized_scanners: List[Any] = []

    @property
    def input_keys(self) -> List[str]:
        return [self.input_key]

    @property
    def output_keys(self) -> List[str]:
        return [self.output_key]

    @model_validator(mode="before")
    def init_scanners(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        logger.warning(f"init_scanners called with values keys: {list(values.keys())}")

        if values.get("initialized_scanners") is not None:
            logger.warning(f"initialized_scanners already exists: {len(values.get('initialized_scanners', []))}")
            return values

        try:
            scanners_config = values.get("scanners")
            logger.debug(f"scanners config: {scanners_config}")

            if scanners_config is not None:
                values["initialized_scanners"] = []
                logger.info(f"Initializing {len(scanners_config)} scanners")

                for scanner_name in scanners_config:
                    scanner_config = scanners_config[scanner_name]
                    logger.debug(f"Initializing scanner: {scanner_name} with config: {scanner_config}")

                    if scanner_name == "Anonymize":
                        scanner_config["vault"] = values["vault"]
                        logger.debug(f"Added vault to Anonymize scanner")

                    try:
                        scanner = llm_guard.input_scanners.get_scanner_by_name(scanner_name, scanner_config)
                        values["initialized_scanners"].append(scanner)
                        logger.info(f"Successfully initialized scanner: {scanner_name}")
                    except Exception as scanner_error:
                        logger.error(f"Failed to initialize scanner {scanner_name}: {scanner_error}")
                        raise

                logger.info(f"Total initialized scanners: {len(values['initialized_scanners'])}")
            else:
                logger.info("No scanners config provided")

            return values
        except Exception as e:
            logger.error(f"Error in init_scanners: {e}")
            raise ValueError(
                "Could not initialize scanners. " f"Please check provided configuration. {e}"
            ) from e

    def _extract_last_human_message(self, messages: Union[List[BaseMessage], str]) -> str:
        if isinstance(messages, str):
            return messages

        if not isinstance(messages, list):
            return str(messages)

        for message in reversed(messages):
            if isinstance(message, HumanMessage):
                return message.content

        raise ValueError("No HumanMessage found in the message history")

    def _sanitize_message_history(
            self,
            messages: Union[List[BaseMessage], str],
            run_manager: Optional[CallbackManagerForChainRun] = None
    ) -> Union[List[BaseMessage], str]:
        if isinstance(messages, str):
            sanitized_content = messages
            for scanner in self.initialized_scanners:
                sanitized_content, is_valid, risk_score = scanner.scan(sanitized_content)
                self._check_result(type(scanner).__name__, is_valid, risk_score, run_manager)
            return sanitized_content

        if not isinstance(messages, list):
            content = str(messages)
            for scanner in self.initialized_scanners:
                content, is_valid, risk_score = scanner.scan(content)
                self._check_result(type(scanner).__name__, is_valid, risk_score, run_manager)
            return content

        history_copy = messages.copy()

        last_human_idx = None
        for i, message in enumerate(reversed(history_copy)):
            if isinstance(message, HumanMessage):
                last_human_idx = len(history_copy) - 1 - i
                break

        if last_human_idx is None:
            raise ValueError("No HumanMessage found in the message history")

        original_content = history_copy[last_human_idx].content

        logger.info(f"Number of initialized scanners: {len(self.initialized_scanners)}")
        for i, scanner in enumerate(self.initialized_scanners):
            logger.debug(f"Scanner {i}: {type(scanner).__name__}")

        sanitized_content = original_content
        for scanner in self.initialized_scanners:
            before_scan = sanitized_content
            sanitized_content, is_valid, risk_score = scanner.scan(sanitized_content)
            logger.info(
                f"Scanner {type(scanner).__name__}: is_valid={is_valid}, risk_score={risk_score}, changed_content={before_scan != sanitized_content}")
            self._check_result(type(scanner).__name__, is_valid, risk_score, run_manager)

        history_copy[last_human_idx].content = sanitized_content

        logger.debug(f"Original last human message: {original_content}")
        logger.debug(f"Sanitized last human message: {sanitized_content}")

        return history_copy

    def _check_result(
            self,
            scanner_name: str,
            is_valid: bool,
            risk_score: float,
            run_manager: Optional[CallbackManagerForChainRun] = None,
    ):
        if is_valid:
            return

        if run_manager:
            run_manager.on_text(
                text=f"This prompt was determined as invalid by {scanner_name} scanner with risk score {risk_score}",
                color="red",
                verbose=self.verbose,
            )

        if scanner_name in self.scanners_ignore_errors:
            return

        if self.raise_error:
            raise LLMGuardPromptException(
                f"This prompt was determined as invalid based on configured policies with risk score {risk_score}"
            )

    async def _acall(
            self,
            inputs: Dict[str, Any],
            run_manager: Optional[AsyncCallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        if run_manager:
            await run_manager.on_text("Running LLMGuardPromptChain...\n")

        # Sanitize the message history
        raw_input = inputs[self.input_keys[0]]
        sanitized_history = self._sanitize_message_history(raw_input, run_manager)

        return {self.output_key: sanitized_history}

    def _call(
            self,
            inputs: Dict[str, str],
            run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        if run_manager:
            run_manager.on_text("Running LLMGuardPromptChain...\n")

        raw_input = inputs[self.input_keys[0]]
        sanitized_history = self._sanitize_message_history(raw_input, run_manager)

        return {self.output_key: sanitized_history}


class LLMGuardOutputException(Exception):
    """Exception to raise when llm-guard marks output invalid."""


class LLMGuardOutputChain(Chain):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    input_key: List[str] = ["prompt", "output"]
    output_key: str = "result"

    scanners: Dict[str, Dict] = {}
    """The scanners to use."""
    scanners_ignore_errors: List[str] = []
    """The scanners to ignore if they throw errors."""
    vault: Optional[llm_guard.vault.Vault] = None
    """The scanners to ignore errors from."""
    raise_error: bool = True
    """Whether to raise an error if the LLMGuard marks the output invalid."""

    initialized_scanners: List[Any] = []

    @property
    def input_keys(self) -> List[str]:
        return self.input_key

    @property
    def output_keys(self) -> List[str]:
        return [self.output_key]

    @model_validator(mode="before")
    def init_scanners(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get("initialized_scanners") is not None:
            return values
        try:
            if values.get("scanners") is not None:
                values["initialized_scanners"] = []
                for scanner_name in values.get("scanners"):
                    scanner_config = values.get("scanners")[scanner_name]
                    if scanner_name == "Deanonymize":
                        scanner_config["vault"] = values["vault"]

                    values["initialized_scanners"].append(
                        llm_guard.output_scanners.get_scanner_by_name(scanner_name, scanner_config)
                    )

            return values
        except Exception as e:
            raise ValueError(
                "Could not initialize scanners. " f"Please check provided configuration. {e}"
            ) from e

    def _prompt_to_str(self, prompt: Any) -> str:
        if isinstance(prompt, str):
            return prompt

        if hasattr(prompt, "to_messages"):
            try:
                msgs = prompt.to_messages()
                return "\n".join(getattr(m, "content", "") for m in msgs)
            except Exception:
                pass

        if isinstance(prompt, list) and all(hasattr(m, "content") for m in prompt):
            return "\n".join(m.content for m in prompt)

        return str(prompt)

    def _check_result(
            self,
            scanner_name: str,
            is_valid: bool,
            risk_score: float,
    ):
        if is_valid:
            return

        logger.warning(
            f"This output was determined as invalid by {scanner_name} scanner with risk score {risk_score}"
        )

        if scanner_name in self.scanners_ignore_errors:
            return

        if self.raise_error:
            raise LLMGuardOutputException(
                f"This output was determined as invalid based on configured policies with risk score {risk_score}"
            )

    def scan(self, prompt: Any, output: Union[BaseMessage, str]) -> Union[BaseMessage, str]:
        prompt_str = self._prompt_to_str(prompt)

        sanitized_output = output
        if isinstance(output, BaseMessage):
            sanitized_output = sanitized_output.content

        for scanner in self.initialized_scanners:
            sanitized_output, is_valid, risk_score = scanner.scan(prompt_str, sanitized_output)
            self._check_result(type(scanner).__name__, is_valid, risk_score)

        if isinstance(output, BaseMessage):
            output.content = sanitized_output
            return output
        return sanitized_output

    def _call(
            self,
            inputs: Dict[str, Any],
            run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        prompt = inputs["prompt"]
        output = inputs["output"]
        return {"result": self.scan(prompt, output)}

    async def _acall(
            self,
            inputs: Dict[str, Any],
            run_manager: Optional[AsyncCallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        return self._call(inputs, run_manager)

    def __hash__(self) -> int:
        return hash((
            id(self),
            len(self.initialized_scanners),
        ))
