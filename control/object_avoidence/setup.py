import glob
from setuptools import find_packages, setup

package_name = "object_avoidence"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            "share/" + package_name + "/launch",
            glob.glob("launch/*.launch.py"),
        ),  # Corrected launch file installation
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="gzub",
    maintainer_email="gzub@todo.todo",
    description="TODO: Package description",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "object_avoidance = object_avoidence.object_avoidence:main"  # ROS 2 node entry point
        ],
    },
)
