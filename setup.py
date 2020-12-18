import setuptools

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="Raffi-Personality-Adaptive-Chatbot",
    version="0.1.0",
    author="Marcel Goergens",
    author_email="",
    description=(
        "Raffi is used as a chatbot for a personality adaptive " +
        "conversation with multiple users."
    ),
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: Unix",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
)