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

"""
Excel spreadsheet generator

Example:
    excel_report = ExcelReporter('../output/test_results.xls')
    result = Result()
    result.dut = dutIP
    result.target = target
    result.nic = nic
        result.test_suite = test_suite
            result.test_case = test_case.__name__
            result.test_case_passed()
    excel_report.save(result)

Result:
    execl will be formatted as
    DUT             Target                      NIC      Test suite Test case Results
    10.239.128.117  x86_64-native-linuxapp-gcc  niantic
                                                         SUITE      CASE      PASSED


"""
import xlwt
from xlwt.ExcelFormula import Formula


class ExcelReporter(object):

    """
    Make use of a Result object generates an Excel Spreadsheet with those
    results.
    It supports saving the same file with incremental results.
    """

    def __init__(self, filename):
        self.filename = filename
        self.xsl_file = None
        self.result = None
        self.__styles()

    def __init(self):
        self.workbook = xlwt.Workbook()
        self.sheet = self.workbook.add_sheet(
            "Test Results", cell_overwrite_ok=True)

    def __add_header(self):
        self.sheet.write(0, 0, 'DUT', self.header_style)
        self.sheet.write(0, 1, 'DPDK version', self.header_style)
        self.sheet.write(0, 2, 'Target', self.header_style)
        self.sheet.write(0, 3, 'NIC', self.header_style)
        self.sheet.write(0, 4, 'Test suite', self.header_style)
        self.sheet.write(0, 5, 'Test case', self.header_style)
        self.sheet.write(0, 6, 'Results', self.header_style)

        self.sheet.write(0, 8, 'Pass', self.header_style)
        self.sheet.write(0, 9, 'Fail', self.header_style)
        self.sheet.write(0, 10, 'Blocked', self.header_style)
        self.sheet.write(0, 11, 'N/A', self.header_style)
        self.sheet.write(0, 12, 'Not Run', self.header_style)
        self.sheet.write(0, 13, 'Total', self.header_style)

        self.sheet.write(1, 8, Formula('COUNTIF(G2:G2000,"PASSED")'))
        self.sheet.write(1, 9, Formula('COUNTIF(G2:G2000,"FAILED*") + COUNTIF(G2:G2000,"IXA*")'))
        self.sheet.write(1, 10, Formula('COUNTIF(G2:G2000,"BLOCKED*")'))
        self.sheet.write(1, 11, Formula('COUNTIF(G2:G2000,"N/A*")'))
        self.sheet.write(1, 13, Formula('I2+J2+K2+L2+M2'))

        self.sheet.col(0).width = 4000
        self.sheet.col(1).width = 4500
        self.sheet.col(2).width = 7500
        self.sheet.col(3).width = 3000
        self.sheet.col(4).width = 5000
        self.sheet.col(5).width = 8000
        self.sheet.col(6).width = 3000
        self.sheet.col(7).width = 1000
        self.sheet.col(8).width = 3000
        self.sheet.col(9).width = 3000
        self.sheet.col(10).width = 3000
        self.sheet.col(11).width = 3000
        self.sheet.col(12).width = 3000
        self.sheet.col(13).width = 3000

    def __styles(self):
        header_pattern = xlwt.Pattern()
        header_pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        header_pattern.pattern_fore_colour = xlwt.Style.colour_map['ocean_blue']

        passed_font = xlwt.Font()
        passed_font.colour_index = xlwt.Style.colour_map['black']
        self.passed_style = xlwt.XFStyle()
        self.passed_style.font = passed_font

        failed_font = xlwt.Font()
        failed_font.bold = True
        failed_font.colour_index = xlwt.Style.colour_map['red']
        self.failed_style = xlwt.XFStyle()
        self.failed_style.font = failed_font

        header_font = xlwt.Font()
        header_font.bold = True
        header_font.height = 260
        header_font.italic = True
        header_font.colour_index = xlwt.Style.colour_map['white']

        title_font = xlwt.Font()
        title_font.bold = True
        title_font.height = 220
        title_font.italic = True

        self.header_style = xlwt.XFStyle()
        self.header_style.font = header_font
        self.header_style.pattern = header_pattern

        self.title_style = xlwt.XFStyle()
        self.title_style.font = title_font
 
    def __get_case_result(self, dut, target, suite, case):
        case_list = self.result.all_test_cases(dut, target, suite)
        if case_list.count(case) > 1:
            tmp_result = []
            for case_name in case_list:
                if case == case_name:
                    test_result = self.result.result_for(dut, target, suite, case)
                    if 'PASSED' in test_result:
                        return ['PASSED', '']
                    else:
                        tmp_result.append(test_result)
            return tmp_result[-1]
        else:
            return self.result.result_for(dut, target, suite, case)

    def __write_result(self, dut, target, suite, case, test_result):
        if test_result is not None and len(test_result) > 0:
            result = test_result[0]
            if test_result[1] != '':
                result = "{0} '{1}'".format(result, test_result[1])
            if test_result[0] == 'PASSED':
                self.sheet.write(self.row, self.col + 1, result)
            else:
                self.sheet.write(
                    self.row, self.col + 1, result if len(result) < 5000 else result[:2000] + '\r\n...\r\n...\r\n...\r\n' + result[-2000:], self.failed_style)

    def __write_cases(self, dut, target, suite):
        for case in set(self.result.all_test_cases(dut, target, suite)):
            result = self.__get_case_result(dut, target, suite, case)
            self.col += 1
            if case[:5] == "test_":
                self.sheet.write(self.row, self.col, case[5:])
            else:
                self.sheet.write(self.row, self.col, case)
            self.__write_result(dut, target, suite, case, result)
            self.row += 1
            self.col -= 1

    def __write_suites(self, dut, target):
        for suite in self.result.all_test_suites(dut, target):
            self.row += 1
            self.col += 1
            self.sheet.write(self.row, self.col, suite)
            self.__write_cases(dut, target, suite)
            self.col -= 1

    def __write_nic(self, dut, target):
        nic = self.result.current_nic(dut, target)
        driver = self.result.current_driver(dut)
        kdriver = self.result.current_kdriver(dut)
        firmware = self.result.current_firmware_version(dut)
        pkg = self.result.current_package_version(dut)
        self.col += 1
        self.sheet.col(self.col).width = 32 * 256  # 32 characters
        self.sheet.write(self.row, self.col, nic, self.title_style)
        self.sheet.write(self.row+1, self.col, 'driver: ' + driver)
        self.sheet.write(self.row+2, self.col, 'kdriver: ' + kdriver)
        self.sheet.write(self.row+3, self.col, 'firmware: ' + firmware)
        if pkg is not None:
            self.sheet.write(self.row+4, self.col, 'pkg: ' + pkg)
            self.row = self.row + 1
        self.row = self.row + 3
        self.__write_suites(dut, target)
        self.col -= 1

    def __write_failed_target(self, dut, target):
        msg = "TARGET ERROR '%s'" % self.result.target_failed_msg(dut, target)
        self.sheet.write(self.row, self.col + 4, msg if len(msg) < 5000 else msg[:2000] + '\r\n...\r\n...\r\n...\r\n' + msg[-2000:], self.failed_style)
        self.row += 1

    def __write_targets(self, dut):
        for target in self.result.all_targets(dut):
            self.col += 1
            self.sheet.write(self.row, self.col, target, self.title_style)
            if self.result.is_target_failed(dut, target):
                self.__write_failed_target(dut, target)
            else:
                self.__write_nic(dut, target)
            self.row += 1
            self.col -= 1

    def __write_failed_dut(self, dut):
        msg = "PREREQ FAILED '%s'" % self.result.dut_failed_msg(dut)
        self.sheet.write(self.row, self.col + 5, msg if len(msg) < 5000 else msg[:2000] + '\r\n...\r\n...\r\n...\r\n' + msg[-2000:], self.failed_style)
        self.row += 1

    def __parse_result(self):
        for dut in self.result.all_duts():
            self.sheet.write(self.row, self.col, dut, self.title_style)
            if self.result.is_dut_failed(dut):
                self.__write_failed_dut(dut)
            else:
                self.col = self.col + 1
                self.sheet.write(self.row, self.col, self.result.current_dpdk_version(dut), self.title_style)
                self.__write_targets(dut)
            self.row += 1

    def save(self, result):
        self.__init()
        self.__add_header()
        self.row = 1
        self.col = 0

        self.result = result
        self.__parse_result()

        self.workbook.save(self.filename)
