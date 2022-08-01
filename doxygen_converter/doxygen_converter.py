#!/usr/bin/env python3
"""
Converts above comment doxygen to docstring doxygen
"""

import argparse
import os
import pathlib
import re
import typing

DOXYGEN_START = re.compile(r"\s*##\s(@brief|@class|@file|@package)\s(.*)")
# BRIEF = re.compile(r"\s*##\s@brief\s(.*)")
FUNCTION_DEF = re.compile(r"(\s*)def\s(.*)\(.*:")
CLASS_DEF = re.compile(r"(\s*)class\s(.*):")
# MODULE = re.compile(r"##\s@package\s(.*)")
OTHER = re.compile(r"\s*#\s\s(.*)")
DECORATOR = re.compile(r"\s*@.*")
SHEBANG = re.compile(r"#!.*")


def file_to_array(file_path: str) -> typing.List[str]:
    """
    Reads an input file and returns as a list of lines

    Parameters
    ----------
    file_path : str
        Path of file to read

    Returns
    -------
    typing.List[str]
        List of the lines in the file
    """
    file_array = []
    with open(file_path, encoding="utf-8", mode="r") as input_file:
        for line in input_file:
            file_array.append(line)
    return file_array


def parse_dir_path(dir_path: str) -> typing.List[str]:
    """
    Take a directory path and return all python files in the directory and any sub-directories

    Parameters
    ----------
    dir_path : str
        Directory path

    Returns
    -------
    typing.List[str]
        List of file paths
    """
    filelist = []
    for root, _, files in os.walk(dir_path):
        for dir_file in files:
            if pathlib.Path(dir_file).suffix == ".py":
                filelist.append(os.path.join(root, dir_file))
    return filelist


class DoxygenConverter:
    """
    Converts above comment doxygen to docstring doxygen
    """

    @staticmethod
    def __write_to_file(code: typing.List[str], file_path: str, new: bool):
        """
        Write the list of strings to a file path

        Parameters
        ----------
        code : typing.List[str]
            The list of strings representing the code with docstrings added in the correct places
        file_path : str
            Path of the original file
        new : bool
            If True then write to a new file called converted_<file_path>
            If False then overwrite the old file
        """
        if new:
            file_path = os.path.dirname(file_path) + "/converted_" + os.path.basename(file_path)
        with open(file_path, encoding="utf-8", mode="w") as result:
            for line in code:
                result.write(line)

    def complete_convert(self, file_path: str, new: bool):
        """
        Converts a Python file with comment Doxygen to docstring Doxygen and either overwrites file or creates new file.

        Parameters
        ----------
        file_path : str
            Path to the Python file
        new : bool
            If True then write to a new file called converted_<file_path>
            If False then overwrite the old file
        """
        doxygen = []
        code = file_to_array(file_path)
        doxygen_flag = False
        line_idx = 0
        while line_idx < len(code):
            if DOXYGEN_START.match(code[line_idx]) and not doxygen_flag:
                doxygen.append(DOXYGEN_START.match(code[line_idx])[2])
                doxygen_flag = True
                code.pop(line_idx)
            while doxygen_flag:
                if DECORATOR.match(code[line_idx]) and doxygen_flag:
                    line_idx += 1
                    continue
                if FUNCTION_DEF.match(code[line_idx]) and doxygen_flag:
                    indent = FUNCTION_DEF.match(code[line_idx])[1] + "    "
                    code.insert(line_idx + 1, f'{indent}"""!\n')
                    for idx, line in enumerate(doxygen):
                        code.insert(line_idx + 2 + idx, f"{indent}{line}\n")
                    code.insert(line_idx + 2 + len(doxygen), f'{indent}"""\n')

                    doxygen_flag = False
                    doxygen = []
                elif CLASS_DEF.match(code[line_idx]) and doxygen_flag:
                    indent = CLASS_DEF.match(code[line_idx])[1] + "    "
                    code.insert(line_idx + 1, f'{indent}"""!\n')
                    for idx, line in enumerate(doxygen):
                        code.insert(line_idx + 2 + idx, f"{indent}{line}\n")
                    code.insert(line_idx + 2 + len(doxygen), f'{indent}"""\n')

                    doxygen_flag = False
                    doxygen = []
                elif code[line_idx] == "\n" and doxygen_flag:
                    code.insert(line_idx, '"""\n')
                    for idx, line in enumerate(doxygen):
                        code.insert(line_idx + 1 + idx, f"{line}\n")
                    code.insert(line_idx + 1 + len(doxygen), '"""\n')

                    doxygen_flag = False
                    doxygen = []
                else:
                    print(code[line_idx])
                    doxygen.append(OTHER.match(code[line_idx])[1])
                    code.pop(line_idx)
            line_idx += 1
        self.__write_to_file(code, file_path, new)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="PROG")
    parser.add_argument("path", nargs="+", help="File(s)/Folder(s) to run script on")
    parser.add_argument(
        "-n", "--new", action="store_true", help="Put results into new file instead of overwriting files"
    )

    args = parser.parse_args()

    converter = DoxygenConverter()
    for path in args.path:
        if os.path.isdir(path):
            for py_file in parse_dir_path(path):
                converter.complete_convert(py_file, args.new)
        elif os.path.isfile(path):
            if pathlib.Path(path).suffix == ".py":
                converter.complete_convert(os.path.join(os.getcwd(), path), args.new)
            else:
                raise ValueError("Not a python file")
