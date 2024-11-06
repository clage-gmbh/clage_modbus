#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Python command line application to control a CLAGE continuous-flow water heater.
#

from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
# What type of modbus client do we need:
try:
    from pymodbus.client.sync import ModbusTcpClient
    from pymodbus.client.sync import ModbusSerialClient
except ImportError:
    from pymodbus.client import ModbusTcpClient
    from pymodbus.client import ModbusSerialClient
import datetime
import pytz
import logging
import difflib
import clage_param
import clage_modbus_mapping
import argparse
import sys
import glob
import serial
import re
import dateutil.parser
import time
import os
import ipaddress


class clage_modbus:
    # Version of this class and tool.
    c_version = '0.1.8'
    c_clage_magic = 0xC1A6

    def examples(void):
        print("""Examples:
The default modbus server address of a CLAGE continuous-flow water heater
is derived from the last two digits of its serial number. In these examples
the device has S/N xxxxx97. If your device has S/N xxxxx00 the server
address is 100, not 0 which is the modbus broadcast address.

The default serial port is the last one found e.g. if you are using an
MS-OS (Win) providing COM1, COM3 and COM5, the default will be COM5.

  Check for options and their defaults:
    ./clage_modbus.py -h

  Read temperature setting from CLAGE continuous-flow water heater with modbus server ID 97:
    ./clage_modbus.py --server_id=97 --read temp_setpoint_C10

Read and write can take multiple values and multiple occurrences.
Options can be used in short format.
Read, write and run can be used several times and with several values mixed.
But the order of execution is always read, write and after that run.
              
  Read temperature setting and water flow limit from server ID 97:
    ./clage_modbus.py -s97 -r temp_setpoint_C10 flow_max_lmin10
  or
    ./clage_modbus.py -s97 -r temp_setpoint_C10 -r flow_max_lmin10

  Read mixed parameters:
    ./clage_modbus.py -s97 -r temp_setpoint_C10 epoch_s wlan_ap

  Read temperature setting and change to new value:
    ./clage_modbus.py -s97 -r temp_setpoint_C10 -w temp_setpoint_C10=48.0

  Read temperature setting and change to new raw register value:
    ./clage_modbus.py -s97 -r temp_setpoint_C10 -w temp_setpoint_C10:480

  Read complete list of all parameters and write with ISO timestamps to CSV table.
    ./clage_modbus.py -s97 --read list --format csv --timestamp iso >list.csv

  Toggle the temperature setting once per second. Read back and protocol to CSV with epoch timestamp.
    ./clage_modbus.py -s97 -a t=temp_setpoint_C10 -te -fc -cR t=32 t w:1s t=47 t w:1s
""")

    def flat_list(self, list):
        try:
            return [item for sublist in list for item in sublist]
        except:
            return list

    def isotime(self, epoch=None):
        if epoch:
            d = datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc)
        else:
            d = datetime.datetime.now(tz=pytz.UTC)
        return d.isoformat(timespec='seconds').replace('+00:00', 'Z')

    def print_error(self, error):
        print(error, file=sys.stderr)

    def serial_ports(self):
        """ Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A sorted list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # Only take care of first 100 numbered devices (no named symbolic links et al.)
            ports = glob.glob('/dev/ttyUSB[0-9]') + glob.glob('/dev/ttyUSB[0-9][0-9]')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.[0-9]') + glob.glob('/dev/tty.[0-9][0-9]')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException) as e:
                print(f'serial exception: {e}')
                pass
            except e:
                print(f'exception: {e}')
                pass
        return sorted(result, key=lambda s: int(re.search(r'\d+', s).group()))

    def replace_alias(self, name):
        return self.alias[name] if name in self.alias else (name,0)

    def get_map(self):
        map_v = len(clage_modbus_mapping.clage_modbus_map)
        if map_v < self.map_version[1]:
            self.print_error(
                f'mapping table up to version {map_v} but device is {self.map_version[1]}. Do update clage_modbus_mapping.py')
        return clage_modbus_mapping.clage_modbus_map[self.map_version[1]-1]

    def get_map_entry(self, param_name, exemplar=0):
        return self.get_map()[(param_name, exemplar)]

    def param_element(self, param_name):
        # TODO: Do parse for [n]
        element = 0
        return (param_name, element)

    def check_param_name(self, param_name):
        (param_name,element) = self.param_element(param_name)
        (param_name,element) = self.replace_alias(param_name)
        if not param_name in self.param_names:
            self.print_error(f'unknown parameter name: {param_name}')
            alt_names = difflib.get_close_matches(
                param_name, self.param_names, n=5, cutoff=0.4)
            if alt_names:
                self.print_error('e.g.:')
                for alt_name in difflib.get_close_matches(param_name, self.param_names, n=5, cutoff=0.3):
                    self.print_error(
                        f'  {alt_name} : {self.get_map_entry(alt_name,0)[2]}')
            else:
                self.print_error(
                    '  do use option -l to list valid parameter names.\n')
                # parser.print_help()
            sys.exit(2)
        return (param_name,element)

    def setup_aliases(self):
        self.alias = {}
        for ali in self.args.alias:
            if '=' in ali:
                (a, p) = ali.split('=')
                if a in self.alias:
                    self.print_error(f'alias {ali} already defined')
                    sys.exit(2)
                self.alias[a] = self.check_param_name(p)
            else:
                self.print_error(f'invalid alias {ali}')
                sys.exit(2)

    def setup_parser(self):
        # Take some defaults from environment.
        default_server_id = os.environ.get('CLAGE_MODBUS_SERVER_ID')
        default_ip = os.environ.get('CLAGE_MODBUS_IP_ADDR')
        default_port = os.environ.get('CLAGE_MODBUS_IP_PORT')
        default_port = 502 if None == default_port else default_port
        default_uart = os.environ.get('CLAGE_MODBUS_UART')
        if None == default_uart:
            ports = self.serial_ports()
            default_uart = ports[-1] if ports else None
        default_baudrate = os.environ.get('CLAGE_MODBUS_BAUDRATE')
        default_baudrate = 19200 if None == default_baudrate else default_baudrate
        default_parity = os.environ.get('CLAGE_MODBUS_PARITY')
        default_parity = 'N' if None == default_parity else default_parity

        # Define command line options using defaults.
        self.parser = argparse.ArgumentParser(description='Command line tool to control a CLAGE continuous-flow water heater by modbus RTU',
                                              epilog='(c) copyright 2023 by CLAGE GmbH')
        self.parser.add_argument('-v', '--verbose', action='store_true', default=False,
                                 help='more output')
        self.parser.add_argument('-x', '--examples', action='store_true', default=False,
                                 help='print some examples')
        self.parser.add_argument('-i', '--ip_addr', default=default_ip, type=ipaddress.IPv4Address,
                                 help='TCP/IP address if Modbus TCP shall be used (e.g. using a gateway).')
        self.parser.add_argument('-P', '--port', default=default_port,
                                 help=f'TCP/IP port number (default {default_port})')
        self.parser.add_argument('-u', '--uart', default=default_uart,
                                 help=f'serial UART port to be used (default is {default_uart})')
        self.parser.add_argument('-b', '--baudrate', default=default_baudrate, type=int,
                                 help=f'Baudrate to use e.g. 9600, 19200, ... (default {default_baudrate})')
        self.parser.add_argument('-p', '--parity', default=default_parity,
                                 help=f'serial line parity N, O or E (default {default_parity})')
        if default_server_id:
            self.parser.add_argument('-s', '--server_id', default=default_server_id, type=int,
                                     help='Modbus RTU server address of the CLAGE device.' +
                                     ' Factory default are the last two digits of the S/N.' +
                                     ' If S/N xxxx00 the address is 100. (default by environment {default_server_id})')
        else:
            self.parser.add_argument('-s', '--server_id', required=True, type=int,
                                     help='Modbus RTU server address of the CLAGE device. Factory default are the last two digits of the S/N. If S/N xxxx00 the address is 100.')
        self.parser.add_argument('-l', '--list', default=False, action='store_true',
                                 help='Print list of all valid parameters')
        self.parser.add_argument('-r', '--read', nargs='*', default=[], action='append',
                                 help='Parameter(s) to read from device (e.g. temp_setpoint_C10 or flow_max_lmin10 ). If "list" is given as the only one, the complete list of parameters is read.')
        self.parser.add_argument('-w', '--write', nargs='*', default=[], action='append',
                                 help='Parameter(s) and value to write to device (e.g. raw value temp_setpoint_C10:385 set to 38.5°C or temp_setpoint_C10=38.5 )')
        self.parser.add_argument('-R', '--run', nargs='*', default=[], action='append',
                                 help='Run a sequence of read, write and wait (cyclic if -c)')
        self.parser.add_argument('-c', '--cycle', action='store_true', default=False,
                                 help='run through sequence cyclically')
        self.parser.add_argument('-a', '--alias', nargs='*', default=[], action='append',
                                 help='Define an alias (shortcut) for a parameter (e.g. t=temp_setpoint_C10 or f=flow_max_lmin10)')
        self.parser.add_argument('--log', action='store_true', default=False,
                                 help='print out logging messages')
        self.parser.add_argument('-f', '--format', default='default',
                                 help='Format of output (default, raw or csv)')
        self.parser.add_argument('-t', '--timestamp', default='no',
                                 help='Format of timestamp (default is no,[no, iso, epoch]')
        self.parser.add_argument('--retry', default=3, type=int,
                                 help='Maximum number of retries (default is 3)')
        self.parser.add_argument('-V', '--version', action='store_true', default=False,
                                 help='show version information')

    def do_parse(self, args=None, namespace=None):
        self.args = self.parser.parse_args(args, namespace)

    def print_version(self):
        print(f'CLAGE modbus command line tool version {self.c_version}')
        print(
            f'CLAGE modbus register mapping version {self.map_version[1]}.{self.map_version[2]} used on this device')

    def setup_args(self):
        # read, write, run and alias can take multiple values in multiple occurrences
        self.args.read = self.flat_list(self.args.read)
        self.args.write = self.flat_list(self.args.write)
        self.args.run = self.flat_list(self.args.run)
        self.args.alias = self.flat_list(self.args.alias)
        # Shall we print some examples?
        if self.args.examples:
            self.examples()
            sys.exit(0)
        # List parameters to read or write if verbose.
        if self.args.verbose:
            if self.args.read:
                print(f'Read: {self.args.read}')
            if self.args.write:
                print(f'Write: {self.args.write}')

    def check_args(self):
        self.setup_parser()
        self.do_parse()
        self.setup_args()

    def timestamp(self, sep=''):
        if self.args.timestamp in ('no'):
            return ''
        elif self.args.timestamp in ('iso'):
            return self.isotime() + sep
        elif self.args.timestamp in ('epoch'):
            return f'{int(time.time())}{sep}'
        else:
            self.print_error(
                f'unknown timestamp {self.args.timestamp} valid are "no", "iso" or "epoch"')
            sys.exit(2)

    def connect(self):
        # Setup the type of modbus client to use:
        if None != self.args.ip_addr:
            self.modbus_client = ModbusTcpClient(
                f'{self.args.ip_addr}', port=self.args.port, retries=self.args.retry)
            if self.args.verbose:
                print(f'Using Modbus TCP {self.args.ip_addr}:{self.args.port}')
        else:
            # Default is framer=FramerType.RTU (method='rtu' is outdated)
            # Default bytesize=8, stopbits=1, handle_local_echo=False
            self.modbus_client = ModbusSerialClient(
                port=self.args.uart, baudrate=self.args.baudrate, parity=self.args.parity, timeout=1, retries=self.args.retry)
            if self.args.verbose:
                print(
                    f'Using Modbus RTU {self.args.uart},{self.args.baudrate},{self.args.parity}')
        # Check for CLAGE device magic number and mapping version.
        try:
            if not self.modbus_client.connect():
                if self.args.verbose:
                    print('modbus_client.connect() failed')
                raise Exception("failed to connect")
            rr = self.get_ain(400, 3)
            if rr.isError():
                raise Exception(
                    f'connection failed or not a CLAGE device: {rr}')
            self.map_version = rr.registers
        except AttributeError as e:
            self.print_error(f'{e}')
            raise Exception(f'make sure {self.args.uart} is available.')
        if self.c_clage_magic != self.map_version[0]:
            raise Exception(
                f'not a CLAGE device AIN[400] != 0x{self.c_clage_magic:X}')
        if self.args.version:
            self.print_version()

        # List of signal names (needs further read mapping version)
        param_names = []
        for (name, x) in self.get_map().keys():
            if not name in ('end'):
                param_names.append(name)
        self.param_names = sorted(set(param_names))
        self.setup_aliases()
        # Check if shall list parameter names.
        if self.args.list:
            for s in self.param_names:
                print(f'{s} : {self.get_map_entry(s,0)[2]}')
            sys.exit(0)

        # Check for word order (Old devices default was little endian)
        self.is_word_big_endian = False
        try:
            rr = self.get_dout( 402, 1)
            if rr.isError():
                if self.args.verbose:
                    print( "Old firmware. Assuming little word endianness.")
            else:
                self.is_word_big_endian = rr.bits[0]
                if self.args.verbose:
                    print( 'Word endianness ' + ('big' if self.is_word_big_endian else 'little'))
        except AttributeError as e:
            self.print_error(f'{e}')
            raise Exception(f'failed to read word endianness')

        if self.args.log:
            format = (
                '%(asctime)-15s %(levelname)-8s %(module)-12s:%(lineno)-6s %(message)s')
            logging.basicConfig(format=format)
            self.log = logging.getLogger("pymodbus")
            self.log.setLevel(logging.DEBUG)

    def get_num_registers(self, param_name):
        # Lookup parameter type and unit.
        (type, unit) = clage_param.clage_param_map[self.check_param_name(param_name)[0]]
        if 'bool' == type:
            return 1
        if 'u8' == type:
            return 1
        elif 'i8' == type:
            return 1
        elif 'u16' == type:
            return 1
        elif 'i16' == type:
            return 1
        elif 'u32' == type:
            return 2
        elif 'i32' == type:
            return 2
        elif 'float' == type:
            return 2
        elif 'u64' == type:
            return 4
        elif 'i64' == type:
            return 4
        elif 'string' == type:
            return 1  # at least but may be more
        else:
            assert False, f'unknown parameter type: {type}'

    def get_aout(self, address, count):
        return self.modbus_client.read_holding_registers(
            address, count, slave=self.args.server_id)

    def get_ain(self, address, count):
        return self.modbus_client.read_input_registers(
            address, count, slave=self.args.server_id)

    def get_dout(self, address, count):
        return self.modbus_client.read_coils(
            address, count, slave=self.args.server_id)

    def get_din(self, address, count):
        return self.modbus_client.read_discrete_inputs(
            address, count, slave=self.args.server_id)

    def print_default(self, string):
        print(self.timestamp(': ')+string)

    def print_raw(self, param_name, exemplar, value, comment):
        print(
            f'{self.timestamp(", ")}{param_name:<24}, {exemplar:3d}, {value:<12}, {comment}')

    def print_csv(self, param_name, exemplar, value, comment):
        print(
            f'{self.timestamp(", ")}{param_name:<24}, {exemplar:3d}, {value:<12}, {self.get_base_unit(param_name):<10}, {comment}')

    def print_wrong_format(self):
        self.print_error(
            f'unknown format {self.args.format}. Do set option --format correct.')
        sys.exit(2)

    def get_value(self, param_name, exemplar=None, retry=0):
        (param_name, exemplar_2) = self.check_param_name(param_name)
        if None == exemplar:
            exemplar = exemplar_2
        # Lookup register address
        [p_type, p_addr, p_comment] = self.get_map_entry(param_name, exemplar)
        p_size = self.get_num_registers(param_name)
        if self.args.verbose:
            print(
                f'request {param_name}[{exemplar}] as {p_type}[{p_addr}] count {p_size}')
        if 'aout' == p_type:
            rr = self.get_aout(p_addr, p_size)
        elif 'ain' == p_type:
            rr = self.get_ain(p_addr, p_size)
        elif 'dout' == p_type:
            rr = self.get_dout(p_addr, p_size)
        elif 'din' == p_type:
            rr = self.get_din(p_addr, p_size)
        else:
            assert False, f'type {p_type} not implemented'
        if rr.isError():
            if 'No Response' in str(rr) and retry < self.args.retry:
                return self.get_value(param_name, exemplar, retry+1)
            if self.args.format in ('d', 'default'):
                # Human readable output format.
                self.print_default(
                    f'read of {param_name}[{exemplar}] failed: {rr}')
            elif self.args.format in ('raw', 'r'):
                # Machine readable raw values
                self.print_raw(param_name, exemplar, '???', rr)
            elif self.args.format in ('csv', 'c'):
                # Machine readable base values
                self.print_csv(param_name, exemplar, '???', rr)
            else:
                self.print_wrong_format()
            return None
        # Check that not an error reply.
        assert(rr.function_code < 0x80)
        # Lookup parameter type and unit.
        (type, unit) = clage_param.clage_param_map[param_name]
        if p_type in ('din', 'dout'):
            if self.args.verbose:
                print(f'got payload {rr.bits} for {type} {unit}')
            assert 'bool' == type, f'non boolean discrete {param_name}'
            return rr.bits[0]
        else:
            if self.args.verbose:
                print(f'got payload {rr.registers} for {type} {unit}')
            # Parse payload according to parameter type.
            payload = BinaryPayloadDecoder.fromRegisters(
                rr.registers, byteorder=Endian.BIG, wordorder=Endian.BIG if self.is_word_big_endian else Endian.LITTLE)
            if 'bool' == type:
                return payload.decode_16bit_uint()
            elif 'u8' == type:
                return payload.decode_16bit_uint()
            elif 'i8' == type:
                return payload.decode_16bit_int()
            elif 'u16' == type:
                return payload.decode_16bit_uint()
            elif 'i16' == type:
                return payload.decode_16bit_int()
            elif 'u32' == type:
                return payload.decode_32bit_uint()
            elif 'i32' == type:
                return payload.decode_32bit_int()
            elif 'float' == type:
                return payload.decode_32bit_float()
            elif 'u64' == type:
                return payload.decode_64bit_uint()
            elif 'i64' == type:
                return payload.decode_64bit_int()
            elif 'string' == type:
                # TODO: Find tailing zero ?
                size = len(payload._payload) - payload._pointer
                return payload.decode_string(size)
            else:
                assert False, f'unknown parameter type: {type}'

    def get_base_value(self, param_name, value):
        if None == value:
            return None
        # Lookup parameter type and unit.
        (type, unit) = clage_param.clage_param_map[param_name]
        if 'epoch' == unit:
            return self.isotime(value)
        elif unit in ('C10', 'C10main', 'lmin10', 'lmin10max', 'kW10'):
            return '%.1f' % (float(value)/10.0)
        else:
            return f'{value}'

    def get_base_unit(self, param_name):
        # Lookup parameter type and unit.
        (type, unit) = clage_param.clage_param_map[param_name]
        if 'epoch' == unit:
            return 'UTC'
        elif unit in ('C', 'C10', 'C10main'):
            return '°C'
        elif unit in ('lmin', 'lmin10', 'lmin10max'):
            return 'l/min'
        elif unit in ('kW', 'kW10'):
            return 'kW'
        elif unit in ('PC'):
            return '%'
        elif unit in ('none', 'u16ctrl', 'parity'):
            return ''
        else:
            return unit

    def print_param(self, param_name, exemplar=None):
        (param_name, exemplar_2) = self.check_param_name(param_name)
        if None == exemplar:
            exemplar = exemplar_2
        value = self.get_value(param_name, exemplar)
        if None == value:
            return
        # Lookup register address
        [p_type, p_addr, p_comment] = self.get_map_entry(param_name, exemplar)
        # Lookup parameter type and unit.
        (type, unit) = clage_param.clage_param_map[param_name]
        if self.args.format in ('default', 'd'):
            # Human readable output format.
            self.print_default(
                f'{value} = {self.get_base_value(param_name, value)} {self.get_base_unit(param_name)} : {p_comment}')
        elif self.args.format in ('raw', 'r'):
            # Machine readable raw values
            self.print_raw(param_name, exemplar, value, p_comment)
        elif self.args.format in ('csv', 'c'):
            # Machine readable base values
            self.print_csv(param_name, exemplar, self.get_base_value(
                param_name, value), p_comment)
        else:
            self.print_wrong_format()

    def set_aout(self, address, value_list):
        if 1 == len(value_list):
            return self.modbus_client.write_register(address, value_list[0], slave=self.args.server_id)
        else:
            return self.modbus_client.write_registers(address, value_list, slave=self.args.server_id)

    def set_dout(self, address, value_list):
        if 1 == len(value_list):
            return self.modbus_client.write_coil(address, value_list[0], slave=self.args.server_id)
        else:
            return self.modbus_client.write_coils(address, value_list, slave=self.args.server_id)

    def set_raw_value(self, param_name, value):
        (param_name, exemplar) = self.check_param_name(param_name)
        # Lookup parameter type and unit.
        (type, unit) = clage_param.clage_param_map[param_name]
        # Lookup register address
        [p_type, p_addr, p_comment] = self.get_map_entry(param_name, 0)
        if self.args.verbose:
            print(
                f'set raw: {param_name}:{value} to {p_type} at {p_addr} as {type}')
        if p_type in ('din', 'dout'):
            assert 'bool' == type, f'non boolean discrete {param_name}'
            wr = self.set_dout(p_addr, [0 != value])
        else:
            payload = BinaryPayloadBuilder(
                byteorder=Endian.BIG, wordorder=(Endian.BIG if self.is_word_big_endian else Endian.LITTLE))
            if 'bool' == type:
                payload.add_16bit_uint(value)
            elif 'u8' == type:
                payload.add_16bit_uint(value)
            elif 'i8' == type:
                payload.add_16bit_int(value)
            elif 'u16' == type:
                payload.add_16bit_uint(value)
            elif 'i16' == type:
                payload.add_16bit_int(value)
            elif 'u32' == type:
                payload.add_32bit_uint(value)
            elif 'i32' == type:
                payload.add_32bit_int(value)
            elif 'float' == type:
                payload.add_32bit_float(value)
            elif 'u64' == type:
                payload.add_64bit_uint(value)
            elif 'i64' == type:
                payload.add_64bit_int(value)
            elif 'string' == type:
                payload.add_string(value)
                payload.add_8bit_uint(0)
            else:
                assert False, f'unknown parameter type: {type}'
            if self.args.verbose:
                print(f'write {payload.to_registers()} to AOUT {p_addr}')
            wr = self.set_aout(p_addr, payload.to_registers())
        # Check that not an error reply.
        assert(wr.function_code < 0x80)

    def set_base(self, param_name, base):
        (param_name, exemplar) = self.check_param_name(param_name)
        # Lookup parameter type and unit.
        (type, unit) = clage_param.clage_param_map[param_name]
        if 'epoch' == unit:
            # Assume time to be in ISO format.
            self.set_raw_value(
                param_name, dateutil.parser.isoparse(base).timestamp())
        elif unit in ('C10', 'C10main', 'lmin10', 'lmin10max'):
            self.set_raw_value(param_name, int(round(float(base)*10.0)))
        else:
            assert False, f'no base value supported for parameter {param_name}'

    def set_any(self, string):
        is_raw = ':' in string
        is_base = '=' in string
        if is_raw == is_base:
            if is_raw:
                self.print_error(
                    f'wrong write parameter syntax: ":" (raw) and "=" (base)')
                sys.exit(2)
            else:
                self.print_error(
                    f'wrong write parameter syntax: neither raw (:) or base (=) value')
                sys.exit(2)
        if is_raw:
            (p, v) = string.split(':')
            self.set_raw_value(p, int(v))
        elif is_base:
            (p, b) = string.split('=')
            self.set_base(p, b)

    def get_seconds(self, string):
        r = re.search(r'([0-9.]+)(.*)', string)
        # Check for float or int number followed by unit string.
        if 2 != len(r.groups()):
            self.print_error(
                f'time for wait: needs to be a float or integer followed by a unit (ms, s, min, h, d, w)')
            sys.exit(2)
        val = float(r.group(1))
        unit = r.group(2)
        if 'ms' == unit:
            val /= 1000.0
        elif 's' == unit:
            pass
        elif 'min' == unit:
            val *= 60.0
        elif 'h' == unit:
            val *= (60.0*60.0)
        elif 'd' == unit:
            val *= (60.0*60.0*24.0)
        elif 'w' == unit:
            val *= (60.0*60.0*24.0*7.0)
        else:
            self.print_error(f'time for wait: with unknown unit {unit}')
            sys.exit(2)
        if self.args.verbose:
            print(f'waiting for {val} seconds')
        return val

    def do_step(self, step):
        is_raw = ':' in step
        is_base = '=' in step
        if is_raw and is_base:
            self.print_error(
                f'wrong step syntax in running sequence using ":" and "="')
            sys.exit(2)
        elif is_raw:
            (p, v) = step.split(':')
            if p in ('wait', 'w'):
                time.sleep(self.get_seconds(v))
            else:
                self.set_raw_value(p, int(v))
        elif is_base:
            (p, b) = step.split('=')
            if p in ('wait', 'w'):
                time.sleep(self.get_seconds(v))
            else:
                self.set_base(p, b)
        else:
            self.print_param(step)

    def do_read_list(self):
        for (r, e) in sorted(self.get_map().keys()):
            if r in ('end'):
                continue
            if self.args.verbose:
                [p_type, p_addr, p_comment] = self.get_map_entry(r, e)
                if 0 == e:
                    print(f'read {r} as {p_type}({p_addr}) :')
                else:
                    print(f'read {r}[{e}] as {p_type}({p_addr}) :')
            if (0 == e):
                print(f'{r}: ', end = '')
            else:
                print(f'{r}[{e}]: ', end = '')
            self.print_param(r, e)

    def do_read(self):
        # If only parameter to list is "list", do list all.
        if 1 == len(self.args.read) and self.args.read[0] in ('l', 'list'):
            self.do_read_list()
        else:
            for r in self.args.read:
                self.print_param(r)

    def do_write(self):
        for w in self.args.write:
            self.set_any(w)

    def do_run(self):
        while True:
            for s in self.args.run:
                self.do_step(s)
            if not self.args.cycle:
                break

    def do_dump(self):
        print(
            f'RTU Client: {self.modbus_client} => {self.modbus_client.__dir__()}')
        print(
            f'RTU Transaction: {self.modbus_client.transaction} => {self.modbus_client.transaction.__dir__()}')
        print(
            f'RTU Socket: {self.modbus_client.socket} => {self.modbus_client.socket.__dir__()}')
        print(
            f'RTU Framer: {self.modbus_client.framer} => {self.modbus_client.framer.__dir__()}')

    def __str__(self):
        return f'{self.args}'


def main():
    while True:
        try:
            c = clage_modbus()
            # Parse command line.
            c.check_args()
            # Open serial device
            c.connect()
            # Read from CLAGE device
            c.do_read()
            # Write to CLAGE device
            c.do_write()
            # Run sequence if any
            c.do_run()
        # Finish by keyboard
        except KeyboardInterrupt:
            print("finish")
            sys.exit(0)
        # Finish or retry by any other exception.
        except Exception as e:
            print(e)
        if not c.args.cycle:
            print("finish")
            sys.exit(0)
        print("restart ...")
        time.sleep(2)


# Start main() if called directly (not included)
if __name__ == "__main__":
    main()

# EOF
