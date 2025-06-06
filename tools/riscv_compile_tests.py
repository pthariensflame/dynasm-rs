#!/usr/bin/python3

# this file takes one of the testcase listings generated by riscv_gen_tests.py
# and compiles them using `as`, then using `objcopy` to extract the generated machine code

import subprocess
import binascii
import argparse
from pathlib import Path

def read_test_strings(f):
    buf = []
    for line in f:
        if line:
            if not "\t" in line:
                print(line)
            dynasm, gas, extensions = line.split("\t")
            buf.append((dynasm.strip(), gas.strip(), extensions.strip()))

    return buf

def compile_with_as(asmstring, extensions, is_64bit=True, is_32bit=False):
    with open("test.s", "w", encoding="utf-8") as f:
        f.write(".global _start\n")
        f.write("_start:\n")
        f.write(asmstring)
        f.write("\n")

    if is_64bit:
        arch = "rv64i" + extensions
        ldemulation = "elf64lriscv"
    elif is_32bit:
        arch = "rv32i" + extensions
        ldemulation = "elf32lriscv"
    else:
        raise ValueError("Unknown architecture")

    subprocess.run(["as", f"-march={arch}", "-mlittle-endian", "-mno-relax", "test.s", "-o", "test.o"], check=True, capture_output=True)
    subprocess.run(["ld", "-m", ldemulation, "test.o", "-o", "test.elf"], check=True)
    subprocess.run(["objcopy", "-O", "binary", "test.elf", "test.bin"], check=True)

    with open("test.bin", "rb") as f:
        data = f.read()

    return data

def write_result(buf, f):
    for dynasm, gas, extensions, binary in buf:
        binary = binascii.hexlify(binary).decode("utf-8")
        f.write(f"{dynasm}\t{gas}\t{extensions}\t{binary}\n")

def main():
    parser = argparse.ArgumentParser("riscv_compile_tests",  description="compile riscv testcases using riscv `as` to use as reference output")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--rv32", help="compile tests for riscv-32", action="store_true")
    group.add_argument("--rv64", help="compile tests for riscv-64", action="store_true")

    parser.add_argument("input_file", help="The output of riscv_gen_tests.py", type=Path)
    parser.add_argument("output_file", help="The file with compiled test case data", type=Path)

    args = parser.parse_args()


    with args.input_file.open("r", encoding="utf-8") as f:
        test_strings = read_test_strings(f)

    buf = []
    for dynasm, gas, extensions in test_strings:
        try:
            binary = compile_with_as(gas, extensions, args.rv64, args.rv32)
            buf.append((dynasm, gas, extensions, binary))
        except subprocess.CalledProcessError as e:
            print(f"Error at {gas} ({extensions}):\n{e.stderr}")

    with args.output_file.open("w", encoding="utf-8") as f:
        write_result(buf, f)

if __name__ == '__main__':
    main()
