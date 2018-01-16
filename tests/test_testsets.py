import pytest
import os
import json
from eth_project import regen_artifacts

startdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'testsets')
testsets = [f.path for f in os.scandir(startdir) if f.is_dir() ] 

@pytest.mark.parametrize('directory', testsets)
def test_regen(directory):
    output_file = directory + '.json'
    results_file = directory + '.result'
    assert not os.path.isfile(output_file), "Need to remove file first!"
    regen_artifacts(directory, output_file)
    # Check the results of the function
    assert os.path.isfile(output_file), "File did not get produced!"
    with open(output_file, 'r') as f:
        output = json.loads(f.read())
    with open(results_file, 'r') as f:
        results = json.loads(f.read())
    assert output == results, "Output doesn't match expected results!"
    os.remove(output_file)  # Clean up
