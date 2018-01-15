# eth-project
Tool that generates json-encoded project file
(containing relevant artifacts such as abi, binary, etc.)
for an arbitrarily-nested contracts directory with any supported compiler.

## Compilers
Supported compilers are:
* [Solidity](github.com/ethereum/solidity) (via [py-solc](github.com/ethereum/py-solc)) - `*.sol`
* [Vyper](github.com/etherem/vyper) - `*.vy`

## Output Format
Output format is encoded in JSON format.
Structure is:
```json
{
    'ContractA' : {
        'abi' : {...}, # Contract's Application Binary Interface
        'bytecode' : '0x...', # Serialized EVM Bytecode of contract
        'bytecode_runtime' : '0x...', # Bytecode minus contructor
        'checksum' : '0x...' # 32-byte sha256 checksum of code (minus comments)
    },
    'ContractB' : { ... },
    ...
}
```

## Other tools
This output file is an standardized input for other tools:
* pytest-ethereum
* eth-deployer
* eth-botnet
