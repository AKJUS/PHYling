"""Binary wrapper"""

from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Literal, TypeVar

from .. import logger
from ..libphyling import SeqTypes
from ..libphyling._utils import CheckAttrs

_C = TypeVar("Callable", bound=Callable[..., Any])


def _check_attributes(*attrs: str):
    """Decorator to ensure specific attributes are initialized before executing the function.

    Args:
        *attrs: Attribute names to check in the instance.

    Raises:
        AttributeError: If any specified attribute is `False` in the instance.
    """
    var_mapping = {"done": "run"}
    invalid_attrs = [attr for attr in attrs if attr not in var_mapping]
    if invalid_attrs:
        raise AttributeError(f"Invalid attribute names: {invalid_attrs}")

    def decorator(func: _C) -> _C:
        @wraps(func)
        def wrapper(instance, *args, **kwargs):
            """Validate variable inequality and execute the wrapped function."""
            false_attrs = CheckAttrs.is_false(instance, *attrs)
            for var in sorted(false_attrs, key=lambda x: list(var_mapping.keys()).index(x)):
                raise AttributeError(f"Please run the {var_mapping[var]} method first.")
            return func(instance, *args, **kwargs)

        return wrapper

    return decorator


class BinaryWrapper(ABC):
    _prog: str
    _cmd_log: Literal["stdout", "stderr"] = "stdout"
    __slots__ = ("_output", "_cmd", "_result", "done")

    def __init__(self, file: str | Path, output: str | Path | None = None, *args, **kwargs) -> None:
        file = Path(file)
        if not file.exists():
            raise FileNotFoundError(f"{file}")
        if output:
            self._output = output
        args, kwargs = self._params_check(*args, **kwargs)
        self._construct_cmd(file, output, *args, **kwargs)
        self._cmd: list[str]
        self.done = False

    def run(self, *, verbose: bool = False) -> None:
        """Execute the command."""
        if self._output:
            Path(self._output).parent.mkdir(parents=True, exist_ok=True)
        logger.debug(self.cmd)
        try:
            result = subprocess.run(self._cmd, capture_output=True, check=True, text=True)
            if verbose:
                logger.debug("%s", getattr(result, self._cmd_log))
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"{self._prog} failed with cmd: {self.cmd}\n{e.stderr}")
        if self._output:
            self._result = self._output
        else:
            self._result = result.stdout
        self._post_run()
        self.done = True

    @property
    @_check_attributes("done")
    def result(self) -> str | Path:
        return self._result

    @property
    def cmd(self) -> str:
        return " ".join(self._cmd)

    def _params_check(self, *args, **kwargs) -> tuple[tuple, dict]:
        return args, kwargs

    @abstractmethod
    def _construct_cmd(self, file: Path, output: Path, *args, **kwargs) -> None: ...

    def _post_run(self):
        pass


class TreeToolWrapper(BinaryWrapper):
    __slots__ = ("_model",)

    def __init__(
        self,
        file: str | Path,
        output: str | Path,
        *args,
        seqtype: Literal["dna", "pep", "AUTO"] = "AUTO",
        model: str = "AUTO",
        **kwargs,
    ) -> None:
        super().__init__(file, output, *args, seqtype=seqtype, model=model, **kwargs)
        self._model: str = model

    def run(self, *, verbose=False) -> None:
        """Execute the phylogeny inference command.

        Returns:
            Path: The path of the newick tree file.
        """
        super().run(verbose=verbose)

    @property
    @_check_attributes("done")
    def model(self) -> str:
        return self._model

    def _params_check(self, *args, seqtype: str, **kwargs) -> tuple[tuple, dict]:
        if seqtype == SeqTypes.DNA:
            seqtype = "DNA"
        elif seqtype == SeqTypes.PEP:
            seqtype = "AA"
        else:
            seqtype = None
        return super()._params_check(*args, seqtype=seqtype, **kwargs)

    @abstractmethod
    def _construct_cmd(
        self,
        file: Path,
        output: Path,
        *args,
        seqtype: Literal["DNA", "AA"] | None,
        model: str,
        **kwargs,
    ) -> None: ...
