import socket
import logging
import math
from datetime import datetime


def main():
    logging.basicConfig(level=logging.INFO)
    print_label('3642', 'LS98347778264', '192.168.1.135', 9100)


def print_label(wk_nr: str, ls_nr: str, ip: str = '192.168.1.135', port: int = 9100):
    """
    Prints the ware basket number and the number of the delivery note on a predefined layout on a brother ql-820NWB
    :param wk_nr: Number of the ware basket
    :param ls_nr: Number of the delivery note
    :param ip: IP of the target printer
    :param port: Port of the target printer
    :return: Nothing
    """
    print_date = datetime.today().strftime('%d.%m.%Y')

    label = Label(length=29.0, width=62.0, lr_margin=3.0, tb_margin=1.5)
    label.select_landscape_orientation(0)
    label.specify_page_length()
    label.add_qr_code(wk_nr)
    label.add_text(25.0, 0.0, 10, 33, "Warenkorbnummer:")
    label.add_text(25.0, 5.0,  10, 33, wk_nr, isbold=True)
    label.add_text(25.0, 10.0, 10, 33, "Lieferscheinnummer:")
    label.add_text(25.0, 15.0, 1, 24, ls_nr, isbold=False)
    label.add_text(2.8, 20.0, 10, 33, "Druckdatum:")
    label.add_text(25.0, 20.0,  10, 33, print_date)
    label.cut_after_print(True)
    label.print(ip, port)
    return


