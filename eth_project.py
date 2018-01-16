import os
import json
import solc
#import vyper # Add integration later
from hashlib import sha256

def generate_checksum(s):
    return '0x' + sha256(s).hexdigest()

class Contract:
    def __init__(self, code, parser, compiler):
        self.code = code # Full code without imports
        self.parser = parser # Parser partial (for checksum generation)
        self.compiler = compiler # Compiler partial

    @property
    def checksum(self):
        if not hasattr(self, '_checksum'):
            serialized_parse_tree = self.parser(self.code)
            self._checksum = generate_checksum(serialized_parse_tree)
        return self._checksum

    def _compile(self):
        results = self.compiler(self.code)
        self._abi = results['abi']
        self._bytecode = results['bin']
        self._runtime = results['bin-runtime']
    
    @property
    def abi(self):
        if not hasattr(self, '_abi'):
            self._compile()
        return self._abi

    @property
    def bytecode(self):
        if not hasattr(self, '_bytecode'):
            self._compile()
        return self._bytecode

    @property
    def runtime(self):
        if not hasattr(self, '_runtime'):
            self._compile()
        return self._runtime

    def read_artifacts(self, artifacts):
        # Reduces need to run compiler if code hasn't changed
        if 'checksum' in artifacts and artifacts['checksum'] is self.checksum:
            self.abi = artifacts['abi']
            self.bytecode = artifacts['bin']
            self.runtime = artifacts['bin-runtime']
        # otherwise, will need to fully compile when asked for data

    def write_artifacts(self):
        return {
            'abi': self.abi, 
            'bin': self.bytecode, 
            'bin-runtime': self.runtime, 
            'checksum': self.checksum
        }

    def __repr__(self):
        return self.checksum


def regen_artifacts(contracts_directory, artifacts_file):
    starting_directory = os.getcwd()
    os.chdir(contracts_directory)
    # Search and load contract objects from filenames
    contracts = {}
    solc_files = []
    for root, dirs, files in os.walk(os.getcwd()):
        for _file in files:
            if _file.endswith('.sol'):
                solc_files.append(os.path.join(root, _file))
                continue # No need to process further
            # Vyper contracts are 1 contract per file,
            # and do not have an explicit name,
            # so use base of filename as name
            #if _file.endswith('.vy'):
            #    name = _file.strip('.vy')
            #    with open(os.path.join(root, _file), 'r') as f:
            #        full_code = f.read()
            #    contracts[name] = Contract(full_code, vyper.parser, vyper.compiler)
            #    continue # No need to process further

    # Solidity can have multiple contracts in a file
    # and has no batching functionality,
    # so just create object for every contract
    if solc_files:
        # TODO solc needs to be located in the contracts_directory to work
        results = solc.compile_files(solc_files)
        for name, artifact in results.items():
            # TODO Fix this so it works right with Contract object
            name = name.split(':')[1]
            contracts[name] = Contract(b"", lambda c: c, lambda c: artifact)
            artifact['checksum'] = generate_checksum(b"")
            contracts[name].read_artifacts(artifact)

    # Set artifacts from file (if present)
    if os.path.isfile(artifacts_file):
        with open(artifacts_file, 'r') as f:
            for name, artifacts in json.loads(f.read()).items():
                if name in contracts.keys():
                    contracts[name].read_artifacts(artifacts)

    os.chdir(starting_directory)

    # Once everything is parsed, write it all out again
    artifact_list = [(name, contract.write_artifacts()) for name, contract in contracts.items()]
    with open(artifacts_file, 'w') as f:
        artifacts = dict(artifact_list)
        f.write(json.dumps(artifacts))

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='''
        Create compilation artifacts file for other tools to leverage.
    ''')
    ap.add_argument('--contracts-directory', nargs='?', default='./')
    ap.add_argument('--artifacts-file', nargs='?', default='./contracts.json')
    regen_artifacts(**vars(ap.parse_args()))
