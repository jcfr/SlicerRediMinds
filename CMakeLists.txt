cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(SlicerRediMinds)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/Rediminds/SlicerRediMinds#readme")
set(EXTENSION_CATEGORY "RediMinds")
set(EXTENSION_CONTRIBUTORS "K Mordhwaj (Inzint), Andras Lasso (PerkLab)")
set(EXTENSION_DESCRIPTION "This extension enables the user to load original CT scans and segmented files into Slicer using a URL, and then use the Segment Editor module to label or polish the segments of an organ. The RediMinds module, installed from the marketplace, can be used to send the segmented files to the RediMinds backend for further processing.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/Rediminds/SlicerRediMinds/main/RediMinds.png")
set(EXTENSION_SCREENSHOTURLS
  "https://raw.githubusercontent.com/Rediminds/SlicerRediMinds/main/Screenshots/Screenshot_1.png"
  "https://raw.githubusercontent.com/Rediminds/SlicerRediMinds/main/Screenshots/Screenshot_2.png"
  "https://raw.githubusercontent.com/Rediminds/SlicerRediMinds/main/Screenshots/Screenshot_3.png"
  "https://raw.githubusercontent.com/Rediminds/SlicerRediMinds/main/Screenshots/Screenshot_4.png"
  "https://raw.githubusercontent.com/Rediminds/SlicerRediMinds/main/Screenshots/Screenshot_5.png"
  "https://raw.githubusercontent.com/Rediminds/SlicerRediMinds/main/Screenshots/Screenshot_6.png"
  "https://raw.githubusercontent.com/Rediminds/SlicerRediMinds/main/Screenshots/Screenshot_7.png"
  "https://raw.githubusercontent.com/Rediminds/SlicerRediMinds/main/Screenshots/Screenshot_8.png"
  "https://raw.githubusercontent.com/Rediminds/SlicerRediMinds/main/Screenshots/Screenshot_9.png"
)
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(RediMinds)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
