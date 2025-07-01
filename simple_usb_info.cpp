// Simple USB Device Information Utility
// Investigates USB device identification capabilities for PSU boards

#include <iostream>
#include <iomanip>
#include <string>
#include <libusb-1.0/libusb.h>

void print_device_strings(libusb_device_handle* handle, const libusb_device_descriptor& desc) {
    if (!handle) return;
    
    char string_buffer[256];
    
    // Try to read manufacturer string
    if (desc.iManufacturer > 0) {
        int ret = libusb_get_string_descriptor_ascii(handle, desc.iManufacturer, 
                                                   (unsigned char*)string_buffer, sizeof(string_buffer));
        if (ret > 0) {
            std::cout << "  Manufacturer: " << string_buffer << std::endl;
        } else {
            std::cout << "  Manufacturer: Failed to read (error " << ret << ")" << std::endl;
        }
    } else {
        std::cout << "  Manufacturer: No string descriptor" << std::endl;
    }
    
    // Try to read product string
    if (desc.iProduct > 0) {
        int ret = libusb_get_string_descriptor_ascii(handle, desc.iProduct, 
                                                   (unsigned char*)string_buffer, sizeof(string_buffer));
        if (ret > 0) {
            std::cout << "  Product: " << string_buffer << std::endl;
        } else {
            std::cout << "  Product: Failed to read (error " << ret << ")" << std::endl;
        }
    } else {
        std::cout << "  Product: No string descriptor" << std::endl;
    }
    
    // Try to read serial number string
    if (desc.iSerialNumber > 0) {
        int ret = libusb_get_string_descriptor_ascii(handle, desc.iSerialNumber, 
                                                   (unsigned char*)string_buffer, sizeof(string_buffer));
        if (ret > 0) {
            std::cout << "  Serial Number: " << string_buffer << std::endl;
        } else {
            std::cout << "  Serial Number: Failed to read (error " << ret << ")" << std::endl;
        }
    } else {
        std::cout << "  Serial Number: No string descriptor" << std::endl;
    }
}

int main() {
    std::cout << "USB Device Information Utility" << std::endl;
    std::cout << "Searching for PSU interface boards (VID:0xA0A0, PID:0x000C)" << std::endl;
    std::cout << "==========================================================" << std::endl;
    
    libusb_context *context = nullptr;
    if (libusb_init(&context) < 0) {
        std::cerr << "Failed to initialize libusb" << std::endl;
        return 1;
    }
    
    libusb_device **device_list;
    ssize_t device_count = libusb_get_device_list(context, &device_list);
    
    if (device_count < 0) {
        std::cerr << "Failed to get device list" << std::endl;
        libusb_exit(context);
        return 1;
    }
    
    int target_device_count = 0;
    
    for (ssize_t i = 0; i < device_count; i++) {
        libusb_device_descriptor desc;
        int ret = libusb_get_device_descriptor(device_list[i], &desc);
        
        if (ret < 0) {
            continue;
        }
        
        // Look for our target devices
        if (desc.idVendor == 0xA0A0 && desc.idProduct == 0x000C) {
            std::cout << "\nFound PSU Interface Board #" << target_device_count << ":" << std::endl;
            std::cout << "  VID:PID: 0x" << std::hex << desc.idVendor << ":0x" << desc.idProduct << std::dec << std::endl;
            std::cout << "  BCD Device: 0x" << std::hex << desc.bcdDevice << std::dec << std::endl;
            std::cout << "  Device Class: " << (int)desc.bDeviceClass << std::endl;
            std::cout << "  Device SubClass: " << (int)desc.bDeviceSubClass << std::endl;
            std::cout << "  Device Protocol: " << (int)desc.bDeviceProtocol << std::endl;
            std::cout << "  String Descriptor Indices:" << std::endl;
            std::cout << "    iManufacturer: " << (int)desc.iManufacturer << std::endl;
            std::cout << "    iProduct: " << (int)desc.iProduct << std::endl;
            std::cout << "    iSerialNumber: " << (int)desc.iSerialNumber << std::endl;
            
            // Try to open the device to read string descriptors
            libusb_device_handle *handle;
            ret = libusb_open(device_list[i], &handle);
            if (ret == 0) {
                std::cout << "  String Descriptors:" << std::endl;
                print_device_strings(handle, desc);
                libusb_close(handle);
            } else {
                std::cout << "  String Descriptors: Unable to open device (error " << ret << ")" << std::endl;
                std::cout << "    (This might require root privileges or udev rules)" << std::endl;
            }
            
            target_device_count++;
        }
    }
    
    std::cout << "\nSummary:" << std::endl;
    std::cout << "Found " << target_device_count << " PSU interface board(s)" << std::endl;
    
    if (target_device_count == 0) {
        std::cout << "No PSU interface boards detected. Check:" << std::endl;
        std::cout << "  - USB connections" << std::endl;
        std::cout << "  - Device power" << std::endl;
        std::cout << "  - USB permissions (may need sudo/udev rules)" << std::endl;
    } else if (target_device_count > 1) {
        std::cout << "\nPotential identification methods found:" << std::endl;
        std::cout << "  1. BCD Device version differences" << std::endl;
        std::cout << "  2. String descriptor differences (manufacturer, product, serial)" << std::endl;
        std::cout << "  3. Enumeration order (current method - platform dependent)" << std::endl;
        std::cout << "\nCurrent system uses enumeration order only!" << std::endl;
    } else {
        std::cout << "Only one device found - identification not needed" << std::endl;
    }
    
    libusb_free_device_list(device_list, 1);
    libusb_exit(context);
    
    return 0;
}