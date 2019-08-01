# Tests should generate (and then clean up) any files they need for testing. No
# binary files should be included in the repository.

from suitcase.nxstxm import export


def test_export(tmp_path, example_data):
    # Exercise the exporter on the myriad cases parametrized in example_data.
    documents = example_data()
    export(documents, tmp_path)
    # For extra credit, capture the return value from export in a variable...
    # artifacts = export(documents, tmp_path)
    # ... and read back the data to check that it looks right.
