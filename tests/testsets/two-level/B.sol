pragma solidity ^0.4.13;

import "inner/A.sol";

contract B is A
{
    function B()
        public
    {
        a = 1;
    }
}
