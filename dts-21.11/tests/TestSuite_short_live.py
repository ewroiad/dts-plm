# BSD LICENSE
#
# Copyright(c) 2010-2015 Intel Corporation. All rights reserved.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of Intel Corporation nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.



"""
DPDK Test suite.

Test short live dpdk app Feature

"""

import os
import re
import time

from framework.pmd_output import PmdOutput
from framework.settings import FOLDERS
from framework.test_case import TestCase

#
#
# Test class.
#


class TestShortLiveApp(TestCase):
    #
    #
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.ports = self.dut.get_ports(self.nic)
        self.verify(len(self.ports) >= 2, "Insufficient number of ports.")
        self.app_l2fwd_path = self.dut.apps_name['l2fwd']
        self.app_l3fwd_path = self.dut.apps_name['l3fwd']
        self.app_testpmd = self.dut.apps_name['test-pmd']
        self.eal_para = self.dut.create_eal_parameters

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def compile_examples(self, example):
        # compile
        out = self.dut.build_dpdk_apps("./examples/%s"%example)
        self.verify("Error" not in out, "Compilation error")
        self.verify("No such" not in out, "Compilation error")


    def check_forwarding(self, ports, nic, testerports=[None, None], pktSize=64, received=True):
        self.send_packet(ports[0], ports[1], self.nic, testerports[1], pktSize, received)

    def send_packet(self, txPort, rxPort, nic, testerports=None, pktSize=64, received=True):
        """
        Send packages according to parameters.
        """

        if testerports is None:
            rxitf = self.tester.get_interface(self.tester.get_local_port(rxPort))
            txitf = self.tester.get_interface(self.tester.get_local_port(txPort))
        else:
            itf = testerports
        smac = self.tester.get_mac(self.tester.get_local_port(txPort))
        dmac = self.dut.get_mac_address(txPort)
        Dut_tx_mac = self.dut.get_mac_address(rxPort)

        self.tester.scapy_background()
        count = 1
        # if only one port rx/tx, we should check count 2 so that both
        # rx and tx packet are list
        if (txPort == rxPort):
            count = 2

        filter_list = [{'layer': 'ether', 'config': {'type': 'not IPv6'}}, {'layer': 'userdefined', 'config': {'pcap-filter': 'not udp'}}]
        inst = self.tester.tcpdump_sniff_packets(rxitf, count=count,filters=filter_list)

        pktlen = pktSize - 14
        padding = pktlen - 20
        self.tester.scapy_append('sendp([Ether(src="%s", dst="%s")/IP()/Raw(load="P"*%s)], iface="%s", count=4)' % (smac, dmac, padding, txitf))

        self.tester.scapy_execute()

        pkts = self.tester.load_tcpdump_sniff_packets(inst,timeout=2)
        out = str(pkts[0].show)
        self.logger.info('SCAPY Result:\n' + out + '\n\n\n')
        if received:
            self.verify(('PPP' in out) and 'src=%s'% Dut_tx_mac in out, "Receive test failed")
        else:
            self.verify('PPP' not in out, "Receive test failed")

    def check_process(self, delay_max=10):
        process_file = "/var/run/dpdk/rte/config"
        delay = 0
        while delay < delay_max:
            process = self.dut.send_expect("lsof %s | wc -l" % process_file, "# ")
            # as FUSE filesystem may not be accessible for root, so the output might include some warning info
            res = process.splitlines()[-1].strip()
            if res != '0':
                time.sleep(1)
                delay = delay + 1
            else:
                break
        self.verify(delay < delay_max, "Failed to kill the process within %s seconds" % delay_max)

    def test_basic_forwarding(self):
        """
        Basic rx/tx forwarding test
        """
        #dpdk start
        self.dut.send_expect("./%s %s -- -i --portmask=0x3" % (self.app_testpmd, self.eal_para()), "testpmd>", 120)
        time.sleep(5)
        self.dut.send_expect("set fwd mac", "testpmd>")
        self.dut.send_expect("set promisc all off", "testpmd>")
        self.dut.send_expect("start", "testpmd>")

        # check the ports are UP before sending packets
        self.pmd_out = PmdOutput(self.dut)
        res = self.pmd_out.wait_link_status_up('all', 30)
        self.verify(res is True, 'there have port link is down')

        self.check_forwarding([0, 1], self.nic)

    def test_start_up_time(self):
        """
        Using linux time to get start up time
        """
        time = []
        regex = re.compile(".* (\d+:\d{2}\.\d{2}).*")
        eal_para = self.dut.create_eal_parameters(no_pci=True)
        out = self.dut.send_expect("echo quit | time ./%s %s -- -i" % (self.app_testpmd, eal_para), "# ", 120)
        time = regex.findall(out)

        if time != []:
            print("start time: %s s"%time[0])
        else:
            self.verify(0, "start_up_time failed")

    def test_clean_up_with_signal_testpmd(self):
        repeat_time = 5
        for i in range(repeat_time):
            #dpdk start
            print("clean_up_with_signal_testpmd round %d" % (i + 1))
            self.dut.send_expect("./%s %s -- -i --portmask=0x3" % (self.app_testpmd, self.eal_para()), "testpmd>", 120)
            self.dut.send_expect("set fwd mac", "testpmd>")
            self.dut.send_expect("set promisc all off", "testpmd>")
            self.dut.send_expect("start", "testpmd>")

            # check the ports are UP before sending packets
            self.pmd_out = PmdOutput(self.dut)
            res = self.pmd_out.wait_link_status_up('all', 30)
            self.verify(res is True, 'there have port link is down')

            self.check_forwarding([0, 1], self.nic)

            # kill with different Signal
            if i%2 == 0:
                self.dut.send_expect("pkill -2 testpmd", "# ", 60, True)
            else:
                self.dut.send_expect("pkill -15 testpmd", "# ", 60, True)
            self.check_process()

    def test_clean_up_with_signal_l2fwd(self):
        repeat_time = 5
        self.compile_examples("l2fwd")
        for i in range(repeat_time):
            #dpdk start
            print("clean_up_with_signal_l2fwd round %d" % (i + 1))
            self.dut.send_expect("%s %s -- -p 0x3 &" % (self.app_l2fwd_path, self.eal_para()), "L2FWD: entering main loop", 60)
            self.check_forwarding([0, 1], self.nic)

            # kill with different Signal
            if i%2 == 0:
                self.dut.send_expect("pkill -2 l2fwd", "Bye...", 60)
            else:
                self.dut.send_expect("pkill -15 l2fwd", "Bye...", 60)
            self.check_process()

    def test_clean_up_with_signal_l3fwd(self):
        repeat_time = 5
        self.compile_examples("l3fwd")
        for i in range(repeat_time):
            #dpdk start
            print("clean_up_with_signal_l3fwd round %d" % (i + 1))
            self.dut.send_expect("%s %s -- -p 0x3 --config='(0,0,1),(1,0,2)' &" % (self.app_l3fwd_path, self.eal_para()), "L3FWD: entering main loop", 120)
            self.check_forwarding([0, 0], self.nic)

            # kill with different Signal
            if i%2 == 0:
                self.dut.send_expect("pkill -2 l3fwd", "Bye...", 60)
            else:
                self.dut.send_expect("pkill -15 l3fwd", "Bye...", 60)
            self.check_process()

    def tear_down(self):
        """
        Run after each test case.
        """

        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        self.dut.send_expect("rm -rf ./app/test-pmd/testpmd", "# ")
        self.dut.send_expect("rm -rf ./app/test-pmd/*.o", "# ")
        self.dut.send_expect("rm -rf ./app/test-pmd/build", "# ")
