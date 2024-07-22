"""Simulation of the grp module."""


class struct_group:
    def __init__(self):
        self.gr_name = "NA"
        self.gr_gid = 0
        self.gr_passwd = "x"
        self.gr_mem = []


def getgrnam(group):
    return struct_group()


def get_getgrgid(num):
    return struct_group()
