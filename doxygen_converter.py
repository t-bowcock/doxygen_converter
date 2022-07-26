#!/usr/bin/env python3
"""
Converts above comment doxygen to docstring doxygen
"""

import argparse
import os
import pathlib
import re
import typing


BRIEF = re.compile(r"\s*##\s@brief\s(.*)")
FUNCTION_DEF = re.compile(r"(\s*)def\s(.*)\(.*:")
CLASS_DEF = re.compile(r"(\s*)class\s(.*):")
MODULE = re.compile(r"##\s@package\s(.*)")
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
    def __parse_file(file_path: str) -> typing.Tuple[dict, typing.List[str]]:
        """
        Parses a Python file to return a dictionary of doxygen comments and a list of the remaining file lines

        Parameters
        ----------
        file_path : str
            Path to Python file to parse

        Returns
        -------
        typing.Tuple[dict, typing.List[str]]
            Doxygen dictionary in the form {"<object-name>": [<doxygen lines>]}
            Module docstring is stored under the key "module"
            e.g. {"module": "some docstring", "TestClass": ["summary"], "test_func": ["summary", "@param param1]}

            List of strings for all the other non-doxygen lines of code
        """
        docstrings = {}
        temp = []
        code = []
        doxygen_flag = False
        for line in file_to_array(file_path):
            if BRIEF.match(line) and not doxygen_flag:
                temp.append(BRIEF.match(line)[1])
                doxygen_flag = True
            elif MODULE.match(line) and not doxygen_flag:
                doxygen_flag = True
            elif FUNCTION_DEF.match(line) and doxygen_flag:
                docstrings[FUNCTION_DEF.match(line)[2]] = temp
                doxygen_flag = False
                temp = []
                code.append(line)
            elif CLASS_DEF.match(line) and doxygen_flag:
                docstrings[CLASS_DEF.match(line)[2]] = temp
                doxygen_flag = False
                temp = []
                code.append(line)
            elif line == "\n" and doxygen_flag:
                docstrings["module"] = temp
                doxygen_flag = False
                temp = []
                code.append(line)
            elif DECORATOR.match(line) and doxygen_flag:
                code.append(line)
            elif doxygen_flag:
                temp.append(OTHER.match(line)[1])
            else:
                code.append(line)
        print(docstrings)
        return (docstrings, code)

    @staticmethod
    def __add_docstrings(docstrings: dict, code: typing.List[str]) -> typing.List[str]:
        """
        Takes a dictionary of doxygen and list of strings and returns a list of strings with the converted docstrings
        added in the relevant locations.

        Parameters
        ----------
        docstrings: dict
            Doxygen dictionary in the form {"<object-name>": [<doxygen lines>]}
            Module docstring is stored under the key "module"
            e.g. {"module": "some docstring", "TestClass": ["summary"], "test_func": ["summary", "@param param1]}
        code: typing.List[str]
            List of strings for all the other non-doxygen lines of code

        Returns
        -------
        typing.List[str]
            The list of strings representing the code with docstrings added in the correct places
        """
        line_idx = 0
        while line_idx < len(code):
            if SHEBANG.match(code[line_idx]) and "module" in docstrings:
                code.insert(line_idx + 2, '"""\n')
                for idx, line in enumerate(docstrings["module"]):
                    code.insert(line_idx + 3 + idx, f"{line}\n")
                code.insert(line_idx + 3 + len(docstrings["module"]), '"""\n')
            elif FUNCTION_DEF.match(code[line_idx]):
                indent = FUNCTION_DEF.match(code[line_idx])[1] + "    "
                function = FUNCTION_DEF.match(code[line_idx])[2]
                if function in docstrings:
                    code.insert(line_idx + 1, f'{indent}"""!\n')
                    for idx, line in enumerate(docstrings[function]):
                        code.insert(line_idx + 2 + idx, f"{indent}{line}\n")
                    code.insert(
                        line_idx + 2 + len(docstrings[function]),
                        f'{indent}"""\n',
                    )
            elif CLASS_DEF.match(code[line_idx]):
                indent = CLASS_DEF.match(code[line_idx])[1] + "    "
                function = CLASS_DEF.match(code[line_idx])[2]
                if function in docstrings:
                    code.insert(line_idx + 1, f'{indent}"""!\n')
                    for idx, line in enumerate(docstrings[function]):
                        code.insert(line_idx + 2 + idx, f"{indent}{line}\n")
                    code.insert(
                        line_idx + 2 + len(docstrings[function]),
                        f'{indent}"""\n',
                    )
            line_idx += 1
        return code

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

    def convert(self, file_path: str, new: bool):
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
        docstrings, code = self.__parse_file(file_path)
        code = self.__add_docstrings(docstrings, code)
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
                converter.convert(py_file, args.new)
        elif os.path.isfile(path):
            if pathlib.Path(path).suffix == ".py":
                converter.convert(os.path.join(os.getcwd(), path), args.new)
            else:
                raise ValueError("Not a python file")