class Label:
    def __init__(self,
                 length: float = 29.0,
                 width: float = 62.0,
                 lr_margin: float = 3.0,
                 tb_margin: float = 1.5):

        self.data = b""
        self.__select_escp_mode()
        self.__init_escp_mode()
        self.label_length = length  # lenght of the label in mm
        self.label_width = width  # Width of the label in mm
        self.lr_margin = lr_margin  # Left/Right margin in mm
        self.tb_margin = tb_margin  # Top/Bottom margin in mm
        return

    def __select_escp_mode(self):
        self.data += b"\x1B\x69\x61\x00"
        return

    def __init_escp_mode(self):
        self.data += b"\x1B\x40"
        return

    def print(self, ip, port: int = 9100):
        """
        Adds the "Start printing" command to the byte series and sends the data via tcp socket to the printer
        :param ip: IP of the printer
        :param port: Port of the raw printing service, defaults to 9100
        """
        self.data += b"\x0C"  # Print start command
        tcp_print(ip, self.data, port)
        return

    def add_text(self, x_pos: float, y_pos: float, font: int, size: int, text: str, isbold: bool = False):
        """
        Prints a text string on a defined position
        :param x_pos: position in mm from the left
        :param y_pos: position in mm from the top
        :param font: font type, which will be used
        :param size: font size in dots
        :param text: Text which will be shown
        :param isbold: (optional) print the text bold
        :return:
        """
        self.specify_horizontal_pos(x_pos)
        self.specify_vertical_pos(y_pos)
        self.select_font_and_char_size(font, size)
        if isbold:
            self.apply_bold()

        self.data += bytes(text, 'utf-8')

        if isbold:
            self.cancel_bold()
        return

    def select_landscape_orientation(self, orientation: int):
        """
        Specify landscape orientation
        :param orientation: 1 = applies the landscape orientation, 0 = cancels the landscape orientation
        """

        if not (orientation == 1 or orientation == 0):
            raise ValueError("orientation must be int(1) oder int(0)")

        # Add the command
        self.data += b"\x1B\x69\x4C"

        # Add the parameters
        self.data += orientation.to_bytes(1, 'big')
        return

    def cut_after_print(self, arg: bool = True):
        """
        Specifies cutting after printing
        :param arg: true = cut after print (default), false = dont cut after print
        """
        # Add the command
        self.data += b"\x1B\x69\x43"

        # Add the parameter
        if arg:
            self.data += b"\x01"
        else:
            self.data += b"\x00"

    def specify_page_length(self):
        """
        Specifies the page length
        :return:
        """

        if (self.label_length < 0) or (self.label_length > 677):
            raise ValueError("The Label length can be set between 0 mm and 677 mm")

        # Calculate the page length in dots
        margin = mm_to_dots(self.lr_margin) * 2
        len_in_dots = mm_to_dots(self.label_length) - margin

        # Calculate the hex-values of the parameters
        m_l, m_h = dots_to_hex(len_in_dots)

        # Add Command
        self.data += b"\x1B\x24\x02\x00"

        # Add Parameters
        self.data += m_l  # mL
        self.data += m_h  # mH
        return

    def add_qr_code(self, wk_nr: str):
        """
        Adds a qr code with the number of the ware basket to the top left corner of the label
        :param wk_nr: Number of the ware basket, which will be encode within the qr code
        :return: Nothing
        """
        # Add command
        self.data += b"\x1B\x69\x51"

        # Add Parameters
        self.data += b"\x0a"  # Cell-Size
        self.data += b"\x02"  # Model
        self.data += b"\x00"  # Structured Append setting
        self.data += b"\x00"  # Code-Number
        self.data += b"\x00"  # Number of partitions
        self.data += get_parity_byte(wk_nr)
        self.data += b"\x02"  # Error correction level
        self.data += b"\x00"  # Data input method
        self.data += bytes(wk_nr, 'utf-8')    # Add data
        self.data += b'\\\\\\'

    def specify_horizontal_pos(self, x_in_mm: float):
        """
        Specifyesthe horizontal position
        :param x_in_mm: distance from the left side in mm
        :return: Nothing
        """
        if x_in_mm > self.label_length:
            raise ValueError("Position outside of the label")

        # Get hex-values of the parameter
        n1, n2 = dots_to_hex(mm_to_dots(x_in_mm))
        # Add command
        self.data += b"\x1B\x24"

        # Add Parameters
        self.data += n1
        self.data += n2
        return

    def specify_vertical_pos(self, y_in_mm: float):
        """
        Specifyesthe vertical position
        :param y_in_mm: distance from the top side in mm
        :return: Nothing
        """
        if y_in_mm > self.label_width:
            raise ValueError("Position outside of the label")

        # Get hex-values of the parameter
        n1, n2 = dots_to_hex(mm_to_dots(y_in_mm))
        # Add command
        self.data += b"\x1B\x28\x56\x02\x00"

        # Add Parameters
        self.data += n1
        self.data += n2
        return

    def select_font_and_char_size(self, font_number: int, char_size_in_dots: int):
        """
        Select between 8 diffrent font types (these are specified in the ESP/C command reference page 23"
        :param font_number: 0 to 4 (Bitmap Fonts) and 9 to 10 (Outline Fonts)
        :param char_size_in_dots (= nL + nH * 256)
        :return: Nothing
        Bitmap Fonts only valid with nH = 0 and nL = 24, 32, 48 dots
        Outline Fonts only valid with   nH = 1 and nL = 11, 44, 77, 111, 144
                                        nH = 0 and nL = 33, 38, 42, 46, 50, 58, 67, 75, 83, 92, 100, 117, 133, 150
                                                        167, 200, 233
        """

        if not (0 <= font_number <= 4) and not (9 <= font_number <= 11):
            raise ValueError("Selected font does not exsist")

        # Add command (font selection)
        self.data += b"\x1B\x6B"

        # Add Parameter (font selection) n
        n = font_number.to_bytes(1, 'big')
        self.data += n

        if 0 < font_number < 4:
            size_list = (24, 32, 48)
            if char_size_in_dots not in size_list:
                raise ValueError(f"{char_size_in_dots} is not supported with the selected font")

        if 9 < font_number < 11:
            size_list = (33, 38, 42, 46, 50, 58, 67, 75, 83, 92, 100, 117, 133, 150, 167, 200, 233)
            if char_size_in_dots not in size_list:
                raise ValueError(f"char size: {char_size_in_dots} is not supported with the selected font")

        # Add command (font size selection)
        self.data += b"\x1B\x58\x00"

        # Add Parameter (font size)
        self.data += char_size_in_dots.to_bytes(1, 'big')
        self.data += b"\x00"
        return

    def apply_bold(self):
        """
        Prints the subsequent text in bold.
        This command is valid anywhere in a text line.
        :return: Nothing
        """
        # Add command
        self.data += b"\x1B\x45"
        return

    def cancel_bold(self):
        """
        Cancels the bold style.
        This command is valid anywhere in a text line.
        :return: Nothing
        """
        # Add command
        self.data += b"\x1B\x46"
        return

    def specify_min_line_feed(self, lf_in_mm: float):
        """
        Specifyes the minimum line feed in mm
        :param lf_in_mm: line feed in mm
        :return:
        """
        # Add command
        self.data += b"\x1B\x33"

        lf_in_dots = mm_to_dots(lf_in_mm)
        if not 0 < lf_in_dots < 255:
            raise ValueError("Line feed is to big")

        # Add Parameter
        self.data += lf_in_dots.to_bytes(1, 'little')

    def specify_line_feed(self, lf_multiplier: int):
        """
        Specifyes the minimum line feed in mm
        :param lf_multiplier: line feed multiplier each, line feed is 5 dots = 4,2mm; 0 < lf_multiplier < 255
        :return: Nothing
        """
        # Add command
        self.data += b"\x1B\x41"

        if not 0 < lf_multiplier < 255:
            raise ValueError("Line feed is to big")

        # Add Parameter
        self.data += lf_multiplier.to_bytes(1, 'little')


