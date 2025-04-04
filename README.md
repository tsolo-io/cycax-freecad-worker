# CyCAx FreeCAD worker

cycax-server

## Installation

```
sudo apt install pipx git make wget
mkdir -p ~/Applications
cd ~/Applications
wget https://github.com/FreeCAD/FreeCAD-Bundle/releases/download/1.0.0/FreeCAD_1.0.0-conda-Linux-aarch64-py311.AppImage
chmod a+x ~/Applications
mkdir -p ~/src
cd ~/src
pipx install hatch
git clone https://github.com/tsolo-io/cycax-freecad-worker.git
cd cycax-freecad-worker
make build
```


