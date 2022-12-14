# BSD LICENSE
#
# Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
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

from .settings import TIMEOUT, USERNAME
from .ssh_pexpect import SSHPexpect

"""
Global structure for saving connections
"""
CONNECTIONS = []

class SSHConnection(object):

    """
    Module for create session to host.
    Implement send_expect/copy function upper SSHPexpect module.
    """

    def __init__(self, host, session_name, username, password='', dut_id=0):
        self.session = SSHPexpect(host, username, password, dut_id)
        self.name = session_name
        connection = {}
        connection[self.name] = self.session
        CONNECTIONS.append(connection)
        self.history = None

    def init_log(self, logger):
        self.logger = logger
        self.session.init_log(logger, self.name)

    def set_history(self, history):
        self.history = history

    def send_expect(self, cmds, expected, timeout=15, verify=False):
        self.logger.info(cmds)
        out = self.session.send_expect(cmds, expected, timeout, verify)
        if isinstance(out, str):
            self.logger.debug(out.replace(cmds, ''))
        if type(self.history) is list:
            self.history.append({"command": cmds, "name": self.name, "output": out})
        return out

    def send_command(self, cmds, timeout=1):
        self.logger.info(cmds)
        out = self.session.send_command(cmds, timeout)
        self.logger.debug(out.replace(cmds, ''))
        if type(self.history) is list:
            self.history.append({"command": cmds, "name": self.name, "output": out})
        return out

    def get_session_before(self, timeout=15):
        out = self.session.get_session_before(timeout)
        self.logger.debug(out)
        return out

    def close(self, force=False):
        if getattr(self, "logger", None):
            self.logger.logger_exit()

        self.session.close(force)
        connection = {}
        connection[self.name] = self.session
        try:
            CONNECTIONS.remove(connection)
        except:
            pass

    def isalive(self):
        return self.session.isalive()

    def check_available(self):
        MAGIC_STR = "DTS_CHECK_SESSION"
        out = self.session.send_command('echo %s' % MAGIC_STR, timeout=0.1)
        # if not available, try to send ^C and check again
        if MAGIC_STR not in out:
            self.logger.info("Try to recover session...")
            self.session.send_command('^C', timeout=TIMEOUT)
            out = self.session.send_command('echo %s' % MAGIC_STR, timeout=0.1)
            if MAGIC_STR not in out:
                return False

        return True

    def copy_file_from(self, src, dst=".", password='', crb_session=None):
        self.session.copy_file_from(src, dst, password, crb_session)

    def copy_file_to(self, src, dst="~/", password='', crb_session=None):
        self.session.copy_file_to(src, dst, password, crb_session)