def mm_to_dots(len_in_mm: float):
    """
    Converts a length provided in mm to dots
    :param len_in_mm: Lenght in mm
    :return: Length in dots
    """

    if len_in_mm < 0:
        raise ValueError("Only positive lengths can be converted")

    if not isinstance(len_in_mm, float):
        raise ValueError("length must be provided as float")

    len_in_dots = int(round(len_in_mm * 11.811))
    return len_in_dots


def dots_to_hex(dots: int):
    """
    calculates the most- and least significant hex values which are representing distances
    distance in dots = hex(n1) + hex(n2) * 256
    exmaple: 767 dots = 0xE9 + 0x02 * 256 [0xE9 = 233, 0x02 = 2] -> 2 * 256 + 233 = 767
    :param dots: Distances by the unit dots as specified in the ESP/C command reference
    :return: distances encoded as hex values as specified in the ESP/C command reference
    """

    if dots < 0:
        raise ValueError("provided dots must be greater than 0")

    if dots > 8000:
        raise ValueError("a length greater than 8000 dots is not allowed")

    high = math.floor(dots/256)
    low = dots-(high*256)

    high = high.to_bytes(1, 'big')
    low = low.to_bytes(1, 'big')
    return low, high


def tcp_print(printer_ip: str, print_message: bytes, printer_port: int = 9100):
    """
    Prints a message in RAW-Format on the specified printer
    :param printer_ip:  IP-Adresse of the printer
    :param printer_port: Port of the printer (Defaults to 9100)
    :param print_message: the message, which will be send
    :return:
    """
    logging.info(f"IP: {printer_ip}")
    logging.info(f"Port: {printer_port}")
    logging.info(f"Port: {print_message}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((printer_ip, printer_port))
    sock.sendall(print_message)
    sock.close()
    return


def get_parity_byte(input_data: str):
    len_input_data = len(input_data)
    parity_byte_as_int = None

    if not isinstance(input_data, str):
        raise TypeError("input_data must be a string")

    if len_input_data < 1:
        raise ValueError("number of chars must be > 1")

    for ii, char in enumerate(input_data):
        char_as_byte = bytes(char, 'utf-8')
        char_as_int = int.from_bytes(char_as_byte, 'big')
        if ii == 0:
            parity_byte_as_int = char_as_int
        else:
            parity_byte_as_int ^= char_as_int

    return parity_byte_as_int.to_bytes(1, 'big')


if __name__ == "__main__":
    main()
