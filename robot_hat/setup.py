#!/usr/bin/env python3
from setuptools import setup, find_packages

package_name = "robot_hat"

setup(
    name=package_name,
    version="0.0.1",
    packages=find_packages(exclude=["tests", "docs", "examples"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=[
        "setuptools",
        "smbus2",
        "gpiozero",
        "rpi-lgpio",
        "pyaudio",
        "spidev",
        "pyserial",
        "pillow",
        "pygame>=2.1.2",
    ],
    zip_safe=True,
    maintainer="Your Name",
    maintainer_email="your_email@example.com",  # Replace with a valid email
    description="Robot Hat Python library for Raspberry Pi.",
    license="GPLv3",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            # Add any executables if needed
        ],
    },
)