from distutils.core import setup

setup(
    name="dds-frontend",
    version="0.1",
    author="Crew",
    author_email="crew@ccs.neu.edu",
    url="http://crew-git.ccs.neu.edu/git/frontend/",
    package_dir={"crew": "src"},
    packages=["crew", "crew.dds", "crew.dds.contrib"],
    keywords="crew digitaldisplay",
    scripts=["scripts/dds.py", "scripts/runner.sh"],
)
