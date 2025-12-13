from setuptools import setup, find_packages

setup(
    name="simplex_lattice_design",
    version="69.6",
    author="Manazael Zuliani Jora",
    description="Ferramenta para planejamento de misturas Simplex-Lattice.",
    long_description="A comprehensive Python tool designed for formulation scientists to generate Simplex-Lattice mixture designs.",
    long_description_content_type="text/markdown",
    url="https://github.com/ManasJora/simplex_lattice_design",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pandas",
        "numpy",
        "plotly",
        "ipywidgets"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
