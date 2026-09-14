# Image Display Idea

I would like to display images with pytanga via a three-js plane with an appropriate shader. Here are some features I would like in an unordered list:

- the image is drawn on a plane in 2d view using a shader. 
- by default the image is shown in the correct aspect ratio. We did something similar 
    for 2d plots.
- the image can draw up to the edge of the 2d view, which could be part of a split view.
- In principle, an image display is also a View derived class, that allows the registration of a shader that draws the actual image. For each shader uniforms can be 
registered with the ImageView class, which can be attached to mouse events (e.g. left mouse button with ctrl) or attached to target names that can be used by python handlers on the ImageView class, to adapt the uniforms of the shader.
- The ImageView class should define a standard shader that offers brightness and contrast, and contrast mid-point.
- The ImageView class should allow to hold a number of images, which are all made availabel as textures to the shader. A custom shader can in this way do arbitrary computations with the multiple images. The number of images should be restricted by the typical capabilites of the graphics system or OpenGL.
- There should be a pixel based frame on the image with 0,0 at the top left of the image and x pointing right and y pointing down. In this way, we should be able to draw on the image in pixel coordinates.
- maybe ImageView cannot be a view class for all those features, but we need to have a construction like the coordinate system, so setup the appropriate frame to draw over the image. 
- there should be a mouse handler that returns the pixel position and also records dragging in pixel coordinates, which would work immediately with the correct frame setup. 
- as use case, I can imagine a label tool, that allows users to draw boxes, or polygons on an image. 
- Another use case is just to look at images and have a fast zoom, and contrast/brightness change.
- when zooming do not interpolate the pixels. I want to see the actual pixels.
- zoom, pan and rotate should happen in the 2d frame, and not in the image shader, so that drawing overlays on the image fits the image itself.
- the default datatype for images consumed by ImageView should be numpy arrays of 1, 3 or 4 channels. The default shader should support just displaying one channel as grayscale (also channel 4), channels 1-3 as rgb, and the magnitude of channels 1-3 combined as grayscale. 
- I would also like to support the PIL image datatype, but I dont want to make tanga-py dependent on PIL by default. Maybe this should be an extra, and there should be a function that converts PIL to numpy array, which ImageView understands natively. But the PIL import should be done lazily and just raise an exception if PIL is not available.

