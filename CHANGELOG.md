# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic
Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Use JC instead of GTR for faster phylogenetic inference during filtering step.

- Swap back to FastTree since VeryFastTree stuck occasionally. [#35](https://github.com/stajichlab/PHYling/issues/35)

## [2.1.1] - 2025-03-19

### Changed

- Set HMM.name to the filename of the hmm profile to adapt the change on the v12 dataset.

### Fixed

- The treeness/RCV computation error when the tree's total branch length is zero.

## [2.1.0] - 2025-03-12

### Added

- Environment variable PHYLING\_DB that can be set to retrieve the database across multiple paths.

- Site concordance factor along with bootstrap value to better interpret branch support.

### Removed

- The threads option in SearchHitsManager load method - it run faster in single process/thread.

- Custom bootstrap value assignment in main menu. Now bootstrap was done by UFBoot with 1000 replicates, standardized across all tools.

### Changed

- Make SampleList hashable and use it directly in SearchHits instead of just name.

- Remove the selected\_MSAs folder and directly link the selected MSAs to the main output folder produced by the filter module.

- Use VeryFastTree to replace FastTree.

- In consensus mode, use GTR and LG models for DNA and peptide data. In concatenation mode, use ModelFinder to find the best model(s)

- Use UFBoot for bootstrapping after tree building by either tool.

### Fixed

- The unload data when hmmsearch with multithreads.

- The FileNotFoundError when rerun in a different working directory.

- The missing newline of the treeness file output from filter module.

- Simplify the log when verbose is disabled.

## [2.0.0] - 2025-01-10

### Added

- `phyling download list` now will also print out the markersets that have already been downloaded.

- The filter module that calculate the treeness/RCV scores through `PhyKIT` to filter the uninformative markers. Use
  `-n/--top_n_toverr` to specify the number of markers you which to use in the final tree building.

- `RAxML-NG` and `IQTree` are now available for final tree building.

### Removed

- Output option in download module. Now all the BUSCO datasets will be saved in the config folder `~/.phyling/HMM`.

- Remove `--from_checkpoint` feature. Output to the previous output folder will trigger the check and automatically determine the
  rerun status.

- Remove tree building methods `UPGMA` and `Neighbor Joining`.

### Changed

- Change the align module -m/--markerset behavior. It firstly searches against the given path and the config folder
  `~/.phyling/HMM` if the path doesn't exist. Users can also directly specify the markerset name that has already been downloaded
  and saved in the config folder.

- Use timestamp for default output folder in align and tree module.

- Use `FastTree` to replace the `UPGMA` for the default tree building method.

### Fixed

- Fix the multiprocessing issue.

## [2.0.0-beta] - 2023-11-14

### Added

- Check for duplicated sample names.

- Report problematic cds sequences.

- Use checkpoint file to save the hmmsearch results to prevent rerunning the search process when adding/removing samples.

### Changed

- Use ClipKIT to replace the self-defined function for trimming off the sites that display poor phylogenetic signal.

- Move the MSA concatenate function from align module to tree module. Users who want to try different tree building strategy won't
  have to rerun the align module again.

- Replace the VeryFastTree with FastTree for stability.

### Fixed

- Fix the bug caused by translation from cds sequences with invalid length.

- Fix the bug caused by inconsistent MSA output extension.

- Fix the bug that the trimming function always return peptide MSA if the sequence has no site being trimmed.

- Fix the Python logger issue.

## [2.0.0-alpha] - 2023-10-04

### Added

- Add Download module to download the conserved markerset HMM profiles from BUSCO v5 dataset.

- Add align module which driven by pyhmmer to perform hmmsearch and hmmalign against the BUSCO markerset.

- Add tree module to visualize the resulting phylogenetic tree.

- Implement back-translation to convert the peptide MSA results to DNA counterpart when receiving coding sequence fasta as inputs.

[Unreleased]: https://github.com/stajichlab/PHYling/compare/v2.1.1...HEAD

[2.1.1]: https://github.com/stajichlab/PHYling/compare/v2.1.0...v2.1.1

[2.1.0]: https://github.com/stajichlab/PHYling/compare/v2.0.0...v2.1.0

[2.0.0]: https://github.com/stajichlab/PHYling/compare/v2.0.0-beta...v2.0.0

[2.0.0-beta]: https://github.com/stajichlab/PHYling/compare/v2.0.0-alpha...v2.0.0-beta

[2.0.0-alpha]: https://github.com/stajichlab/PHYling/releases/tag/v2.0.0-alpha
