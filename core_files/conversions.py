
def capitalized_hex(addr):
    string = hex(addr)
    string = string.upper()

    string = string[2:]
    string = '0x' + string

    return string


def HEX(addr):
    return capitalized_hex(addr)


def HEX_LST(bytes):
    return str([HEX(byte) for byte in bytes])


def hex_to_text(convert):
    with open('Files/Table.txt') as f:
        lines = f.read().splitlines()
    for i in range(0, len(lines)):
        lines[i] = lines[i].split('=')

    result = ""

    while convert != '':
        char = convert[:2]
        convert = convert[2:]

        for element in lines:
            if element[0] == char:
                result += (element[1])
    return result
