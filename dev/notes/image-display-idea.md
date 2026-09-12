# Image Display Idea

I would like to display images with pytanga via a three-js plane with an appropriate shader. Here are some features I would like in an unordered list:

- the image is drawn on a plane in 2d view using a shader. 
- by default the image is shown in the correct aspect ratio. We did something similar 
    for 2d plots.
- the image can draw up to the edge of the 2d view, which could be part of a split view.
- we should be able to set margins separately on either side of the image.
- In principle, an image display is also a View derived class, that allows the registration of a shader that draws the actual image. For each shader uniforms can be 
registered with the ImageView class, which can be attached to mouse events (e.g. left mouse button with ctrl) or attached to target names that can be used by python handlers on the ImageView class, to adapt the uniforms of the shader.
- The ImageView class should define a standard shader that offers zoom to mouse position, pan, tilt, brightness, contrast. 
- The ImageView class should allow to hold a number of images, which are all made availabel as textures to the shader. A custom shader can in this way do arbitrary computations with the multiple images. The number of images should be restricted by the typical capabilites of the graphics system or OpenGL.
- There should be a pixel based frame on the image with 0,0 at the top left of the image and x pointing right and y pointing down. In this way, we should be able to draw on the image in pixel coordinates.
- maybe ImageView cannot be a view class for all those features, but we need to have a construction like the coordinate system, so setup the appropriate frame to draw over the image. 
- there should be a mouse handler that returns the pixel position and also records dragging in pixel coordinates, which would work immediately with the correct frame setup. 
- as use case, I can imagine a label tool, that allows users to draw boxes, or polygons on an image. 
- Another use case is just to look at images and have a fast zoom, and contrast/brightness change.
