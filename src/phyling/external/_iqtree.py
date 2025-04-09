"""IQ-Tree utilities"""

from __future__ import annotations

import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="numpy")
import gzip
import re
from pathlib import Path
from typing import Literal, overload

from ..libphyling import SeqTypes, TreeMethods
from ..libphyling._utils import check_binary
from ._abc import BinaryWrapper, TreeToolWrapper
from ._models import (
    ALL_MODELS,
    DNA_MODELS,
    INVARIANT_CODES,
    PEP_MODELS,
    STATIONARY_CODES,
    NexusHandler,
    RaxmlHandler,
)

IQTREE_BIN = check_binary(
    TreeMethods.IQTREE.method, TreeMethods.IQTREE.bins, "bioconda::iqtree", "https://github.com/iqtree/iqtree2"
)


class ModelFinder(BinaryWrapper):
    _prog: str = "ModelFinder"

    @overload
    def __init__(
        self,
        file: str | Path,
        output: str | Path,
        partition_file: str | Path,
        *,
        seqtype: Literal["dna", "pep", "AUTO"] = "AUTO",
        method: Literal["ft", "raxml", "iqtree"] = "iqtree",
        threads: int = 1,
    ): ...

    @overload
    def __init__(
        self,
        file: str | Path,
        output: str | Path,
        *,
        seqtype: Literal["dna", "pep", "AUTO"] = "AUTO",
        method: Literal["ft", "raxml", "iqtree"] = "iqtree",
        threads: int = 1,
    ): ...

    def __init__(
        self,
        file: str | Path,
        output: str | Path,
        partition_file: str | Path | None = None,
        *,
        seqtype: Literal["dna", "pep", "AUTO"] = "AUTO",
        method: Literal["ft", "raxml", "iqtree"] = "iqtree",
        threads: int = 1,
    ):
        super().__init__(file, output, partition_file, seqtype=seqtype, method=method, threads=threads)

    def _post_run(self) -> None:
        if self._output.suffix == ".nex":  # partitioning analysis
            if self._method == "raxml":
                with NexusHandler(self._output) as fi, RaxmlHandler(self._output.with_suffix(""), mode="w") as fo:
                    part_info = fi.read()["sets"]
                    part_info = part_info.convert_to("raxml")
                    fo.write(part_info)
                self._result = self._output.with_suffix("")
            else:
                self._result = self._output
        else:
            with gzip.open(self._output, "rt") as f:
                for line in f.read().strip("\n").split("\n"):
                    best_model_prefix = "best_model_BIC: "
                    if line.startswith(best_model_prefix):
                        best_model = line.lstrip(best_model_prefix)
                        model, *params = best_model.split("+")
                        method_idx = list(TreeMethods).index(TreeMethods[self._method.upper()])
                        # Convert model in IQTree name to the name of each tool
                        model = ALL_MODELS[ALL_MODELS[:, 2] == model, method_idx].tolist()
                        for param in params:
                            if self._method == "ft":
                                if param.startswith(("F", "I")):
                                    params
                            else:
                                if param.startswith("F"):
                                    param = STATIONARY_CODES[STATIONARY_CODES[:, 2] == param, method_idx][0].item()
                                elif param.startswith("F"):
                                    param = INVARIANT_CODES[INVARIANT_CODES[:, 2] == param, method_idx][0].item()
            self._result = "+".join(model + params)

    def _params_check(
        self,
        partition_file: str | Path,
        seqtype: Literal["dna", "pep", "AUTO"],
        method: Literal["ft", "raxml", "iqtree"],
        **kwargs,
    ):
        if partition_file:
            if not isinstance(partition_file, (str, Path)):
                raise TypeError(f"Argument partition only accepts str or Path. Got {type(partition_file)}.")
            if method == "ft":
                raise ValueError(f"Partitioning analysis is not allowed when using {TreeMethods.FT.method}.")
            partition_file = Path(partition_file)
        method_idx = list(TreeMethods).index(TreeMethods[method.upper()])
        if seqtype == SeqTypes.DNA:
            seqtype = "DNA"
            # Find the support models for each tool and map to the name in IQTree format
            mset = ",".join(DNA_MODELS[DNA_MODELS[:, method_idx] != "", 2])
        elif seqtype == SeqTypes.PEP:
            seqtype = "AA"
            mset = ",".join(PEP_MODELS[PEP_MODELS[:, method_idx] != "", 2])
        else:
            seqtype = None
            mset = ",".join(ALL_MODELS[ALL_MODELS[:, method_idx] != "", 2])
        self._method = method
        return super()._params_check(partition_file, seqtype=seqtype, mset=mset, **kwargs)

    def _construct_cmd(
        self,
        file: Path,
        output: Path,
        partition_file: Path | None,
        *,
        seqtype: Literal["dna", "pep"] | None,
        mset: str | None,
        threads: int,
    ):
        self._cmd = [
            IQTREE_BIN,
            "-s",
            str(file.absolute()),
            "--prefix",
            str(output.absolute()),
            "-T",
            "AUTO",
            "--threads-max",
            str(threads),
            "-m",
            "TESTONLY",
        ]
        if seqtype:
            self._cmd.extend(["--seqtype", seqtype])
        if mset:
            self._cmd.extend(["--mset", mset])
        if partition_file:
            self._cmd.extend(["-p", str(partition_file)])
            self._output = Path(f"{output}.best_scheme.nex")
        else:
            self._output = Path(f"{output}.model.gz")


