from setuptools import setup

setup(
    name="kgl",
    version="0.1.2",
    author="James (capjamesg)",
    description="Knowledge Graph Language (KGL) parser.",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    python_requires='>=3.8',
    install_requires=[
        "lark==0.11.3",
        "numpy<2.0",
        "faiss-cpu"
    ],
    keywords=["knowledge graph", "graphs"],
    license="MIT License",
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
)
