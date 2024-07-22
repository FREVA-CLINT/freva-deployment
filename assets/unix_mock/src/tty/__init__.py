"""Simulation of the tty unix library for Windows."""

import termios

IFLAG = termios.IFLAG
OFLAG = termios.OFLAG
CFLAG = termios.CFLAG
LFLAG = termios.LFLAG
CC = termios.CC


def setraw(fd, when=termios.TCSANOW):
    """Put terminal into raw mode."""
    mode = termios.tcgetattr(fd)
    mode[termios.IFLAG] = mode[termios.IFLAG] & ~(
        termios.BRKINT
        | termios.ICRNL
        | termios.INPCK
        | termios.ISTRIP
        | termios.IXON
    )
    mode[termios.OFLAG] = mode[termios.OFLAG] & ~(termios.OPOST)
    mode[termios.CFLAG] = mode[termios.CFLAG] & ~(
        termios.CSIZE | termios.PARENB
    )
    mode[termios.CFLAG] = mode[termios.CFLAG] | termios.CS8
    mode[termios.LFLAG] = mode[termios.LFLAG] & ~(
        termios.ECHO | termios.ICANON | termios.IEXTEN | termios.ISIG
    )
    mode[termios.CC][termios.VMIN] = 1
    mode[termios.CC][termios.VTIME] = 0
    termios.tcsetattr(fd, when, mode)


def setcbreak(fd, when=termios.TCSANOW):
    """Put terminal into cbreak mode."""
    mode = termios.tcgetattr(fd)
    mode[termios.LFLAG] = mode[termios.LFLAG] & ~(termios.ICANON)
    termios.tcsetattr(fd, when, mode)
