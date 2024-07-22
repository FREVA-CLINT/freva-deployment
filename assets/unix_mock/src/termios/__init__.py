"""Simulation of the termios unix library for Windows."""

# Constants for when argument in tcsetattr()
TCSANOW = 0
TCSADRAIN = 1
TCSAFLUSH = 2

# Constants for tcflush() argument
TCIFLUSH = 0
TCOFLUSH = 1
TCIOFLUSH = 2

# Indexes for the mode array
IFLAG = 0
OFLAG = 1
CFLAG = 2
LFLAG = 3
ISPEED = 4
OSPEED = 5
CC = 6

# Control characters indexes
VINTR = 0
VQUIT = 1
VERASE = 2
VKILL = 3
VEOF = 4
VTIME = 5
VMIN = 6
VSWTCH = 7
VSTART = 8
VSTOP = 9
VSUSP = 10
VEOL = 11
VREPRINT = 12
VDISCARD = 13
VWERASE = 14
VLNEXT = 15
VEOL2 = 16

# Sample mode array to simulate termios attributes
default_mode = [0] * 7
default_mode[IFLAG] = 0
default_mode[OFLAG] = 0
default_mode[CFLAG] = 0
default_mode[LFLAG] = 0
default_mode[ISPEED] = 0
default_mode[OSPEED] = 0
default_mode[CC] = [0] * 32


def tcgetattr(fd):
    """Get the parameters associated with the terminal."""
    # This is a mock implementation, returning a default mode array.
    return default_mode


def tcsetattr(fd, when, attributes):
    """Set the parameters associated with the terminal."""
    # This is a mock implementation. We won't actually change any attributes.
    pass


def tcflush(fd, queue):
    """Discard queued data on the terminal."""
    # This is a mock implementation. We won't actually flush anything.
    pass


def ioctl(fd, request, argp):
    """Control device parameters."""
    if request == 0x5413:  # TIOCGWINSZ
        # Assume a default terminal size (rows, cols, x pixels, y pixels)
        return (24, 80, 640, 480)
    raise NotImplementedError("ioctl request not supported in this mock.")
