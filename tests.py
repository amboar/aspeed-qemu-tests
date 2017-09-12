#!/usr/bin/env python
#
# Copyright 2017 IBM Corp.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import argparse
import pexpect
import sys
import unittest

args = None

class TestQemu(unittest.TestCase):	
    def test_machines(self):
        child = pexpect.spawn("%s -M ?" % args.qemu)
        child.logfile = sys.stdout
        child.expect(args.machine, timeout=1)

    def test_machine_boots(self):
        child = pexpect.spawn("%s -M %s -kernel %s -dtb %s -initrd %s -nographic" %
                (args.qemu, args.machine, args.kernel, args.dtb, args.initrd))
        child.logfile = sys.stdout
        child.expect("login:", timeout=30)
        child.kill(15)

class TestMachine(unittest.TestCase):
    qemu = None

    @classmethod
    def setUpClass(cls):
        cls.qemu = pexpect.spawn("%s -M %s -kernel %s -dtb %s -initrd %s -append 'console=ttyS4 earlyprintk debug ipv6.disable=1' -nographic" %
                (args.qemu, args.machine, args.kernel, args.dtb, args.initrd))

        cls.qemu.logfile = sys.stdout
        cls.qemu.expect("login:", timeout=30)
        cls.qemu.sendline("root")

    @classmethod
    def tearDownClass(cls):
        cls.qemu.kill(15)

    def test_external_network(self):
        self.qemu.expect("#")
        # HACK: abc.net.au still allows HTTP (not S), and doesn't have a AAAA
        # record. Busybox wget prefers IPv6 and won't retry on IPv4 on failure
        self.qemu.sendline("wget http://abc.net.au/robots.txt")
        self.qemu.sendline("sha1sum robots.txt")
        self.qemu.expect("59eade2378c6369804091f64cee3df325faff2a5  robots.txt")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exercise QEMU's Aspeed machines")
    parser.add_argument("--qemu", dest='qemu', action='store', help="Path to the qemu binary")
    parser.add_argument("--machine", dest='machine', action='store', help="The machine type to test")
    parser.add_argument("--kernel", dest='kernel', action='store', help="The kernel to execute")
    parser.add_argument("--dtb", dest='dtb', action='store', help="The DTB to configure the kernel")
    parser.add_argument("--initrd", dest='initrd', action='store', help="The userspace to execute")
    parser.add_argument("--bmc-flash", dest='bmc_flash', action='store', help="The backing file for the BMC flash device")
    parser.add_argument("--host-flash", dest='host_flash', action='store', help="The backing file for the Host flash device")
    args = parser.parse_args()
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    unittest.TextTestRunner().run(suite)
