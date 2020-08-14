from __future__ import print_function
import os, sys
from collections import Counter

__version__ = "0.9.0"

TYPE = {
    0:  'bios',
    1:  'system',
    2:  'base board',
    3:  'chassis',
    4:  'processor',
    7:  'cache',
    8:  'port connector',
    9:  'system slot',
    10: 'on board device',
    11: 'OEM strings',
    #13: 'bios language',
    15: 'system event log',
    16: 'physical memory array',
    17: 'memory device',
    19: 'memory array mapped address',
    24: 'hardware security',
    25: 'system power controls',
    27: 'cooling device',
    32: 'system boot',
    41: 'onboard device',
    }


def parse_dmi(content):
    """
    Parse the whole dmidecode output.
    Returns a list of tuples of (type int, value dict).
    """
    info = []
    lines = iter(content.strip().splitlines())
    while True:
        try:
            line = next(lines)
        except StopIteration:
            break

        if line.startswith('Handle 0x'):
            typ = int(line.split(',', 2)[1].strip()[len('DMI type'):])
            if typ in TYPE:
                info.append((TYPE[typ], _parse_handle_section(lines)))
    return info


def _parse_handle_section(lines):
    """
    Parse a section of dmidecode output

    * 1st line contains address, type and size
    * 2nd line is title
    * line started with one tab is one option and its value
    * line started with two tabs is a member of list
    """
    data = {
        '_title': next(lines).rstrip(),
        }

    for line in lines:
        line = line.rstrip()
        if line.startswith('\t\t'):
            data[k].append(line.lstrip())
        elif line.startswith('\t'):
            k, v = [i.strip() for i in line.lstrip().split(':', 1)]
            if v:
                data[k] = v
            else:
                data[k] = []
        else:
            break

    return data


def get_profile():
    content = _get_output()
    info = parse_dmi(content)
    return info

def get_device_info(info, type):
    if type == 'cpu':
        return _show(info, type)
    elif type == 'memory':
        return _show(info, type)


def _get_output():
    import subprocess
    try:
        output = subprocess.check_output(
        'PATH=$PATH:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin '
        'sudo dmidecode', shell=True)
    except Exception as e:
        print(e, file=sys.stderr)
        if str(e).find("command not found") == -1:
            print("please install dmidecode", file=sys.stderr)
            print("e.g. sudo apt install dmidecode",file=sys.stderr)

        sys.exit(1)
    return output.decode()


def _show(info, type):
    def _get(i):
        return [v for j, v in info if j == i]

    if type == 'cpu':
        cpu_list = _get('processor')
        hardware_model = [x['Version'] for x in cpu_list]
        print(dict(Counter(hardware_model)))
        return hardware_model
    elif type == 'memory':
        cnt, total, unit = 0, 0, None
        memory_list_tmp = _get('memory device')
        memory_list = []
        for index in range(len(memory_list_tmp)):
            mem = memory_list_tmp[index]
            if mem['Size'] == 'No Module Installed':
                continue
            else:
                memory_list.append(mem)
            i, unit = mem['Size'].split()
            cnt += 1
            total += int(i)
        hardware_model = [x['Manufacturer'] for x in memory_list]
        print(dict(Counter(hardware_model)))
        return hardware_model
    elif type == 'bios':
        bios = _get('bios')[0]
        print ('BIOS: %s v.%s %s Systemversion: %s' % (
            bios['Vendor'],
            bios['Version'],
            bios['Release Date'],
            system['Version']
            ))
    elif type == 'system':
        system = _get('system')[0]
        print ('%s %s (SN: %s, UUID: %s)' % (
            system['Manufacturer'],
            system['Product Name'],
            system['Serial Number'],
            system['UUID'],
            ))


if __name__ == '__main__':
    info = get_profile()
    get_device_info(info, "cpu")
    get_device_info(info, "memory")
