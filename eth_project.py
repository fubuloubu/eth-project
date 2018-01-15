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
        self._bytecode = results['bytecode']
        self._bytecode_runtime = results['bytecode_runtime']
    
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
    def bytecode_runtime(self):
        if not hasattr(self, '_bytecode_runtime'):
            self._compile()
        return self._bytecode_runtime

    def read_artifacts(self, artifacts):
        # Reduces need to run compiler if code hasn't changed
        if 'checksum' in artifacts and artifacts['checksum'] is self.checksum:
            self.abi = artifacts['abi']
            self.bytecode = artifacts['bytecode']
            self.bytecode_runtime = artifacts['bytecode_runtime']
        # otherwise, will need to fully compile when asked for data

    def write_artifacts(self):
        return {
            'abi': self.abi, 
            'bytecode': self.bytecode, 
            'bytecode_runtime': self.bytecode_runtime, 
            'checksum': self.checksum
        }

    def __repr__(self):
        return self.checksum


def _main(contracts_directory, artifacts_file, output_flattened):
    # Search and load contract objects from filenames
    contracts = {}
    solc_files = []
    for root, dirs, files in os.walk(contracts_directory):
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
        results = solc.compile_files(solc_files)
        for name, artifact in results.items():
            # TODO Fix this so it works right with Contract object
            name = name.split(':')[1]
            artifact['bytecode'] = artifact['bin']
            artifact['bytecode_runtime'] = artifact['bin-runtime']
            contracts[name] = Contract(b"", lambda c: c, lambda c: artifact)
            artifact['checksum'] = generate_checksum(b"")
            contracts[name].read_artifacts(artifact)

    # Set artifacts from file (if present)
    if os.path.isfile(artifacts_file):
        with open(artifacts_file, 'r') as f:
            for name, artifacts in json.loads(f.read()).items():
                if name in contracts.keys():
                    contracts[name].read_artifacts(artifacts)

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
    ap.add_argument('--output-flattened', type=bool, nargs='?', default=False)
    _main(**vars(ap.parse_args()))
