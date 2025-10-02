#!/usr/bin/env python3
"""
QR Code Generator for PassPrint Website
Creates a QR code that opens the website on mobile devices
"""

import qrcode
import socket
import os

def get_local_ip():
    """Get the local IP address"""
    try:
        # Create a socket to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "YOUR_IP"

def create_qr_code():
    """Create QR code for the PassPrint website"""
    # Get local IP
    local_ip = get_local_ip()
    port = 5000
    url = f"http://{local_ip}:{port}"

    print("Creating QR Code...")
    print(f"URL: {url}")
    print("QR Code will be saved as: qr_code.png")

    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    # Create an image from the QR Code instance
    img = qr.make_image(fill='black', back_color='white')

    # Save the image
    img.save("qr_code.png")

    print("QR Code created successfully!")
    print("File saved as: qr_code.png")
    print("Scan this code with your phone to access the website")
    return url

def main():
    try:
        url = create_qr_code()
        print("Success!")
        print(f"Website URL: {url}")
        print("Show the QR code to others to access your website")
        input("\nPress Enter to exit...")

    except ImportError:
        print("QR code library not installed")
        print("Install with: pip install qrcode[pil]")
        input("Press Enter to exit...")

    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()