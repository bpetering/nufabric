# A Brainfuck IDE(!) in Python.
#
# Provides a REPL, an interpreter, and
# a compiler that can generate ELF binaries.
#
# The REPL is the IDE.
#
# Copyright 2013 Ben Petering. (FWTW, this is nonsense.)

# TODO impl this - use pyelftools, and MOSDEF? or this?
#   http://codeflow.org/entries/2009/jul/31/pyasm-python-x86-assembler/

# TODO split a lot of this into a markdown readme

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

# TODO do we need much data going back and forth from main memory?
# syscall proxying - that's the minimum

# Maximize uses for compiler / interpreter. Toy, but how far can you push it?

# Write a ray-tracer? :)

import sys
import re
import time

# This reads cleaner if a) we have some functions
# for skipping, b) we don't have to pass lots of
# variables around. Hence these globals

bytes  = None       # memory
src    = None       # program text
ip     = None       # instruction pointer
dp     = None       # data pointer
level  = None       # bracket nesting level
trace  = None       # trace mode toogle
fulltrace = None    # full trace mode toggle
delay  = None       # delay between trace output


class BFMem:
    def __init__(self):
        self.bytes = bytearray(30000)

    # TODO handle negative indices - wrap?

    # def __len__(self):
    #     return 30000

    def __getitem__(self, i):
        return self.bytes[i]

    def __setitem__(self, i, val):
        if val > 255:
            val = 0
        if val < 0:
            val = 255
        self.bytes[i] = val

    # TODO fix if we implement slicing on mem
    def __getslice__(self, i, j):
        #return str([hex(b) for b in self.bytes[i:j]])
        return self.bytes[i:j]


def setup():
    global bytes, src, ip, dp, level, trace, fulltrace, delay

    bytes = BFMem()
    src   = ''
    ip    = -1
    dp    = 0
    level = 0
    trace = False
    fulltrace = False
    delay = 1.0


def reset():
    # Trace settings persist within an interpreter session
    global bytes, src, ip, dp, level

    bytes  = BFMem()
    src    = ''
    ip     = -1
    dp     = 0
    level  = 0          # TODO don't set these in lots of different places


def inspect():
    global dp
    global bytes

    # TODO design this properly:
    # - what needs to be ther
    # - how best to lay it out
    # TODO print half before dp, then just center
    print ' ' * 6 * (dp % 10),
    print 'dp'
    print
    print "dp = %4x" % dp
    print "           ",
    for i in range(0,10):
        print "%4x " % (dp+i),
    print
    print
    print "mem = (0x) ",
    for i in bytes[dp:dp+10]:
        print "%4.2x " % i,
    print


def toggle_trace():
    global trace, fulltrace

    if trace:
        trace = False
        fulltrace = False
    else:
        trace = True


def toggle_fulltrace():
    global trace, fulltrace

    if fulltrace:
        fulltrace = False
    else:
        trace = True
        fulltrace = True


def trace_status():
    global trace, fulltrace

    print "Trace mode %s" % ('on' if trace else 'off')
    print "Full trace mode %s" % ('on' if fulltrace else 'off')


# Skip fwd past matching bracket if byte at pointer is zero
def skip_fwd():
    global ip
    global level

    start = ip
    ip += 1          # skip past the current bracket
    while True:
        if src[ip] == '[':
            level += 1
        if src[ip] == ']':
            if level > 0:
                level -= 1
            else:
                # next iter of main loop will set next command for us
                level = 0   # reset level
                break
        ip += 1
    #print "skipped %d instructions" % (ip - start)


# Skip back to matching bracket if byte at pointer is non-zero
def skip_back():
    global ip
    global level

    start = ip
    ip -= 1          # skip past current bracket
    while True:
        if src[ip] == ']':
            level += 1
        if src[ip] == '[':
            if level > 0:
                level -= 1
            else:
                # next iter of main loop will set next command for us
                level = 0   # reset level
                break
        ip -= 1


# TODO set and inspect dp manually


# TODO extend BF with a compiler to ELF
# - add a new operator to do a linux syscall
# - use cells a,b,c,d,e,f,... relative to current data pointer

# TODO catch errors and print debug info - "register" values,
# src around pointer, memory around pointer
def interpret(s):
    global bytes
    global src
    global ip
    global dp
    global level
    global trace
    global delay

    src = re.sub(r'[^\[\]><+-.,]', '', s)
    srclen = len(src)

    opening = src.count('[')
    closing = src.count(']')
    if opening != closing:
        print "Invalid - number of opening and closing braces doesn't match"
        print " (opening = %d, closing = %d)" % (opening, closing)
        exit(1)

    ip = -1
    while ip < srclen-1:
        ip += 1

        # TODO this should be both before loop beings, and *after* execution of
        # instruction, and at end of interpret()
        if trace:
            print "ip = %d src = %s dp = %d mem = %s" % (
                ip, src[ip], dp, hex(bytes[dp])
            )
            if fulltrace:
                inspect()
            print
            time.sleep(delay)

        if src[ip] == '[':
            if bytes[dp] == 0:
                skip_fwd()
            continue

        if src[ip] == ']':
            if bytes[dp] != 0:
                skip_back()
            continue

        if src[ip] == '>':
            if dp == 29999:
                dp = -1
            dp += 1
            continue

        if src[ip] == '<':
            if dp == 0:
                dp = 30000
            dp -= 1
            continue

        if src[ip] == '+':
            bytes[dp] += 1
            continue

        if src[ip] == '-':
            bytes[dp] -= 1
            continue

        if src[ip] == '.':
            sys.stdout.write(chr(bytes[dp]))
            continue

        if src[ip] == ',':
            bytes[dp] = sys.stdin.read(1)
            continue


# TODO what other BF operations/algorithms/primitives are useful?
# which ones do you need to write a ray tracer? :)


# TODO make easier to use these primitives / combine primitives

# TODO exten this -move arbitrary cell to other arbitrary cell
# TODO extend that ^ - move n-cell sized value

# This is basically a macro system :)

# reverse a direction
def r(direction):
    return '<' if direction == '>' else '>'

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
def bfgens(s):
    bf = ''
    for i in xrange(0, len(s)):
        bf += '+' * ord(s[i])
        bf += '.'
        # conserve memory but increase source code length
        # other method: 'throw away' current cell, use next one
        bf += '-' * ord(s[i])
    return bf

# TODO methods to build up segments of a BF program
# TODO easy way to call them

# TODO tool to build up segments, then write that source to a file

# TODO stdin as pipe, file as first arg
if __name__ == '__main__':
    setup()
    while True:
        s = raw_input('bf> ')

        # This is fugly, prettify it
        if s.startswith('p'):        # eval as Python
            print eval(s[2:])        # TODO catch errors in REPL TODO hexdump
        elif s.startswith('b'):
            interpret(eval(s[2:]))   # eval as Python, and then interpret as BF
        elif s.startswith('i'):
            inspect()
        elif re.match(r'[0-9]+', s):
            print "%.2x" % bytes[int(s)]
        elif s.startswith('reset'):
            reset()
            print "State reset."
        elif s.startswith('t'):
            toggle_trace()
            trace_status()
        elif s.startswith('ft'):
            toggle_fulltrace()
            trace_status()
        elif s.startswith('d'):
            delay = float(s[2:])
        else:
            interpret(s)
