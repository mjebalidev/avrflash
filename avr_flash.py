import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import serial.tools.list_ports

F_CPU = 1600000  # 16MHz
CC = "avr-gcc"
OBJCOPY = "avr-objcopy"
TARGET = "main_c"
DATA_FOLDER = "data"
CFLAGS = "-std=c99 -Wall -g -Os"  # Add more flags as needed

class AVRFlashGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AVR Flash Script GUI")

        self.mcu_options = ["atmega328p", "atmega328", "atmega2560", "atmega32u4"]  # Add more as needed

        self.selected_mcu = tk.StringVar(value=self.mcu_options[0])
        self.serial_port_var = tk.StringVar()

        self.src_files = []
        self.hdr_files = []
        self.last_build_folder = None  # To store the path of the last build folder

        self.programmer_options = ["arduino", "xplainedmini"]
        self.selected_programmer = tk.StringVar(value=self.programmer_options[0])

        # Table for selected C files
        self.c_files_tree = ttk.Treeview(self, columns=('C Files',), show='headings', height=10)
        self.c_files_tree.heading('C Files', text='Selected C Files')
        self.c_files_tree.grid(row=0, column=0, padx=10, pady=10, rowspan=4, sticky='nsew')

        # Table for selected H files
        self.h_files_tree = ttk.Treeview(self, columns=('H Files',), show='headings', height=10)
        self.h_files_tree.heading('H Files', text='Selected H Files')
        self.h_files_tree.grid(row=0, column=1, padx=10, pady=10, rowspan=4, sticky='nsew')

        # MCU Dropdown
        tk.Label(self, text="Select MCU:").grid(row=4, column=0, pady=5)
        self.mcu_dropdown = ttk.Combobox(self, textvariable=self.selected_mcu, values=self.mcu_options)
        self.mcu_dropdown.grid(row=4, column=1, pady=5, sticky='nsew')

        # Programmer Dropdown
        tk.Label(self, text="Select Programmer:").grid(row=5, column=0, pady=5)
        self.programmer_dropdown = ttk.Combobox(self, textvariable=self.selected_programmer, values=self.programmer_options)
        self.programmer_dropdown.grid(row=5, column=1, pady=5, sticky='nsew')

        # Serial Port Entry
        tk.Label(self, text="Serial Port (Leave empty for auto-detect):").grid(row=6, column=0, pady=5)
        self.serial_port_entry = tk.Entry(self, textvariable=self.serial_port_var)
        self.serial_port_entry.grid(row=6, column=1, pady=5, sticky='nsew')

        # Buttons
        tk.Button(self, text="Select C Files", command=self.select_c_files).grid(row=1, column=0, pady=10, sticky='nsew')
        tk.Button(self, text="Select H Files", command=self.select_h_files).grid(row=1, column=1, pady=10, sticky='nsew')
        tk.Button(self, text="Create", command=self.create).grid(row=8, column=0, pady=10, sticky='nsew')
        tk.Button(self, text="Flash", command=self.flash).grid(row=8, column=1, pady=10, sticky='nsew')
        tk.Button(self, text="Clean", command=self.clean).grid(row=8, column=2, pady=10, sticky='nsew')

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

    def select_c_files(self):
        self.src_files = list(filedialog.askopenfilenames(filetypes=[("C Files", "*.c"), ("All Files", "*.*")]))
        self.update_tables()

    def select_h_files(self):
        self.hdr_files = list(filedialog.askopenfilenames(filetypes=[("H Files", "*.h"), ("All Files", "*.*")]))
        self.update_tables()

    def update_tables(self):
        self.c_files_tree.delete(*self.c_files_tree.get_children())
        for file in self.src_files:
            self.c_files_tree.insert('', 'end', values=(file,))

        self.h_files_tree.delete(*self.h_files_tree.get_children())
        for file in self.hdr_files:
            self.h_files_tree.insert('', 'end', values=(file,))

    def create(self):
        self.create_data_folder()  # Create 'data' folder if it doesn't exist
        build_folder = self.create_build_folder()
        c_files = " ".join(self.src_files)
        h_files = " ".join(self.hdr_files)
        os.system(f"{CC} {c_files} {h_files} -mmcu={self.selected_mcu.get()} {CFLAGS} -o {build_folder}/{TARGET}.bin")
        os.system(f"{OBJCOPY} -j .text -j .data -O ihex {build_folder}/{TARGET}.bin {build_folder}/{TARGET}.hex")
        print(f"{TARGET}.bin and {TARGET}.hex have been created in {build_folder}")
        self.last_build_folder = build_folder  # Save the last build folder

    def create_build_folder(self):
        build_folder = os.path.join(DATA_FOLDER, f"build_{len(os.listdir(DATA_FOLDER)) + 1}")
        os.makedirs(build_folder, exist_ok=True)
        return build_folder

    def create_data_folder(self):
        os.makedirs(DATA_FOLDER, exist_ok=True)

    def flash(self):
        serial_port = self.serial_port_var.get().strip()

        if not serial_port:
            try:
                serial_port = self.find_arduino_port()
            except:
                serial_port = "usb"

        if serial_port:
            if self.last_build_folder:
                try:
                    os.system(f"avrdude -p {self.selected_mcu.get()} -c {self.selected_programmer.get()} -U flash:w:{self.last_build_folder}/{TARGET}.hex:i -F -P usb")
                except Exception as usb_flash_error:
                    try:
                        os.system(f"avrdude -p {self.selected_mcu.get()} -c {self.selected_programmer.get()} -U flash:w:{self.last_build_folder}/{TARGET}.hex:i -F -P {serial_port}")
                    except Exception as serial_flash_error:
                        print(f"Failed to flash with -P usb: {usb_flash_error}")
                        print(f"Failed to flash with specified serial port: {serial_flash_error}")
                        print("Please check your connections and try again.")
                else:
                    print(f"{TARGET}.hex has been flashed to Microcontroller ({self.selected_mcu.get()}) using -P usb")
            else:
                print("No build folder available. Please create a build first.")
        else:
            messagebox.showerror("Error", "Unable to find Arduino serial port. Please specify a valid serial port or check your connections.")

        try:
            os.system(f"avrdude -p {self.selected_mcu.get()} -c {self.selected_programmer.get()} -U flash:w:{self.last_build_folder}/{TARGET}.hex:i -F -P usb")
        except Exception as usb_flash_error:
            messagebox.showerror("Error", "Unable to find Arduino serial port. Please specify a valid serial port or check your connections.")

    def find_arduino_port(self):
        arduino_ports = [p.device for p in serial.tools.list_ports.comports() if "arduino" in p.description.lower()]
        if arduino_ports:
            return arduino_ports[0]
        return None

    def clean(self):
        for folder in os.listdir(DATA_FOLDER):
            folder_path = os.path.join(DATA_FOLDER, folder)
            if os.path.isdir(folder_path):
                shutil.rmtree(folder_path)
        print("All folders in 'data' have been deleted")


if __name__ == "__main__":
    app = AVRFlashGUI()
    app.mainloop()
