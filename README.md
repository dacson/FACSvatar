# FACSvatar

Framework to create high-quality avatars based on Manuel Bastioni Blender plugin and control their facial expressions in game engines like Unity3D and Unreal Engine (not yet implemented) with an intermediate dataformat based on the [Facial Action Coding System (FACS)](https://en.wikipedia.org/wiki/Facial_Action_Coding_System "https://en.wikipedia.org/wiki/Facial_Action_Coding_System") by Paul Ekman. FACS data is retrieved through [OpenFace](https://github.com/TadasBaltrusaitis/OpenFace "https://github.com/TadasBaltrusaitis/OpenFace").

Running (so far) both on Windows and Linux (Ubuntu).

A video and poster can be found on the [FACSvatar homepage](https://surafusoft.eu/facsvatar/ "https://surafusoft.eu/facsvatar/")

# Documentation & Setup instructions
Currently considering switching from Crossbar.io to ZeroMQ.
ROS has been considered, but due the lack of Windows support and the unneeded complexity for my project, the extra features don't outweigh the cons. ROS 2 would be better suited, but is deemed to be in a too early stage.

Will appear when the project goes out of pre-alpha phase:
https://facsvatar.readthedocs.io/en/latest/

- docker run -it -p 8080:8080 crossbario/crossbar

## Software
* [Blender](https://www.blender.org/) + [Manuel Bastioni Lab addon](http://www.manuelbastioni.com/)  (create human models)
  * [MBlab wikia](http://manuelbastionilab.wikia.com/wiki/Manuel_Bastioni_Lab_Wiki) 
* [OpenFace](https://github.com/TadasBaltrusaitis/OpenFace)  (extract FACS data)
* [Unity 3D](https://unity3d.com/) 2017.2 (animate in game engine)
* [Crossbar.io](https://crossbar.io/) / [ZeroMQ](http://zeromq.org/) (Publisher-Subscriber model)
* [Docker](https://www.docker.com/)  (containerization for easy distribution)



# TODO

- Update Sphinx documentation
- Create a docker image for the Python modules
https://runnable.com/docker/python/dockerize-your-python-application

# Future
- [ROS](https://github.com/ros2/ros2/wiki) 2 support?
