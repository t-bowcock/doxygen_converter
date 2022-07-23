#!/usr/bin/env python3

## @package doxygen_test
#  Some file header

## @brief A test Class
class TestClass:

    ## @brief Some test function
    #  @param param1
    #  @param param2
    #  @return
    @staticmethod
    def test_function(param1: str, param2: int) -> str:
        return param1 * param2
