# -*- coding: UTF-8 -*-


# A Brainfuck interpreter 
#
#
# Copyright 2013 Ben Petering. 
# (last modified 2022-06-29, bugs)

# TODO impl this - use pyelftools, and MOSDEF? or this?
#   http://codeflow.org/entries/2009/jul/31/pyasm-python-x86-assembler/




# TODO optional unlimited cells / unlimited cell size
#  -> proper Turing equivalence?
# - easier to implement unlimited cell size (bignum) in Python ... or is it?
#  -> how would you implement unlimited number of cells?
#     - same for general Turing machine

# The compiler compiles a superset of Brainfuck that
# has an extra instruction: *
# This performs a syscall on x86 Linux, turning this
# version of Brainfuck into a pseudo-assembly language.
# Args are taken from memory at data pointer:
# %eax - dp+0
# %ebx - dp+4
# ...
# TODO how big to args need to be
# TODO if 32 bits, write Python helper func to create 32-bit values

import sys
import re

import time

class BFMemory:
    def __init__(self):
        self.bytes = bytearray(30000)

    # TODO handle negative indices - wrap?

    # def __len__(self):
    #     return 30000

    def __getitem__(self, i):
        return self.bytes[i]

    def __setitem__(self, i, val):
        
        # TODO approximate x86 semantics
        if val > 255:
            val = 0
        if val < 0:
            val = 255
        self.bytes[i] = val

    # TODO fix if we implement slicing on mem
    def __getslice__(self, i, j):
        #return str([hex(b) for b in self.bytes[i:j]])
        return self.bytes[i:j]

class BFInterpreter:
    def __init__(self, memory=None, text=None, trace=False, full_trace=False, delay=1.0):
        if memory != None:
            self.bfmem = memory
        else:
            self.bfmem  = BFMemory()    # memory
        
        self._initial_bfmem = bytearray(self.bfmem)

        if text != None:
            self.text = text
            self.text_len = len(text)
        else:
            self.text   = ''            # program text
            self.text_len = 0
            
        self.ip     = -1                # "ip"

        self.mp     = 0                 # pointer -> memory
        self.level  = 0                 # bracket nesting level

        self.trace  = trace             # trace mode toogle
        self.full_trace = full_trace    # ^ full trace 
        self.delay  = delay             # delay -between trace output

    def reset(self):
        # Trace settings persist within a BFInterpreter
        self.bfmem  = bytearray(self._initial_bfmem)
        self.ip     = -1

        self.mp     = 0
        self.level  = 0 

    def inspect(self):
        # TODO print half, mp, then just center
        print(' ' * 6 * (self.mp % 10), end='')


        print('mp')
        print()
        print('mp = %4x' % mp)
        print(' ' * 10)
        for i in range(0, 10):
            print('%4x ' % (dp+i), end='')
        print()
        print()
        print('mem = (0x) ', end='')
        for i in self.bfmem[mp:mp+10]:
            print('%10.2x ' % i, end='')
        print()


    def toggle_trace(self):
        if self.trace:
            self.trace = False
            self.full_trace = False
        else:
            self.trace = True

    def toggle_full_trace(self):
        if self.full_trace:
            self.full_trace = False
        else:
            self.trace = True
            self.full_trace = True

    def trace_status(self):
        print('Trace mode %s' % ('on' if trace else 'off'))
        print('Full trace mode %s' % ('on' if full_trace else 'off'))

    # Skip fwd past matching bracket if byte at pointer is zero

    def skip_fwd(self):
        self.ip += 1          # skip past the current bracket
        if self.ip == self.text_len:
            raise Exception("skip_fwd() reached end of text, not expected")

        while self.ip < self.text_len:
            if self.text[self.ip] == '[':
                self.level += 1
            if self.text[self.ip] == ']':
                if self.level > 0:
                    self.level -= 1
                else:
                    # next iter of main loop will set next command for us
                    self.level = 0   # reset level
                    break
            self.ip += 1
        #print "skipped %d instructions" % (ip - start)


    # Skip back to matching bracket if byte at pointer is non-zero
    
    def skip_back(self):
        self.ip -= 1          # skip past current bracket
        if self.ip == -1:
            raise Exception("skip_back() went past index 0, not expected")

        while self.ip > 0:
            if self.text[self.ip] == ']':
                self.level += 1
            if self.text[self.ip] == '[':
                if self.level > 0:
                    self.level -= 1
                else:
                    # next iter of main loop will set next command for us
                    self.level = 0   # reset level
                    break
            self.ip -= 1


    # TODO set and inspect mp 


    # TODO extend BF with a compiler to ELF
    # - add a new operator to do a linux syscall
    # - use cells a,b,c,d,e,f,... 

    # TODO catch errors and print debug info - "register" values,
    # src around pointer, memory around pointer


    def interpret(self, add_text=None):


        # Don't remove characters - keep text offsets
        self.text += add_text


        self.text_len += len(add_text)

        left = self.text.count('[')
        right = self.text.count(']')
        if left != right:
            raise Exception(
                "Program text not valid - number of brackets do not match "
                "( '[' / ']' -> {} / {})".format(left, right)
            );

        # IP = -1
        while self.ip < self.text_len - 1:
            self.ip += 1

            # TODO this should be both prior to the loop, and *after* execution of
            # instruction, and at end of interpret()
            if self.trace:
                print("ip = %d src = %s mp = %d mem = %s" % (
                    self.ip, self.text[ip], self.mp, hex(self.bfmem[self.mp])
                ))
                if self.full_trace:
                    self.inspect()
                print()
                time.sleep(delay)

            if self.text[self.ip] == '[':
                if self.bfmem[self.mp] == 0:

                    self.skip_fwd()
                continue

            if self.text[self.ip] == ']':
                if self.bfmem[self.mp] != 0:


                    self.skip_back()
                continue

            if self.text[self.ip] == '>':
                if self.mp == 29999:
                    self.mp = -1
                self.mp += 1
                continue

            if self.text[self.ip] == '<':
                if self.mp == 0:
                    self.mp = 30000
                self.mp -= 1
                continue

            if self.text[self.ip] == '+':
                self.bfmem[self.mp] += 1
                continue

            if self.text[self.ip] == '-':
                self.bfmem[self.mp] -= 1
                continue

            if self.text[self.ip] == '.':
            
                sys.stdout.write(chr(self.bfmem[self.mp]))        # ???
                continue

            if self.text[self.ip] == ',':
                self.bfmem[self.mp] = sys.stdin.read(1)
                continue

            # Remaining - ignore


            # TODO what other BF operations/algorithms/primitives are useful?


            # TODO make easier to use these primitives / combine primitives

            # TODO extend this -move arbitrary cell to other arbitrary cell
        # TODO extend that ^ - move n-cell sized value