class Iqtree(TreeToolWrapper):
    _prog: str = TreeMethods.IQTREE.method

    def __init__(
        self,
        file: str | Path,
        output: str | Path,
        *,
        seqtype: Literal["dna", "pep", "AUTO"] = "AUTO",
        model: str = "AUTO",
        threads: int = 1,
    ):
        super().__init__(file, output, seqtype=seqtype, model=model, threads=threads)

    def _post_run(self):
        model_file = self._output.with_suffix(".best_model.nex")

        if model_file.is_file():
            self._model = model_file
        else:
            with open(self._output.with_suffix(".iqtree")) as f:
                self._model = re.search(r"alisim simulated_MSA .* (\-m) \"(.*)\" ", f.read())[2]

    def _construct_cmd(self, file: Path, output: Path, *, seqtype: Literal["DNA", "AA"] | None, model: str, threads: int):
        self._cmd = [
            IQTREE_BIN,
            "-s",
            str(file.absolute()),
            "--prefix",
            str(output.absolute()),
            "-T",
            "AUTO",
            "--threads-max",
            str(threads),
        ]
        if seqtype:
            self._cmd.extend(["--seqtype", seqtype])
        if Path(model).is_file():
            self._cmd.extend(["-p", str(model)])
        else:
            self._cmd.extend(["-m", str(model)])

        self._output = Path(f"{output}.treefile")


class UFBoot(TreeToolWrapper):
    _prog: str = "UFBoot"

    def __init__(
        self,
        file: str | Path,
        tree: str | Path,
        output: str | Path,
        *,
        model: str = "AUTO",
        bs: int = 1000,
        threads: int = 1,
    ):
        super().__init__(file, output, tree, seqtype="AUTO", model=model, threads=threads, bs=bs)

    def _params_check(self, tree: str | Path, *, seqtype, **kwargs):
        tree = Path(tree)
        if not tree.exists():
            raise FileNotFoundError(f"{tree}")
        if not tree.is_file():
            raise RuntimeError(f"{tree} is not a file.")
        return super()._params_check(tree, seqtype=seqtype, **kwargs)

    def _construct_cmd(self, file: Path, output: Path, tree: Path, *, seqtype: None, model: str, bs: int, threads: int):
        self._cmd = [
            IQTREE_BIN,
            "-s",
            str(file.absolute()),
            "--prefix",
            str(output.absolute()),
            "-t",
            str(tree.absolute()),
            "-B",
            str(bs),
            "-T",
            "AUTO",
            "--threads-max",
            str(threads),
        ]
        if Path(model).is_file():
            self._cmd.extend(["-p", str(model)])
        else:
            self._cmd.extend(["-m", str(model)])

        self._output = Path(f"{output}.treefile")


class Concordance(TreeToolWrapper):
    _prog: str = "Concordance factor calculation"

    def __init__(
        self,
        file: str | Path,
        tree: str | Path,
        output: str | Path,
        *,
        model: str = "AUTO",
        scfl: int = 100,
        threads: int = 1,
    ):
        super().__init__(file, output, tree, seqtype="AUTO", model=model, threads=threads, scfl=scfl)

    def _construct_cmd(self, file: Path, output: Path, tree: Path, *, seqtype: None, model: str, scfl: int, threads: int):
        self._cmd = [
            IQTREE_BIN,
            "-s",
            str(file.absolute()),
            "--prefix",
            str(output.absolute()),
            "-te",
            str(tree.absolute()),
            "--scfl",
            str(scfl),
            "-T",
            "AUTO",
            "--threads-max",
            str(threads),
        ]
        if Path(model).is_file():
            self._cmd.extend(["-p", str(model)])
        else:
            self._cmd.extend(["-m", str(model)])

        self._output = Path(f"{output}.cf.tree")
