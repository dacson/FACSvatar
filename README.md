# FACSvatar

Framework to create high-quality avatars based on Manuel Bastioni Blender plugin and control their facial expressions in game engines like Unity3D and Unreal Engine (not yet implemented) with an intermediate dataformat based on the Facial Action Coding System (FACS). FACS data is retrieved through OpenFace.

Running (so far) both on Windows and Linux (Ubuntu).

# Documentation & Setup instructions
Currently considering switching from Crossbar.io to ROS.

Will appear when message broker has been decided:
https://facsvatar.readthedocs.io/en/latest/

- docker run -it -p 8080:8080 crossbario/crossbar

## Software
* Blender + Manuel Bastioni Lab addon  (create human models)
* OpenFace  (extract FACS data)
* Unity 3D 2017.2 (animate in game engine)
* Crossbar.io / ROS (Publisher-Subscriber model)
* Docker  (containerization for easy distribution)



# TODO

- Update Sphinx documentation
- Create a docker image for the Python server
https://runnable.com/docker/python/dockerize-your-python-application