# Methods. ???
# reverse a direction
#def reverse(direction):
#    return '<' if direction == '>' else '>'

# TODO make these useful - can we embed inside a loop?
# put in other useful places?

# Move a value n cells in a given direction ('<', '>')
def move_value(direction, ncells):
    return "%s [-] %s [-%s+%s]" % (
        direction * ncells,
        r(direction) * ncells,
        direction * ncells,
        r(direction) * ncells
    )# >>[-]<<[->>+<<]


# Store an arbitrary-sized number with most significant byte
# starting at current cell
# TODO finish
# TODO generalize
# TODO make this a macro
# TODO big-endian or little-endian?
def n(n):
    x = 1
    while 2**x <= n:
        x += 1
    # round up to multiple of 8
    if x % 8 != 0:
        x += (8 - (x % 8))

        # store highest 8 bits
        # discard
        # move to next cell

    # bytes[dp] = n >> 8
    # bytes[dp+1] = n & 0xff


# Convert an ASCII string to a Brainfuck program that generates it
#def bfgens(s):
#    bf = ''
#    for i in xrange(0, len(s)):
#        bf += '+' * ord(s[i])
#        bf += '.'
#        # conserve memory but increase source code length
#        # other method: 'throw away' current cell, use next one
#        bf += '-' * ord(s[i])
#    return bf

# TODO methods to build up segments of a BF program - how to call them
# TODO tool to build up segments, then write that source to a file
# TODO stdin as pipe, file as first arg

if __name__ == '__main__':
    interpreter = BFInterpreter()
    while True:
        text = input('bf> ')
        if text.startswith('p '):        # eval as Python
            print(eval(text[2:]))       # TODO catch errors in REPL TODO hexdump
        elif text.startswith('b '):
            # eval as Python, and then interpret as BF
            interpreter.interpret(add_text=eval(text[2:]))   
        elif text.startswith('i'):
            interpreter.inspect()
        elif re.match(r'\d+', text):
            print("%.2x" % interpreter.bfmem[int(text)])
        
        elif text.startswith('r'):
            interpreter.reset()
            print("Reset.")

        elif text.startswith('t'):
            interpreter.toggle_trace()

            interpreter.trace_status()
        elif text.startswith('ft'):
            interpreter.toggle_full_trace()

            interpreter.trace_status()
        elif text.startswith('d '):
            interpreter.delay = float(text[2:])

        else:
            interpreter.interpret()
