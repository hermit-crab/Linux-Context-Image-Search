# Linux Context Image Search
Context menu reverse image search option for linux desktops.
![test](https://i.imgur.com/0eGceKd.png)

Check out the [fancy loader](https://gfycat.com/EdibleEnergeticDeermouse)!

#### Requirements
* Python3
* PyQt4 for the circular loader bar (without it a simpler loader will be shown)  
  (package `python-qt4` on ubuntu, `python-pyqt4` on archlinux)

Other dependencies will be installed automatically.

#### Installation
```bash
> pip3 install --user https://github.com/Unknowny/Linux-Context-Image-Search/archive/master.zip
# next line will install the icons / desktop entries into appropriate home directories
> python3 -m searchbyimage --install
# you should also be able to call it simply with
> searchbyimage --help
```

#### Note
You might want to avoid using google search option as it may cause google to start showing you captchas.
